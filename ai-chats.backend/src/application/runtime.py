"""Ход диалога: сообщение пользователя -> потоковый ответ модели с вызовами инструментов MCP."""

from typing import Annotated

import asyncio
import logging
from collections.abc import AsyncIterator, Sequence
from contextlib import aclosing
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID

import anyio
from ddf.application.exceptions import ApplicationError
from ddf.application.repositories import Repository
from ddf.domain.utils import apply_changes
from pydantic import SecretStr
from typing_extensions import Doc

from src.domain.connections.models import McpConnection, ModelConnection
from src.domain.connections.vo import ModelCapability, ModelSelection, Usage
from src.domain.conversations import (
    AttachmentContent,
    Conversation,
    ConversationTitle,
    Message,
    MessageContent,
    TextContent,
    Thread,
    TitleSource,
    ToolCallContent,
)
from src.domain.runs import (
    ExecutionError,
    FinishReason,
    McpToolCall,
    McpToolCallStatus,
    ModelCall,
    Run,
    RunStatus,
)

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
from .dtos.events import ModelCompleted, ModelTextDelta, ModelToolCall
from .dtos.runs import (
    ConversationUpdated,
    MessageDelta,
    RunCompleted,
    RunEvent,
    RunFailed,
    RunStarted,
    ToolCallCompleted,
    ToolCallStarted,
)
from .dtos.tools import McpToolResult, ModelTool
from .genai.model_executor import ModelAdapterResolver, execute_model
from .mcp.client import McpClient
from .mcp.toolset import Toolset
from .mcp_connections import get_usable_mcp_connections

logger = logging.getLogger(__name__)

TITLE_INSTRUCTIONS = (
    "Ты даёшь названия чатам. В теге <message> - первое сообщение пользователя, не отвечай на него. "
    "Придумай короткий заголовок (до 6 слов), отражающий тему диалога, на языке сообщения. "
    "Ответь только заголовком, без кавычек и точки в конце."
)
TITLE_MAX_LENGTH = 80

MAX_MODEL_CALLS = 8
"""Предел вызовов модели за ход. Последний идёт без инструментов, чтобы модель ответила текстом."""


@dataclass(frozen=True, slots=True)
class ChatTurn:
    """Проверенный ход диалога, готовый к запуску модели."""

    conversation: Conversation
    connection: ModelConnection
    model: ModelSelection
    history: tuple[Message, ...]
    content: tuple[TextContent, ...]
    mcp_connections: Annotated[tuple[McpConnection, ...], Doc("Источники инструментов для модели")]
    access_token: Annotated[SecretStr, Doc("Токен пользователя для MCP серверов экосистемы DIOS")]


@dataclass(slots=True)
class _ToolPart:
    call: McpToolCall
    title: str | None

    def content(self) -> ToolCallContent:
        return ToolCallContent(
            call_id=self.call.id,
            connection_id=self.call.connection_id,
            name=self.call.name,
            title=self.title,
            status=self.call.status,
        )


class _AnswerDraft:
    """Ответ ассистента: текст и вызовы инструментов в порядке появления."""

    def __init__(self) -> None:
        self._parts: list[list[str] | _ToolPart] = []

    def add_text(self, delta: str) -> None:
        last = self._parts[-1] if self._parts else None

        if not isinstance(last, list):
            last = []
            self._parts.append(last)

        last.append(delta)

    def add_tool_call(self, call: McpToolCall, *, title: str | None) -> _ToolPart:
        part = _ToolPart(call=call, title=title)
        self._parts.append(part)
        return part

    def content(self) -> tuple[MessageContent, ...]:
        return tuple(
            TextContent(text="".join(part)) if isinstance(part, list) else part.content()
            for part in self._parts
        )


class ChatRuntime:
    def __init__(
        self,
        *,
        conversations: Repository[Conversation],
        threads: Repository[Thread],
        messages: Repository[Message],
        runs: Repository[Run],
        connections: Repository[ModelConnection],
        mcp_connections: Repository[McpConnection],
        resolve_adapter: ModelAdapterResolver,
        mcp_client: McpClient,
    ) -> None:
        self._conversations = conversations
        self._threads = threads
        self._messages = messages
        self._runs = runs
        self._connections = connections
        self._mcp_connections = mcp_connections
        self._resolve_adapter = resolve_adapter
        self._mcp_client = mcp_client

    async def prepare(
        self,
        identity: Identity,
        conversation_id: UUID,
        command: SendMessage,
        *,
        access_token: SecretStr,
    ) -> ChatTurn:
        """Проверяет, что ход можно выполнить. Ничего не сохраняет.

        Отключённые администратором MCP серверы просто не попадают в ход, чтобы не ломать чат.
        """

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
        mcp_connections = (
            await get_usable_mcp_connections(
                conversation.settings.mcp_connection_ids,
                identity=identity,
                mcp_connections=self._mcp_connections,
            )
            if _supports_tools(connection, model.model_id)
            else []
        )

        return ChatTurn(
            conversation=conversation,
            connection=connection,
            model=model,
            history=tuple(history),
            content=command.content,
            mcp_connections=tuple(mcp_connections),
            access_token=access_token,
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

        answer = _AnswerDraft()

        try:
            async with aclosing(self._respond(turn, run, user_message, answer)) as events:
                async for event in events:
                    yield event

        except (asyncio.CancelledError, GeneratorExit):
            with anyio.CancelScope(shield=True):
                await self._interrupt(run, _answer(user_message, run, answer), reason=FinishReason.CANCELLED)
            raise

        except Exception as exc:
            logger.exception("Run %s failed", run.id)
            error = _to_execution_error(exc)

            with anyio.CancelScope(shield=True):
                await self._interrupt(
                    run, _answer(user_message, run, answer), reason=FinishReason.UNKNOWN, error=error
                )

            yield RunFailed(run_id=run.id, error=error)
            return

        with anyio.CancelScope(shield=True):
            output_message = await self._complete(run, _answer(user_message, run, answer))

        yield RunCompleted(
            run_id=run.id,
            output_message=to_message_response(output_message),
            finish_reason=_model_calls(run)[-1].finish_reason or FinishReason.UNKNOWN,
            usage=run.usage,
        )

        if conversation.title is None and (title := await self._generate_title(turn, user_message)):
            updated = await self._set_auto_title(conversation.id, title)

            if updated is not None:
                yield ConversationUpdated(conversation=to_conversation_response(updated))

    async def _respond(
        self,
        turn: ChatTurn,
        run: Run,
        question: Message,
        answer: _AnswerDraft,
    ) -> AsyncIterator[RunEvent]:
        """Вызывает модель, пока она запрашивает инструменты."""

        toolset = await Toolset.load(self._mcp_client, turn.mcp_connections, access_token=turn.access_token)
        context = _build_context(turn, question, toolset)

        for sequence in range(1, MAX_MODEL_CALLS + 1):
            call = ModelCall(run_id=run.id, sequence=sequence, model=turn.model, started_at=datetime.now(UTC))
            run.steps.append(call)
            requests: list[ModelToolCall] = []
            tools = toolset.tools if sequence < MAX_MODEL_CALLS else None

            async for event in self._call_model(turn, call, context, tools, answer, requests):
                yield event

            if not requests:
                return

            for request in requests:
                async for event in self._use_tool(request, toolset, run, call, answer, context):
                    yield event

    async def _call_model(
        self,
        turn: ChatTurn,
        call: ModelCall,
        context: list[inputs.ModelInput],
        tools: Sequence[ModelTool] | None,
        answer: _AnswerDraft,
        requests: list[ModelToolCall],
    ) -> AsyncIterator[RunEvent]:
        """Один вызов модели: текст уходит в ответ, запросы инструментов - в ``requests``."""

        text: list[str] = []

        async for event in execute_model(
            self._resolve_adapter,
            connection=turn.connection,
            model_id=turn.model.model_id,
            inputs=context,
            tools=tools,
        ):
            match event:
                case ModelTextDelta():
                    text.append(event.delta)
                    answer.add_text(event.delta)
                    yield MessageDelta(run_id=call.run_id, delta=event.delta)

                case ModelToolCall():
                    requests.append(event)

                case ModelCompleted():
                    call.finish(event.finish_reason, usage=event.usage)

        if call.finished_at is None:
            call.finish(FinishReason.UNKNOWN)

        # Пояснение модели перед вызовом инструментов - часть её хода
        if requests and text:
            context.append(_assistant_input("".join(text)))

    async def _use_tool(
        self,
        request: ModelToolCall,
        toolset: Toolset,
        run: Run,
        call: ModelCall,
        answer: _AnswerDraft,
        context: list[inputs.ModelInput],
    ) -> AsyncIterator[RunEvent]:
        """Выполняет запрошенный моделью инструмент и добавляет результат в контекст."""

        context.append(
            inputs.ToolCallInput(call_id=request.call_id, name=request.name, arguments=request.arguments)
        )

        if (tool := toolset.get(request.name)) is None:
            context.append(_tool_result(request, McpToolResult.error(f"Tool {request.name!r} not found.")))
            return

        step = McpToolCall(
            run_id=run.id,
            model_call_id=call.id,
            connection_id=tool.connection.id,
            status=McpToolCallStatus.RUNNING,
            name=tool.tool.name,
            arguments=request.arguments,
        )
        run.steps.append(step)
        part = answer.add_tool_call(step, title=tool.tool.title)
        yield ToolCallStarted(run_id=run.id, tool_call=part.content())

        result = await toolset.call(tool, request.arguments)

        if result.is_error:
            step.fail(ExecutionError(code="tool_error", message=result.text), result=result.value)
        else:
            step.complete(result.value)

        context.append(_tool_result(request, result))
        yield ToolCallCompleted(run_id=run.id, tool_call=part.content())

    async def _touch(self, conversation: Conversation, *, model: ModelSelection) -> None:
        """Запоминает модель последнего хода и поднимает чат вверх списка."""

        apply_changes(
            conversation,
            settings=replace(conversation.settings, model=model),
            updated_at=datetime.now(UTC),
        )
        await self._conversations.update(conversation)

    async def _complete(self, run: Run, output_message: Message) -> Message:
        await self._messages.create(output_message)

        usage = sum((call.usage for call in _model_calls(run)), Usage())
        run.complete(output_message_id=output_message.id, usage=usage)
        await self._runs.update(run)

        return output_message

    async def _interrupt(
        self,
        run: Run,
        partial_answer: Message,
        *,
        reason: FinishReason,
        error: ExecutionError | None = None,
    ) -> None:
        for step in run.steps:
            match step:
                case ModelCall(finished_at=None):
                    step.finish(reason, error=error)

                case McpToolCall(is_finished=False):
                    step.cancel()

        if partial_answer.content:
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


def _answer(question: Message, run: Run, draft: _AnswerDraft) -> Message:
    return Message(
        conversation_id=question.conversation_id,
        thread_id=question.thread_id,
        role="assistant",
        content=draft.content(),
        run_id=run.id,
    )


def _model_calls(run: Run) -> list[ModelCall]:
    return [step for step in run.steps if isinstance(step, ModelCall)]


def _supports_tools(connection: ModelConnection, model_id: str) -> bool:
    return any(
        spec.id == model_id and ModelCapability.TOOLS in spec.capabilities for spec in connection.models
    )


def _build_context(turn: ChatTurn, question: Message, toolset: Toolset) -> list[inputs.ModelInput]:
    """Инструкции MCP серверов и история ветки вместе с новым вопросом."""

    instructions = [inputs.InstructionsInput(text=text)] if (text := toolset.instructions) else []
    messages = (_to_model_input(message) for message in (*turn.history, question))

    return [*instructions, *(message for message in messages if message.content)]


def _assistant_input(text: str) -> inputs.MessageInput:
    return inputs.MessageInput(role="assistant", content=(inputs.TextContent(text=text),))


def _tool_result(request: ModelToolCall, result: McpToolResult) -> inputs.ToolResultInput:
    return inputs.ToolResultInput(call_id=request.call_id, content=result.content, is_error=result.is_error)


def _title_request(message: Message) -> inputs.MessageInput:
    """Сообщение передаётся как данные, чтобы модель не начала на него отвечать."""

    text = "\n".join(content.text for content in message.content if isinstance(content, TextContent))
    return inputs.MessageInput(
        role="user", content=(inputs.TextContent(text=f"<message>\n{text}\n</message>"),)
    )


def _to_model_input(message: Message) -> inputs.MessageInput:
    """Вызовы инструментов прошлых ходов модели не передаются: их итог уже есть в тексте ответа."""

    content = tuple(
        _to_input_content(part) for part in message.content if not isinstance(part, ToolCallContent)
    )
    return inputs.MessageInput(role=message.role, content=content)


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
