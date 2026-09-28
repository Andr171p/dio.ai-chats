from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.domain.connections.vo import ModelSelection
from src.domain.conversations import ConversationTitle, MessageContent, MessageRole, TextContent

from .base import CamelModel


class CreateConversation(CamelModel):
    model: ModelSelection
    title: str | None = Field(default=None, min_length=1, max_length=200)


class UpdateConversation(CamelModel):
    """Частичное изменение: не переданные поля остаются прежними."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    model: ModelSelection | None = None


class ConversationResponse(CamelModel):
    id: UUID
    title: ConversationTitle | None
    model: ModelSelection
    current_thread_id: UUID
    created_at: datetime
    updated_at: datetime


class SendMessage(CamelModel):
    content: tuple[TextContent, ...] = Field(min_length=1)
    model: ModelSelection | None = Field(default=None, description="Сменить модель чата перед ответом")


class MessageResponse(CamelModel):
    id: UUID
    conversation_id: UUID
    thread_id: UUID
    role: MessageRole
    content: tuple[MessageContent, ...]
    run_id: UUID | None
    created_at: datetime
