from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue
from pydantic.alias_generators import to_camel

from src.domain.connections.vo import Usage
from src.domain.runs.vo import FinishReason


class ModelTextDelta(BaseModel):
    """Очередной фрагмент генерируемого текста."""

    model_config = ConfigDict(frozen=True, alias_generator=to_camel)

    type: Literal["text_delta"] = "text_delta"
    delta: str = Field(description="Сгенерированный кусок")


class ModelToolCall(BaseModel):
    """Полностью сформированный tool call от модели."""

    model_config = ConfigDict(frozen=True, alias_generator=to_camel)

    type: Literal["tool_call"] = "tool_call"

    call_id: str = Field(description="Идентификатор вызова")
    name: str = Field(description="Имя инструмента")
    arguments: dict[str, JsonValue] = Field(description="Переданные аргументы в tool")


class ModelCompleted(BaseModel):
    """Завершение генерации для одного вызова модели."""

    model_config = ConfigDict(frozen=True, alias_generator=to_camel)

    type: Literal["completed"] = "completed"

    finish_reason: FinishReason = Field(description="Причина завершения генерации")
    usage: Usage | None = Field(default=None, description="Потрачено на вызов")

    provider_request_id: str | None = Field(
        default=None,
        description="Идентификатор запроса провайдера (для трассировки)",
    )


type ModelEvent = Annotated[
    ModelTextDelta | ModelToolCall | ModelCompleted,
    Field(discriminator="type"),
]

__all__ = [
    "ModelCompleted",
    "ModelEvent",
    "ModelTextDelta",
    "ModelToolCall",
]
