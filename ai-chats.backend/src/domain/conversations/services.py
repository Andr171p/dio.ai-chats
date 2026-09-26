from uuid import UUID, uuid7

from .models import Conversation, ConversationSettings, Thread
from .vo import ConversationTitle, ThreadOrigin


def start_conversation(
    *,
    organization_id: UUID,
    owner_id: UUID,
    settings: ConversationSettings,
    title: ConversationTitle | None = None,
) -> tuple[Conversation, Thread]:
    """Начинает новый чат вместе с корневой веткой диалога."""

    conversation_id = uuid7()
    root_thread = Thread(conversation_id=conversation_id, origin=ThreadOrigin.DEFAULT)

    conversation = Conversation(
        id=conversation_id,
        organization_id=organization_id,
        owner_id=owner_id,
        title=title,
        current_thread_id=root_thread.id,
        settings=settings,
    )
    return conversation, root_thread
