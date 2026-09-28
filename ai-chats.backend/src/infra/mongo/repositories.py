from typing import ClassVar

from collections.abc import Mapping

from ddf.infra.database.mongo import MongoRepository

from src.domain.connections.models import ModelConnection
from src.domain.conversations import Conversation, Message, Thread
from src.domain.runs import Run

from .mappers import DataclassMapper, RunMapper
from .models import ConversationModel, MessageModel, ModelConnectionModel, RunModel, ThreadModel


class MongoModelConnectionRepository(MongoRepository[ModelConnection, ModelConnectionModel]):
    model = ModelConnectionModel
    data_mapper = DataclassMapper(ModelConnection, ModelConnectionModel)
    filter_whitelist: ClassVar[Mapping[str, str]] = {
        "id": "_id",
        "enabled": "enabled",
        "owner.scope": "owner.scope",
        "owner.organization_id": "owner.organizationId",
        "owner.user_id": "owner.userId",
    }


class MongoConversationRepository(MongoRepository[Conversation, ConversationModel]):
    model = ConversationModel
    data_mapper = DataclassMapper(Conversation, ConversationModel)
    filter_whitelist: ClassVar[Mapping[str, str]] = {
        "owner_id": "ownerId",
        "deleted_at": "deletedAt",
        "updated_at": "updatedAt",
    }


class MongoThreadRepository(MongoRepository[Thread, ThreadModel]):
    model = ThreadModel
    data_mapper = DataclassMapper(Thread, ThreadModel)
    filter_whitelist: ClassVar[Mapping[str, str]] = {}


class MongoMessageRepository(MongoRepository[Message, MessageModel]):
    model = MessageModel
    data_mapper = DataclassMapper(Message, MessageModel)
    filter_whitelist: ClassVar[Mapping[str, str]] = {
        "id": "_id",
        "thread_id": "threadId",
    }


class MongoRunRepository(MongoRepository[Run, RunModel]):
    model = RunModel
    data_mapper = RunMapper()
    filter_whitelist: ClassVar[Mapping[str, str]] = {}
