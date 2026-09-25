from typing import Annotated

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID

from typing_extensions import Doc

from .usage import ModelPricing


class ModelProtocol(StrEnum):
    OPENAI_RESPONSES = "openai_responses"
    OPENAI_CHAT_COMPLETIONS = "openai_chat_completions"
    ANTHROPIC_MESSAGES = "anthropic_messages"
    GEMINI = "gemini"


class Modality(StrEnum):
    """Тип данных, который модель может принимать или генерировать."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class ModelCapability(StrEnum):
    """Дополнительные возможности модели, не описываемые модальностью."""

    TOOLS = "tools"
    STRUCTURED_OUTPUT = "structured_output"
    REASONING = "reasoning"
    FILE_INPUT = "file_input"


@dataclass(frozen=True, slots=True)
class ModelSpec:
    """Декларативное описание доступной модели."""

    id: Annotated[str, Doc("Идентификатор модели, например - `gpt-5.6-sol`")]
    provider: Annotated[str, Doc("Идентификатор провайдера или источника модели (`openai`, `google`)")]

    input_modalities: frozenset[Modality]
    output_modalities: frozenset[Modality]

    context_window: Annotated[int, Doc("Максимальный размер контекстного окна модели в токенах")]
    max_output_tokens: int | None = None

    capabilities: frozenset[ModelCapability] = field(default_factory=frozenset)

    pricing: ModelPricing | None = None


@dataclass(frozen=True, slots=True)
class ModelSelection:
    """Ссылка на выбранную модель."""

    connection_id: UUID
    model_id: Annotated[str, Doc("Идентификатор модели, например - `gpt-5.6-sol`")]
