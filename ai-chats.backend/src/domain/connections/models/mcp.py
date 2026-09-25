from dataclasses import dataclass

from ddf.domain.models import AggregateRoot

from src.domain.connections.vo import ConnectionOwner, McpAuth, McpRoute


@dataclass(kw_only=True)
class McpConnection(AggregateRoot):
    """Подключение к MCP серверу."""

    owner: ConnectionOwner
    name: str
    route: McpRoute
    auth: McpAuth
    enabled: bool = True
