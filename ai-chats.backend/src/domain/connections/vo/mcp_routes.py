from typing import Literal

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SystemMcpRoute:
    """MCP endpoint, настроенный системной инфраструктурой."""

    target: str
    type: Literal["managed"] = "managed"


@dataclass(frozen=True, slots=True)
class RemoteMcpRoute:
    """Внешний MCP endpoint, доступный для сервера."""

    url: str
    type: Literal["remote"] = "remote"


@dataclass(frozen=True, slots=True)
class EdgeMcpRoute:
    executor_id: UUID
    local_connection_id: str

    type: Literal["edge"] = "edge"


type McpRoute = SystemMcpRoute | RemoteMcpRoute | EdgeMcpRoute

__all__ = ["EdgeMcpRoute", "McpRoute", "RemoteMcpRoute", "SystemMcpRoute"]
