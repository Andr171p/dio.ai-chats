from typing import Any, ClassVar, Literal

from collections.abc import Sequence
from uuid import UUID

from ddf.infra.database.mongo import MongoBaseModel, MongoEntityMixin
from pydantic import AwareDatetime
from pymongo import ASCENDING, IndexModel

from src.domain.connections.vo import ModelSelection, Usage
from src.domain.runs import ExecutionError, FinishReason, JsonValue, McpToolCallStatus, RunStatus


class ModelCallModel(MongoBaseModel, MongoEntityMixin):
    """Вложенный в run документ вызова модели."""

    type: Literal["model_call"] = "model_call"

    run_id: UUID
    sequence: int
    model: ModelSelection
    started_at: AwareDatetime
    finished_at: AwareDatetime | None
    finish_reason: FinishReason | None
    error: ExecutionError | None
    usage: Usage
    meta: dict[str, Any]


class McpToolCallModel(MongoBaseModel, MongoEntityMixin):
    """Вложенный в run документ вызова MCP tool."""

    type: Literal["mcp_tool_call"] = "mcp_tool_call"

    run_id: UUID
    model_call_id: UUID
    connection_id: UUID
    status: McpToolCallStatus
    name: str
    arguments: dict[str, JsonValue]
    result: JsonValue | None
    error: ExecutionError | None


class RunModel(MongoBaseModel, MongoEntityMixin):
    __collection_name__: ClassVar[str] = "runs"
    __indexes__: ClassVar[Sequence[IndexModel]] = [IndexModel([("threadId", ASCENDING)])]

    thread_id: UUID
    input_message_id: UUID
    output_message_id: UUID | None
    model: ModelSelection
    status: RunStatus
    steps: list[ModelCallModel | McpToolCallModel]
    started_at: AwareDatetime
    finished_at: AwareDatetime | None
    usage: Usage
    error: ExecutionError | None
