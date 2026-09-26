"""События генерации ответа, которые клиент получает потоком."""

from typing import Annotated, Literal

from uuid import UUID

from pydantic import Field

from src.domain.connections.vo import Usage
from src.domain.runs import ExecutionError, FinishReason

from .base import CamelModel
from .conversations import ConversationResponse, MessageResponse


class RunStarted(CamelModel):
    type: Literal["run.started"] = "run.started"
    run_id: UUID
    input_message: MessageResponse


class MessageDelta(CamelModel):
    type: Literal["message.delta"] = "message.delta"
    run_id: UUID
    delta: str


class RunCompleted(CamelModel):
    type: Literal["run.completed"] = "run.completed"
    run_id: UUID
    output_message: MessageResponse
    finish_reason: FinishReason
    usage: Usage


class RunFailed(CamelModel):
    type: Literal["run.failed"] = "run.failed"
    run_id: UUID
    error: ExecutionError


class ConversationUpdated(CamelModel):
    """Чат изменился во время генерации (например, появился автозаголовок)."""

    type: Literal["conversation.updated"] = "conversation.updated"
    conversation: ConversationResponse


type RunEvent = Annotated[
    RunStarted | MessageDelta | RunCompleted | RunFailed | ConversationUpdated,
    Field(discriminator="type"),
]
