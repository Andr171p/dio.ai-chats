from typing import Literal

from dataclasses import dataclass
from uuid import UUID

from ddf.domain.models import Entity

from src.domain.conversations.types import MessageRole


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


type MessageContent = TextContent | AttachmentContent


@dataclass(kw_only=True)
class Message(Entity):
    """Отображаемое сообщение внутри чата."""

    conversation_id: UUID
    thread_id: UUID
    role: MessageRole
    content: tuple[MessageContent, ...]
    run_id: UUID | None = None
