from __future__ import annotations

from typing import Annotated

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from typing_extensions import Doc

from .types import Currency


@dataclass(frozen=True, slots=True)
class ModelPricing:
    """Стоимость одного миллиона токенов (политика ценообразования)."""

    input: Decimal
    output: Decimal

    cache_read: Decimal = Decimal("0")
    cache_write: Decimal = Decimal("0")

    currency: Currency = "USD"


@dataclass(frozen=True, slots=True)
class UsageCost:
    """Фактические затраты за использованные токены."""

    input: Decimal
    output: Decimal

    cache_read: Decimal
    cache_write: Decimal

    currency: Currency

    @property
    def total(self) -> Decimal:
        return self.input + self.output + self.cache_read + self.cache_write


@dataclass(frozen=True, slots=True)
class ModelSelection:
    """Выбранная модель в чате."""

    model_id: str
    connection_id: UUID


@dataclass(frozen=True, slots=True)
class Usage:
    input_tokens: Annotated[
        int,
        Doc(
            "Общее число входных токенов. "
            "Cached/cache-write tokens после нормализации входят в это значение."
        ),
    ] = 0
    output_tokens: int = 0

    cached_input_tokens: Annotated[
        int,
        Doc("Подмножество input_tokens, прочитанное из provider prompt cache."),
    ] = 0
    cache_write_input_tokens: Annotated[
        int,
        Doc("Подмножество input_tokens, записанное provider'ом в prompt cache."),
    ] = 0

    reasoning_tokens: Annotated[
        int,
        Doc("Подмножество output_tokens, потраченное моделью на reasoning."),
    ] = 0

    def __post_init__(self) -> None:
        values = (
            self.input_tokens,
            self.output_tokens,
            self.cached_input_tokens,
            self.cache_write_input_tokens,
            self.reasoning_tokens,
        )

        if any(value < 0 for value in values):
            raise ValueError("Token usage cannot be negative.")

        if self.cached_input_tokens > self.input_tokens:
            raise ValueError("cached_input_tokens cannot exceed input_tokens.")

        if self.cache_write_input_tokens > self.input_tokens:
            raise ValueError("cache_write_input_tokens cannot exceed input_tokens.")

        if self.reasoning_tokens > self.output_tokens:
            raise ValueError("reasoning_tokens cannot exceed output_tokens.")

    @property
    def total_tokens(self) -> int:
        """Общее количество потраченных токенов."""
        return self.input_tokens + self.output_tokens

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cached_input_tokens=self.cached_input_tokens + other.cached_input_tokens,
            cache_write_input_tokens=(self.cache_write_input_tokens + other.cache_write_input_tokens),
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
        )
