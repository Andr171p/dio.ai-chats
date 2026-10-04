from datetime import datetime
from uuid import UUID

from pydantic import Field, HttpUrl

from src.domain.connections.vo import ConnectionOwner, DiosMcpAuth, McpAuth, McpRoute, NoMcpAuth

from .base import CamelModel


class CreateMcpConnection(CamelModel):
    name: str = Field(min_length=1, max_length=100)
    url: HttpUrl = Field(description="Streamable HTTP endpoint, например - `http://localhost:8001/mcp/`")
    auth: DiosMcpAuth | NoMcpAuth = Field(
        default_factory=DiosMcpAuth,
        description="`dios` - от имени пользователя с его учётной записью DIOS",
    )
    enabled: bool = True


class UpdateMcpConnection(CamelModel):
    """Частичное изменение: не переданные поля остаются прежними."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    url: HttpUrl | None = None
    enabled: bool | None = None


class McpConnectionResponse(CamelModel):
    id: UUID
    owner: ConnectionOwner
    name: str
    route: McpRoute
    auth: McpAuth
    enabled: bool
    created_at: datetime
    updated_at: datetime


class AvailableMcpServer(CamelModel):
    """MCP сервер, который пользователь может подключить к чату."""

    connection_id: UUID
    name: str


class McpToolResponse(CamelModel):
    name: str
    title: str | None
    description: str | None
