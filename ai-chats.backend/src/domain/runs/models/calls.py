from typing import Any

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from ddf.domain.exceptions import InvalidStateError
from ddf.domain.models import Entity

from src.domain.connections.vo import ModelSelection, Usage
from src.domain.runs.types import JsonValue
from src.domain.runs.vo import ExecutionError, FinishReason, McpToolCallStatus


@dataclass(kw_only=True)
class ModelCall(Entity):
    """Один физический вызов модели внутри ``Run``."""

    run_id: UUID
    sequence: int

    model: ModelSelection

    started_at: datetime
    finished_at: datetime | None = None

    finish_reason: FinishReason | None = None
    error: ExecutionError | None = None
    usage: Usage = field(default_factory=Usage)

    meta: dict[str, Any] = field(default_factory=dict)

    def finish(
        self,
        finish_reason: FinishReason,
        *,
        usage: Usage | None = None,
        error: ExecutionError | None = None,
    ) -> None:
        """Фиксирует итог вызова модели."""

        if self.finished_at is not None:
            raise InvalidStateError("Model call is already finished.")

        self.finish_reason = finish_reason
        self.error = error
        self.finished_at = datetime.now(UTC)

        if usage is not None:
            self.usage = usage


@dataclass(kw_only=True)
class McpToolCall(Entity):
    """Вызов MCP Tool, инициированный моделью."""

    run_id: UUID
    model_call_id: UUID
    connection_id: UUID

    status: McpToolCallStatus

    name: str
    arguments: dict[str, JsonValue]
    result: JsonValue | None = None
    error: ExecutionError | None = None

    def complete(self, result: JsonValue) -> None:
        self._finish(McpToolCallStatus.COMPLETED, result=result)

    def fail(self, error: ExecutionError, *, result: JsonValue | None = None) -> None:
        """Ошибка вызова; ``result`` - ответ сервера, если инструмент сам сообщил об ошибке."""

        self._finish(McpToolCallStatus.FAILED, result=result, error=error)

    def cancel(self) -> None:
        self._finish(McpToolCallStatus.CANCELLED)

    @property
    def is_finished(self) -> bool:
        return self.status in {
            McpToolCallStatus.COMPLETED,
            McpToolCallStatus.FAILED,
            McpToolCallStatus.CANCELLED,
        }

    def _finish(
        self,
        status: McpToolCallStatus,
        *,
        result: JsonValue | None = None,
        error: ExecutionError | None = None,
    ) -> None:
        if self.is_finished:
            raise InvalidStateError("Tool call is already finished.")

        self.status = status
        self.result = result
        self.error = error


type RunStep = ModelCall | McpToolCall

__all__ = ["McpToolCall", "ModelCall", "RunStep"]
