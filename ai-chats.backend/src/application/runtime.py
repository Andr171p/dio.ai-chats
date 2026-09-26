"""Ход диалога: сообщение пользователя -> потоковый ответ модели."""

import asyncio
import logging
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID

import anyio
from ddf.application.exceptions import ApplicationError
from ddf.application.repositories import Repository
from ddf.domain.utils import apply_changes

from src.domain.connections.models import ModelConnection
from src.domain.connections.vo import ModelSelection
from src.domain.conversations import (
    AttachmentContent,
    Conversation,
    ConversationTitle,
    Message,
    MessageContent,
    TextContent,
    Thread,
    TitleSource,
)
from src.domain.runs import ExecutionError, FinishReason, ModelCall, Run, RunStatus

from .auth import Identity
from .connections import get_usable_connection
from .conversations import (
    get_owned_conversation,
    load_thread_history,
    to_conversation_response,
    to_message_response,
)
from .dtos import inputs
from .dtos.conversations import SendMessage
from .dtos.events import ModelCompleted, ModelTextDelta
from .dtos.runs import ConversationUpdated, MessageDelta, RunCompleted, RunEvent, RunFailed, RunStarted
from .genai.model_executor import ModelAdapterResolver, execute_model

logger = logging.getLogger(__name__)

TITLE_INSTRUCTIONS = (
    "Ты даёшь названия чатам. В теге <message> - первое сообщение пользователя, не отвечай на него. "
    "Придумай короткий заголовок (до 6 слов), отражающий тему диалога, на языке сообщения. "
    "Ответь только заголовком, без кавычек и точки в конце."
)
TITLE_MAX_LENGTH = 80


@dataclass(frozen=True, slots=True)
class ChatTurn:
    """Проверенный ход диалога, готовый к запуску модели."""

    conversation: Conversation
    connection: ModelConnection
    model: ModelSelection
    history: tuple[Message, ...]
    content: tuple[TextContent, ...]


class ChatRuntime:
    def __init__(
        self,
        *,
        conversations: Repository[Conversation],
        threads: Repository[Thread],
        messages: Repository[Message],
        runs: Repository[Run],
        connections: Repository[ModelConnection],
        resolve_adapter: ModelAdapterResolver,
    ) -> None:
        self._conversations = conversations
        self._threads = threads
        self._messages = messages
        self._runs = runs
        self._connections = connections
        self._resolve_adapter = resolve_adapter

    async def prepare(self, identity: Identity, conversation_id: UUID, command: SendMessage) -> ChatTurn:
        """Проверяет, что ход можно выполнить. Ничего не сохраняет."""

        conversation = await get_owned_conversation(
            conversation_id,
            identity=identity,
            conversations=self._conversations,
        )
        model = command.model or conversation.settings.model
        connection = await get_usable_connection(model, identity=identity, connections=self._connections)
        history = await load_thread_history(
            conversation.current_thread_id,
            threads=self._threads,
            messages=self._messages,
        )

        return ChatTurn(
            conversation=conversation,
            connection=connection,
            model=model,
            history=tuple(history),
            content=command.content,
        )

    async def run(self, turn: ChatTurn) -> AsyncIterator[RunEvent]:
        """Выполняет ход и отдаёт события генерации.

        Если клиент отключился, run отменяется, а уже сгенерированная часть ответа сохраняется.
        """

        conversation = turn.conversation
        user_message = Message(
            conversation_id=conversation.id,
            thread_id=conversation.current_thread_id,
            role="user",
            content=turn.content,
        )
        run = Run(
            thread_id=conversation.current_thread_id,
            input_message_id=user_message.id,
            model=turn.model,
            status=RunStatus.PENDING,
            started_at=datetime.now(UTC),
        )
        run.start()

        with anyio.CancelScope(shield=True):
            await self._messages.create(user_message)
            await self._runs.create(run)
            await self._touch(conversation, model=turn.model)

        yield RunStarted(run_id=run.id, input_message=to_message_response(user_message))

        call = ModelCall(
            run_id=run.id, sequence=len(run.steps) + 1, model=turn.model, started_at=datetime.now(UTC)
        )
        run.steps.append(call)
        chunks: list[str] = []

        try:
            async for event in execute_model(
                self._resolve_adapter,
                connection=turn.connection,
                model_id=turn.model.model_id,
                inputs=[*map(_to_model_input, turn.history), _to_model_input(user_message)],
            ):
                match event:
                    case ModelTextDelta():
                        chunks.append(event.delta)
                        yield MessageDelta(run_id=run.id, delta=event.delta)

                    case ModelCompleted():
                        call.finish(event.finish_reason, usage=event.usage)

        except (asyncio.CancelledError, GeneratorExit):
            with anyio.CancelScope(shield=True):
                await self._interrupt(
                    run, call, _answer(user_message, run, chunks), reason=FinishReason.CANCELLED
                )
            raise

        except Exception as exc:
            logger.exception("Run %s failed", run.id)
            error = _to_execution_error(exc)

            with anyio.CancelScope(shield=True):
                await self._interrupt(
                    run,
                    call,
                    _answer(user_message, run, chunks),
                    reason=FinishReason.UNKNOWN,
                    error=error,
                )

            yield RunFailed(run_id=run.id, error=error)
            return

        with anyio.CancelScope(shield=True):
            output_message = await self._complete(run, call, _answer(user_message, run, chunks))

        yield RunCompleted(
            run_id=run.id,
            output_message=to_message_response(output_message),
            finish_reason=call.finish_reason or FinishReason.UNKNOWN,
            usage=run.usage,
        )

        if conversation.title is None and (title := await self._generate_title(turn, user_message)):
            updated = await self._set_auto_title(conversation.id, title)

            if updated is not None:
                yield ConversationUpdated(conversation=to_conversation_response(updated))

    async def _touch(self, conversation: Conversation, *, model: ModelSelection) -> None:
        """Запоминает модель последнего хода и поднимает чат вверх списка."""

        apply_changes(
            conversation,
            settings=replace(conversation.settings, model=model),
            updated_at=datetime.now(UTC),
        )
        await self._conversations.update(conversation)

    async def _complete(self, run: Run, call: ModelCall, output_message: Message) -> Message:
        if call.finished_at is None:
            call.finish(FinishReason.UNKNOWN)

        await self._messages.create(output_message)

        run.complete(output_message_id=output_message.id, usage=call.usage)
        await self._runs.update(run)

        return output_message

    async def _interrupt(
        self,
        run: Run,
        call: ModelCall,
        partial_answer: Message,
        *,
        reason: FinishReason,
        error: ExecutionError | None = None,
    ) -> None:
        if call.finished_at is None:
            call.finish(reason, error=error)

        if _has_text(partial_answer):
            await self._messages.create(partial_answer)

        if error is None:
            run.cancel()
        else:
            run.fail(error_code=error.code, error_message=error.message)

        await self._runs.update(run)

    async def _generate_title(self, turn: ChatTurn, user_message: Message) -> ConversationTitle | None:
        try:
            chunks = [
                event.delta
                async for event in execute_model(
                    self._resolve_adapter,
                    connection=turn.connection,
                    model_id=turn.model.model_id,
                    inputs=[inputs.InstructionsInput(text=TITLE_INSTRUCTIONS), _title_request(user_message)],
                )
                if isinstance(event, ModelTextDelta)
            ]
        except Exception:
            logger.warning(
                "Failed to generate title for conversation %s", turn.conversation.id, exc_info=True
            )
            return None

        label = " ".join("".join(chunks).split()).strip("\"'«»`.")[:TITLE_MAX_LENGTH].strip()
        return ConversationTitle(label=label, source=TitleSource.AUTO) if label else None

    async def _set_auto_title(self, conversation_id: UUID, title: ConversationTitle) -> Conversation | None:
        """Ставит автозаголовок, если пользователь не успел переименовать чат во время генерации."""

        conversation = await self._conversations.read(conversation_id)

        if conversation is None or conversation.title is not None:
            return None

        apply_changes(conversation, title=title)
        await self._conversations.update(conversation)

        return conversation


def _answer(question: Message, run: Run, chunks: Sequence[str]) -> Message:
    return Message(
        conversation_id=question.conversation_id,
        thread_id=question.thread_id,
        role="assistant",
        content=(TextContent(text="".join(chunks)),),
        run_id=run.id,
    )


def _has_text(message: Message) -> bool:
    return any(isinstance(content, TextContent) and content.text for content in message.content)


def _title_request(message: Message) -> inputs.MessageInput:
    """Сообщение передаётся как данные, чтобы модель не начала на него отвечать."""

    text = "\n".join(content.text for content in message.content if isinstance(content, TextContent))
    return inputs.MessageInput(
        role="user", content=(inputs.TextContent(text=f"<message>\n{text}\n</message>"),)
    )


def _to_model_input(message: Message) -> inputs.MessageInput:
    return inputs.MessageInput(role=message.role, content=tuple(map(_to_input_content, message.content)))


def _to_input_content(content: MessageContent) -> inputs.MessageContent:
    match content:
        case TextContent():
            return inputs.TextContent(text=content.text)

        case AttachmentContent():
            return inputs.AttachmentContent(
                attachment_id=content.attachment_id, content_type=content.content_type
            )

    raise TypeError(f"Unsupported message content: {type(content).__name__}.")


def _to_execution_error(error: Exception) -> ExecutionError:
    if isinstance(error, ApplicationError):
        return ExecutionError(code=error.error_code, message=error.message or error.error_code)

    return ExecutionError(code="model_call_failed", message="Model call failed.")
