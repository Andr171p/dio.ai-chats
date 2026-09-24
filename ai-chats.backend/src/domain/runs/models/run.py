from typing import Annotated

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from ddf.domain.exceptions import InvalidStateError
from ddf.domain.models import AggregateRoot
from typing_extensions import Doc

from src.domain.connections.vo import ModelSelection, Usage
from src.domain.runs.vo import ExecutionError, RunStatus

from .calls import RunStep


@dataclass(kw_only=True)
class Run(AggregateRoot):
    """Выполнение одного assistant turn."""

    thread_id: UUID

    input_message_id: UUID
    output_message_id: UUID | None = None

    model: Annotated[ModelSelection, Doc("Выбор модели не меняется после создания ``Run``")]
    status: RunStatus
    steps: list[RunStep] = field(default_factory=list)

    started_at: datetime
    finished_at: datetime | None = None

    usage: Usage = field(default_factory=Usage)
    error: ExecutionError | None = None

    def start(self) -> None:
        if self.status is not RunStatus.PENDING:
            raise InvalidStateError("Only pending run can be started.")

        self.status = RunStatus.RUNNING
        self.started_at = datetime.now(UTC)

    def wait_for_approval(self) -> None:
        if self.status is not RunStatus.RUNNING:
            raise ValueError("Only running run can wait for approval.")

        self.status = RunStatus.WAITING_APPROVAL

    def resume(self) -> None:
        if self.status is not RunStatus.WAITING_APPROVAL:
            raise ValueError("Run is not waiting for approval.")

        self.status = RunStatus.RUNNING

    def complete(self, *, output_message_id: UUID, usage: Usage) -> None:
        self.output_message_id = output_message_id
        self.usage = usage
        self.status = RunStatus.COMPLETED
        self.finished_at = datetime.now(UTC)

    def fail(self, *, error_code: str, error_message: str) -> None:
        self.error = ExecutionError(code=error_code, message=error_message)
        self.status = RunStatus.FAILED
        self.finished_at = datetime.now(UTC)

    def cancel(self) -> None:
        self.status = RunStatus.CANCELLED
        self.finished_at = datetime.now(UTC)
