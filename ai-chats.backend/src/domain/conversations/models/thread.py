from typing import Annotated

from dataclasses import dataclass
from uuid import UUID

from ddf.domain.models import Entity
from typing_extensions import Doc

from src.domain.conversations.vo import ThreadOrigin


@dataclass(kw_only=True)
class Thread(Entity):
    """Одна версий истории диалога внутри чата."""

    conversation_id: UUID

    origin: ThreadOrigin

    parent_thread_id: UUID | None = None
    fork_after_message_id: Annotated[
        UUID | None,
        Doc(
            "Последнее сообщение parent thread, которое входит "
            "в историю нового thread. Для root thread равно None."
        ),
    ] = None
    origin_message_id: Annotated[
        UUID | None,
        Doc(
            "Сообщение, действие над которым породило thread: "
            "например редактируемое сообщение или regenerated assistant message."
        ),
    ] = None
