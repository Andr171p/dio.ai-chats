from typing import Annotated

from dataclasses import dataclass
from uuid import UUID

from ddf.domain.models import AggregateRoot
from typing_extensions import Doc

from src.domain.connections.vo import ModelSelection
from src.domain.conversations.vo import ConversationTitle


@dataclass(frozen=True)
class ConversationSettings:
    """Настройки и политики чата."""

    model: ModelSelection
    mcp_connection_ids: tuple[UUID, ...]


@dataclass(kw_only=True)
class Conversation(AggregateRoot):
    """Чат пользователя с AI ассистентом.
    Имеет независимые ветки для ведения диалога.
    """

    organization_id: UUID
    owner_id: UUID
    title: ConversationTitle | None = None

    current_thread_id: Annotated[UUID, Doc("Текущая ветка, в которой идёт беседа")]
    settings: ConversationSettings
