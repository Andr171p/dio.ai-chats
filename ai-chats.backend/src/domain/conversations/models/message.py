from typing import Annotated, Literal

from dataclasses import dataclass
from uuid import UUID

from ddf.domain.models import Entity
from typing_extensions import Doc

from src.domain.conversations.types import MessageRole
from src.domain.runs.vo import McpToolCallStatus


@dataclass(frozen=True, slots=True)
class TextContent:
    """Текстовый блок сообщения."""

    text: str
    type: Literal["text"] = "text"


@dataclass(frozen=True, slots=True)
class AttachmentContent:
    """Ссылка на приложенный файл."""

    attachment_id: UUID
    content_type: str
    type: Literal["content"] = "content"


@dataclass(frozen=True, slots=True)
class ToolCallContent:
    """Вызов инструмента в ответе ассистента. Аргументы и результат хранятся в шаге ``Run``."""

    call_id: Annotated[UUID, Doc("Идентификатор ``McpToolCall``")]
    connection_id: UUID
    name: str
    title: Annotated[str | None, Doc("Человекочитаемое название инструмента")]
    status: McpToolCallStatus
    type: Literal["tool_call"] = "tool_call"


type MessageContent = TextContent | AttachmentContent | ToolCallContent


@dataclass(kw_only=True)
class Message(Entity):
    """Отображаемое сообщение внутри чата."""

    conversation_id: UUID
    thread_id: UUID
    role: MessageRole
    content: tuple[MessageContent, ...]
    run_id: UUID | None = None
