from typing import Any

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

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


type RunStep = ModelCall | McpToolCall

__all__ = ["McpToolCall", "ModelCall", "RunStep"]
