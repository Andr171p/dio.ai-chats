from typing import ClassVar

from collections.abc import Sequence
from uuid import UUID

from ddf.infra.database.mongo import MongoBaseModel, MongoEntityMixin
from pymongo import ASCENDING, DESCENDING, IndexModel

from src.domain.conversations import (
    ConversationSettings,
    ConversationTitle,
    MessageContent,
    MessageRole,
    ThreadOrigin,
)


class ConversationModel(MongoBaseModel, MongoEntityMixin):
    __collection_name__: ClassVar[str] = "conversations"
    __indexes__: ClassVar[Sequence[IndexModel]] = [
        IndexModel(
            [
                ("ownerId", ASCENDING),
                ("deletedAt", ASCENDING),
                ("updatedAt", DESCENDING),
                ("_id", DESCENDING),
            ]
        ),
    ]

    organization_id: UUID
    owner_id: UUID
    title: ConversationTitle | None
    current_thread_id: UUID
    settings: ConversationSettings


class ThreadModel(MongoBaseModel, MongoEntityMixin):
    __collection_name__: ClassVar[str] = "threads"
    __indexes__: ClassVar[Sequence[IndexModel]] = [IndexModel([("conversationId", ASCENDING)])]

    conversation_id: UUID
    origin: ThreadOrigin
    parent_thread_id: UUID | None
    fork_after_message_id: UUID | None
    origin_message_id: UUID | None


class MessageModel(MongoBaseModel, MongoEntityMixin):
    __collection_name__: ClassVar[str] = "messages"
    __indexes__: ClassVar[Sequence[IndexModel]] = [IndexModel([("threadId", ASCENDING), ("_id", ASCENDING)])]

    conversation_id: UUID
    thread_id: UUID
    role: MessageRole
    content: tuple[MessageContent, ...]
    run_id: UUID | None
