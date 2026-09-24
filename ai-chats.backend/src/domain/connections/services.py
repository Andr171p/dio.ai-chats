from decimal import Decimal

from .vo import ModelPricing, Usage, UsageCost


def calculate_usage_cost(usage: Usage, pricing: ModelPricing) -> UsageCost:
    """Рассчитывает фактические затраты за использованные токены."""

    unit = Decimal(1_000_000)

    return UsageCost(
        input=Decimal(usage.input_tokens) / unit * pricing.input,
        output=Decimal(usage.output_tokens) / unit * pricing.output,
        cache_read=(Decimal(usage.cached_input_tokens) / unit * pricing.cache_read),
        cache_write=(Decimal(usage.cache_write_input_tokens) / unit * pricing.cache_write),
        currency=pricing.currency,
    )
