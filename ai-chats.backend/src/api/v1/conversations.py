from typing import Annotated

from collections.abc import AsyncIterable
from uuid import UUID

from ddf.application.dtos import Page, PaginationQuery
from fastapi import APIRouter, Depends, status
from fastapi.sse import EventSourceResponse, ServerSentEvent

from src.api.dependencies import ContainerDep, CurrentIdentity
from src.application import conversations
from src.application.dtos.conversations import (
    ConversationResponse,
    CreateConversation,
    MessageResponse,
    SendMessage,
    UpdateConversation,
)
from src.application.runtime import ChatTurn

router = APIRouter(prefix="/conversations", tags=["Чаты"])


@router.post(path="", status_code=status.HTTP_201_CREATED, summary="Создать чат")
async def create_conversation(
    command: CreateConversation,
    identity: CurrentIdentity,
    container: ContainerDep,
) -> ConversationResponse:
    return await conversations.create_conversation(
        command,
        identity=identity,
        conversations=container.conversations,
        threads=container.threads,
        connections=container.connections,
    )


@router.get(path="", summary="Чаты пользователя", description="Последние активные чаты - первыми.")
async def list_conversations(
    pagination: PaginationQuery,
    identity: CurrentIdentity,
    container: ContainerDep,
) -> Page[ConversationResponse]:
    return await conversations.list_conversations(
        pagination,
        identity=identity,
        conversations=container.conversations,
    )


@router.get(path="/{conversation_id}", summary="Чат")
async def get_conversation(
    conversation_id: UUID,
    identity: CurrentIdentity,
    container: ContainerDep,
) -> ConversationResponse:
    return await conversations.get_conversation(
        conversation_id,
        identity=identity,
        conversations=container.conversations,
    )


@router.patch(path="/{conversation_id}", summary="Переименовать чат или сменить модель")
async def update_conversation(
    conversation_id: UUID,
    command: UpdateConversation,
    identity: CurrentIdentity,
    container: ContainerDep,
) -> ConversationResponse:
    return await conversations.update_conversation(
        conversation_id,
        command,
        identity=identity,
        conversations=container.conversations,
        connections=container.connections,
    )


@router.delete(path="/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить чат")
async def delete_conversation(
    conversation_id: UUID, identity: CurrentIdentity, container: ContainerDep
) -> None:
    await conversations.delete_conversation(
        conversation_id, identity=identity, conversations=container.conversations
    )


@router.get(path="/{conversation_id}/messages", summary="История текущей ветки чата")
async def list_messages(
    conversation_id: UUID,
    identity: CurrentIdentity,
    container: ContainerDep,
) -> list[MessageResponse]:
    return await conversations.list_messages(
        conversation_id,
        identity=identity,
        conversations=container.conversations,
        threads=container.threads,
        messages=container.messages,
    )


async def prepare_turn(
    conversation_id: UUID,
    command: SendMessage,
    identity: CurrentIdentity,
    container: ContainerDep,
) -> ChatTurn:
    """Проверка до начала стрима, чтобы ошибки вернулись обычным HTTP ответом."""

    return await container.chat_runtime.prepare(identity, conversation_id, command)


@router.post(
    path="/{conversation_id}/messages",
    response_class=EventSourceResponse,
    summary="Отправить сообщение",
    description=(
        "Ответ модели приходит потоком Server-Sent Events. Тип события в поле `event` и `data.type`: "
        "`run.started`, `message.delta`, `run.completed`, `run.failed`, `conversation.updated`. "
        "Разрыв соединения останавливает генерацию, уже полученная часть ответа сохраняется."
    ),
)
async def send_message(
    turn: Annotated[ChatTurn, Depends(prepare_turn)],
    container: ContainerDep,
) -> AsyncIterable[ServerSentEvent]:
    async for event in container.chat_runtime.run(turn):
        yield ServerSentEvent(event=event.type, data=event)
