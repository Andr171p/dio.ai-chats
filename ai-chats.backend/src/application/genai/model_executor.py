from collections.abc import AsyncIterator, Callable, Sequence

from src.application.dtos.events import ModelEvent
from src.application.dtos.inputs import ModelInput
from src.application.dtos.tools import ModelTool
from src.domain.connections.models import ModelConnection

from .model_adapter import ModelAdapter

type ModelAdapterResolver = Callable[[ModelConnection], ModelAdapter]


async def execute_model(
    resolve_adapter: ModelAdapterResolver,
    *,
    connection: ModelConnection,
    model_id: str,
    inputs: Sequence[ModelInput],
    tools: Sequence[ModelTool] | None = None,
) -> AsyncIterator[ModelEvent]:
    """Выполняет вызов к подключенной модели."""

    adapter = resolve_adapter(connection)

    async for event in adapter.stream(model_id=model_id, inputs=inputs, tools=tools):
        yield event
