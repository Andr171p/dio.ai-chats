from typing import Annotated, Literal

from dataclasses import dataclass
from uuid import UUID

from typing_extensions import Doc


@dataclass(frozen=True, slots=True)
class SystemModelRoute:
    """Модель настроенная инфраструктурой сервера."""

    target: str
    type: Literal["system"] = "system"


@dataclass(frozen=True, slots=True)
class RemoteModelRoute:
    """Внешний подключенный endpoint (доступен серверу DIOS)."""

    base_url: str
    credential_id: UUID | None = None

    type: Literal["remote"] = "remote"


@dataclass(frozen=True, slots=True)
class EdgeModelRoute:
    """Клиентская часть управляет секретами и вызовом модели."""

    executor_id: UUID
    local_connection_id: Annotated[str, Doc("Opaque ID локальной конфигурации в DIOS Bridge")]

    type: Literal["edge"] = "edge"


type ModelRoute = SystemModelRoute | RemoteModelRoute | EdgeModelRoute

__all__ = [
    "EdgeModelRoute",
    "ModelRoute",
    "RemoteModelRoute",
    "SystemModelRoute",
]
