from dataclasses import dataclass

from ddf.domain.models import AggregateRoot

from src.domain.connections.vo import ConnectionOwner, ModelProtocol, ModelRoute, ModelSpec


@dataclass(kw_only=True)
class ModelConnection(AggregateRoot):
    """Источник моделей, доступный пользователю."""

    owner: ConnectionOwner

    name: str
    protocol: ModelProtocol
    route: ModelRoute

    models: tuple[ModelSpec, ...]
    enabled: bool = True

    def has_model(self, model_id: str) -> bool:
        return any(model.id == model_id for model in self.models)
