from typing import ClassVar

from collections.abc import Sequence

from ddf.infra.database.mongo import MongoBaseModel, MongoEntityMixin
from pymongo import ASCENDING, IndexModel

from src.domain.connections.vo import ConnectionOwner, ModelProtocol, ModelRoute, ModelSpec


class ModelConnectionModel(MongoBaseModel, MongoEntityMixin):
    __collection_name__: ClassVar[str] = "model_connections"
    __indexes__: ClassVar[Sequence[IndexModel]] = [
        IndexModel([("owner.scope", ASCENDING), ("owner.organizationId", ASCENDING)]),
    ]

    owner: ConnectionOwner
    name: str
    protocol: ModelProtocol
    route: ModelRoute
    models: tuple[ModelSpec, ...]
    enabled: bool
