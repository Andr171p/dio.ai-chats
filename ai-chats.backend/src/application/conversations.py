"""Чаты пользователя и их история."""

from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from ddf.application.dsl import Condition, Group
from ddf.application.dtos import CursorPagination, Page, Pagination, Sort
from ddf.application.exceptions import NotFoundError
from ddf.application.repositories import Repository
from ddf.application.utils import iterate_batches
from ddf.domain.utils import apply_changes

from src.domain.connections.models import ModelConnection
from src.domain.conversations import (
    Conversation,
    ConversationSettings,
    ConversationTitle,
    Message,
    Thread,
    TitleSource,
)
from src.domain.conversations.services import start_conversation

from .auth import Identity
from .connections import get_usable_connection
from .dtos.conversations import ConversationResponse, CreateConversation, MessageResponse, UpdateConversation


async def create_conversation(
    command: CreateConversation,
    *,
    identity: Identity,
    conversations: Repository[Conversation],
    threads: Repository[Thread],
    connections: Repository[ModelConnection],
) -> ConversationResponse:
    await get_usable_connection(command.model, identity=identity, connections=connections)

    conversation, root_thread = start_conversation(
        organization_id=identity.organization_id,
        owner_id=identity.id,
        settings=ConversationSettings(model=command.model, mcp_connection_ids=()),
        title=_manual_title(command.title),
    )
    await threads.create(root_thread)
    await conversations.create(conversation)

    return to_conversation_response(conversation)


async def list_conversations(
    pagination: Pagination,
    *,
    identity: Identity,
    conversations: Repository[Conversation],
) -> Page[ConversationResponse]:
    """Чаты пользователя, последние активные - первыми."""

    query = Group(
        op="$and",
        filters=(
            Condition(field="owner_id", op="$eq", value=identity.id),
            Condition(field="deleted_at", op="$isNull"),
        ),
    )
    page = await conversations.find(pagination, query=query, sort=Sort(field="updated_at", direction="desc"))
    return page.map(to_conversation_response)


async def get_conversation(
    conversation_id: UUID,
    *,
    identity: Identity,
    conversations: Repository[Conversation],
) -> ConversationResponse:
    conversation = await get_owned_conversation(
        conversation_id, identity=identity, conversations=conversations
    )
    return to_conversation_response(conversation)


async def update_conversation(
    conversation_id: UUID,
    command: UpdateConversation,
    *,
    identity: Identity,
    conversations: Repository[Conversation],
    connections: Repository[ModelConnection],
) -> ConversationResponse:
    conversation = await get_owned_conversation(
        conversation_id, identity=identity, conversations=conversations
    )

    settings = None
    if command.model is not None:
        await get_usable_connection(command.model, identity=identity, connections=connections)
        settings = replace(conversation.settings, model=command.model)

    apply_changes(conversation, title=_manual_title(command.title), settings=settings)
    await conversations.update(conversation)

    return to_conversation_response(conversation)


async def delete_conversation(
    conversation_id: UUID,
    *,
    identity: Identity,
    conversations: Repository[Conversation],
) -> None:
    conversation = await get_owned_conversation(
        conversation_id, identity=identity, conversations=conversations
    )

    apply_changes(conversation, deleted_at=datetime.now(UTC))
    await conversations.update(conversation)


async def list_messages(
    conversation_id: UUID,
    *,
    identity: Identity,
    conversations: Repository[Conversation],
    threads: Repository[Thread],
    messages: Repository[Message],
) -> list[MessageResponse]:
    """История текущей ветки чата."""

    conversation = await get_owned_conversation(
        conversation_id, identity=identity, conversations=conversations
    )
    history = await load_thread_history(conversation.current_thread_id, threads=threads, messages=messages)

    return [to_message_response(message) for message in history]


async def get_owned_conversation(
    conversation_id: UUID,
    *,
    identity: Identity,
    conversations: Repository[Conversation],
) -> Conversation:
    """Чат текущего пользователя; чужой чат неотличим от несуществующего."""

    conversation = await conversations.read(conversation_id)

    if conversation is None or conversation.is_deleted or conversation.owner_id != identity.id:
        raise NotFoundError(f"Conversation {conversation_id} not found.")

    return conversation


async def load_thread_history(
    thread_id: UUID,
    *,
    threads: Repository[Thread],
    messages: Repository[Message],
) -> list[Message]:
    """Сообщения, видимые в ветке: префикс родительских веток до точки форка и собственные."""

    lineage = await _load_lineage(thread_id, threads)

    batches = iterate_batches(
        messages,
        CursorPagination(size=100),
        query=Condition(field="thread_id", op="$in", value=[thread.id for thread in lineage]),
        sort=Sort(field="id", direction="asc"),
    )
    thread_messages: dict[UUID, list[Message]] = {thread.id: [] for thread in lineage}

    async for batch in batches:
        for message in batch:
            thread_messages[message.thread_id].append(message)

    history: list[Message] = []

    for thread in lineage:
        if thread.parent_thread_id is not None:
            history = _take_through(history, thread.fork_after_message_id)

        history.extend(thread_messages[thread.id])

    return history


def to_conversation_response(conversation: Conversation) -> ConversationResponse:
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        model=conversation.settings.model,
        current_thread_id=conversation.current_thread_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def to_message_response(message: Message) -> MessageResponse:
    return MessageResponse.model_validate(message)


async def _load_lineage(thread_id: UUID, threads: Repository[Thread]) -> list[Thread]:
    """Цепочка веток от корневой до указанной."""

    lineage: list[Thread] = []
    next_id: UUID | None = thread_id

    while next_id is not None:
        if (thread := await threads.read(next_id)) is None:
            raise NotFoundError(f"Thread {next_id} not found.")

        lineage.append(thread)
        next_id = thread.parent_thread_id

    return lineage[::-1]


def _take_through(messages: Sequence[Message], message_id: UUID | None) -> list[Message]:
    """Префикс истории до сообщения включительно; ``None`` - форк от начала диалога."""

    if message_id is None:
        return []

    for index, message in enumerate(messages):
        if message.id == message_id:
            return list(messages[: index + 1])

    raise NotFoundError(f"Fork message {message_id} not found in parent thread.")


def _manual_title(label: str | None) -> ConversationTitle | None:
    return ConversationTitle(label=label, source=TitleSource.MANUAL) if label is not None else None
