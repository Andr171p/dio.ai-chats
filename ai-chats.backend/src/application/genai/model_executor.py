from collections.abc import AsyncIterator, Mapping, Sequence

from src.application.dtos.events import ModelEvent
from src.application.dtos.inputs import ModelInput
from src.application.dtos.tools import ModelTool
from src.domain.connections.models import ModelConnection
from src.domain.connections.vo import ModelProtocol

from .exceptions import EdgeExecutionNotConfiguredError, ModelProtocolNotSupportedError
from .model_adapter import ModelAdapter


class ModelExecutor:
    """Управляет жизненным циклом вызова ИИ модели."""

    def __init__(
        self,
        adapters: Mapping[ModelProtocol, ModelAdapter],
        *,
        edge_adapter: ModelAdapter | None = None,
    ) -> None:
        self._adapters = adapters
        self._edge_adapter = edge_adapter

    async def stream(
        self,
        connection: ModelConnection,
        model_id: str,
        inputs: Sequence[ModelInput],
        tools: Sequence[ModelTool] | None = None,
    ) -> AsyncIterator[ModelEvent]:
        """"""

        if not connection.enabled:
            raise ModelProtocolNotSupportedError(f"Model connection {connection.id!r} is disabled.")

        adapter = self._resolve_adapter(connection)

        async for event in adapter.stream(
            connection=connection,
            model_id=model_id,
            inputs=inputs,
            tools=tools,
        ):
            yield event

    def _resolve_adapter(self, connection: ModelConnection) -> ModelAdapter:
        """Выбирает реализацию для вызова модели по ``ModelConnection``."""

        if connection.route.type == "edge":
            if self._edge_adapter is None:
                raise EdgeExecutionNotConfiguredError("Edge model execution is not configured.")

            return self._edge_adapter

        if (model_adapter := self._adapters.get(connection.protocol)) is None:
            raise ModelProtocolNotSupportedError(f"Unsupported model protocol: {connection.protocol}.")

        return model_adapter
