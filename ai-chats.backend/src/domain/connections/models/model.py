from dataclasses import dataclass
from enum import StrEnum

from ddf.domain.models import AggregateRoot

from src.domain.connections.vo import ConnectionOwner, ModelRoute, ModelSpec


class ModelProtocol(StrEnum):
    OPENAI_RESPONSES = "openai_responses"
    OPENAI_CHAT_COMPLETIONS = "openai_chat_completions"


@dataclass(kw_only=True)
class ModelConnection(AggregateRoot):
    """Источник моделей, доступный пользователю."""

    owner: ConnectionOwner

    name: str
    protocol: ModelProtocol
    route: ModelRoute

    models: tuple[ModelSpec, ...]
    enabled: bool = True

    def supports(self, model_id: str) -> bool:
        return any(model.id == model_id for model in self.models)
