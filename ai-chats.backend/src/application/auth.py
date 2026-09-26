from typing import Annotated, Protocol

from dataclasses import dataclass, field
from enum import IntEnum, auto
from http import HTTPStatus
from uuid import UUID

from ddf.application.exceptions import ApplicationError
from ddf.domain.vo.email import Email
from typing_extensions import Doc

ADMIN_ROLE = "admin"


class IdentityType(IntEnum):
    """Тип субъекта авторизации."""

    USER = auto()
    SERVICE_ACCOUNT = auto()
    AI_AGENT = auto()


@dataclass(frozen=True, slots=True)
class Identity:
    """Субъект авторизации - аутентифицированная сущность выполняющая запрос."""

    id: UUID
    type: IdentityType
    organization_id: Annotated[UUID, Doc("Чаты доступны только участникам организации")]

    email: Email | None = None
    roles: frozenset[str] = field(default_factory=frozenset)

    @property
    def is_admin(self) -> bool:
        return ADMIN_ROLE in self.roles


class IdentityProvider(Protocol):
    """Проверяет токен доступа и возвращает субъекта запроса."""

    async def authenticate(self, token: str) -> Identity: ...


class UnauthorizedError(ApplicationError):
    status_code = HTTPStatus.UNAUTHORIZED
    error_code = "unauthorized"


class PermissionDeniedError(ApplicationError):
    status_code = HTTPStatus.FORBIDDEN
    error_code = "permission_denied"


def ensure_admin(identity: Identity) -> None:
    if not identity.is_admin:
        raise PermissionDeniedError("Administrator role is required.")
