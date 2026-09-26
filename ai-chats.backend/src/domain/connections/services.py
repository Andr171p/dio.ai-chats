from decimal import Decimal
from uuid import UUID

from .vo import ConnectionOwner, ModelPricing, OrganizationOwner, SystemOwner, Usage, UsageCost, UserOwner


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


def is_available_to(owner: ConnectionOwner, *, organization_id: UUID, user_id: UUID) -> bool:
    """Доступно ли подключение пользователю с учётом области владения."""

    match owner:
        case SystemOwner():
            return True

        case OrganizationOwner():
            return owner.organization_id == organization_id

        case UserOwner():
            return owner.organization_id == organization_id and owner.user_id == user_id

    return False
