from typing import Annotated, Literal

from dataclasses import dataclass
from uuid import UUID

from typing_extensions import Doc


@dataclass(frozen=True, slots=True)
class ServerModelRoute:
    """Модель настроенная инфраструктурой сервера."""

    base_url: str
    credential_id: UUID | None

    type: Literal["system"] = "system"


@dataclass(frozen=True, slots=True)
class EdgeModelRoute:
    """Клиентская часть управляет секретами и вызовом модели."""

    endpoint_id: UUID
    local_connection_id: Annotated[str, Doc("Opaque ID локальной конфигурации в DIOS Bridge")]

    type: Literal["edge"] = "edge"


type ModelRoute = ServerModelRoute | EdgeModelRoute

__all__ = [
    "EdgeModelRoute",
    "ModelRoute",
    "ServerModelRoute",
]
