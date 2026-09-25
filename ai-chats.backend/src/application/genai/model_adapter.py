from typing import Protocol

from collections.abc import AsyncIterator, Sequence

from src.application.dtos.events import ModelEvent
from src.application.dtos.inputs import ModelInput
from src.application.dtos.tools import ModelTool
from src.domain.connections.models import ModelConnection
from src.domain.connections.vo import ModelProtocol


class ModelAdapter(Protocol):
    """Протокол для реализации специфичного API модели."""

    @property
    def protocol(self) -> ModelProtocol: ...

    async def stream(
        self,
        connection: ModelConnection,
        model_id: str,
        inputs: Sequence[ModelInput],
        tools: Sequence[ModelTool] | None = None,
    ) -> AsyncIterator[ModelEvent]: ...
