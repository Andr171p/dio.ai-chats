"""MCP серверы: администрирование и каталог для подключения к чатам."""

from collections.abc import Sequence
from dataclasses import replace
from http import HTTPStatus
from uuid import UUID

from ddf.application.dsl import Condition, Expression, Group
from ddf.application.dtos import CursorPagination, Page, Pagination, Sort
from ddf.application.exceptions import ApplicationError
from ddf.application.repositories import Repository
from ddf.application.utils import get_or_raise_not_found, iterate_batches
from ddf.domain.utils import apply_changes
from pydantic import SecretStr

from src.domain.connections.models import McpConnection
from src.domain.connections.services import is_available_to
from src.domain.connections.vo import SystemMcpRoute, SystemOwner

from .auth import Identity, ensure_admin
from .connections import RouteNotEditableError, available_to
from .dtos.mcp import (
    AvailableMcpServer,
    CreateMcpConnection,
    McpConnectionResponse,
    McpToolResponse,
    UpdateMcpConnection,
)
from .mcp.client import McpClient


class McpConnectionUnavailableError(ApplicationError):
    status_code = HTTPStatus.UNPROCESSABLE_CONTENT
    error_code = "mcp_connection_unavailable"


async def create_mcp_connection(
    command: CreateMcpConnection,
    *,
    identity: Identity,
    mcp_connections: Repository[McpConnection],
) -> McpConnectionResponse:
    ensure_admin(identity)

    connection = McpConnection(
        owner=SystemOwner(),
        name=command.name,
        route=SystemMcpRoute(target=str(command.url)),
        auth=command.auth,
        enabled=command.enabled,
    )
    await mcp_connections.create(connection)

    return to_mcp_connection_response(connection)


async def list_mcp_connections(
    pagination: Pagination,
    *,
    identity: Identity,
    mcp_connections: Repository[McpConnection],
) -> Page[McpConnectionResponse]:
    ensure_admin(identity)

    page = await mcp_connections.find(pagination, sort=Sort(field="id", direction="desc"))
    return page.map(to_mcp_connection_response)


async def update_mcp_connection(
    connection_id: UUID,
    command: UpdateMcpConnection,
    *,
    identity: Identity,
    mcp_connections: Repository[McpConnection],
) -> McpConnectionResponse:
    ensure_admin(identity)

    connection = await get_or_raise_not_found(mcp_connections.read, connection_id, McpConnection)

    route = connection.route
    if command.url is not None:
        if not isinstance(route, SystemMcpRoute):
            raise RouteNotEditableError("Only managed MCP routes have URL.")
        route = replace(route, target=str(command.url))

    apply_changes(connection, name=command.name, enabled=command.enabled, route=route)
    await mcp_connections.update(connection)

    return to_mcp_connection_response(connection)


async def delete_mcp_connection(
    connection_id: UUID,
    *,
    identity: Identity,
    mcp_connections: Repository[McpConnection],
) -> None:
    ensure_admin(identity)

    connection = await get_or_raise_not_found(mcp_connections.read, connection_id, McpConnection)
    await mcp_connections.delete(connection.id)


async def list_available_mcp_servers(
    *,
    identity: Identity,
    mcp_connections: Repository[McpConnection],
) -> list[AvailableMcpServer]:
    """Каталог MCP серверов для подключения к чату."""

    return [
        AvailableMcpServer(connection_id=connection.id, name=connection.name)
        for connection in await _find_usable(mcp_connections, identity)
    ]


async def list_mcp_tools(
    connection_id: UUID,
    *,
    identity: Identity,
    access_token: SecretStr,
    mcp_connections: Repository[McpConnection],
    mcp_client: McpClient,
) -> list[McpToolResponse]:
    """Инструменты сервера, которые увидит модель этого пользователя."""

    connection = await mcp_connections.read(connection_id)

    if connection is None or not _is_usable(connection, identity):
        raise McpConnectionUnavailableError(f"MCP server {connection_id} is not available.")

    description = await mcp_client.describe(connection, access_token=access_token)
    return [McpToolResponse.model_validate(tool) for tool in description.tools]


async def get_usable_mcp_connections(
    connection_ids: Sequence[UUID],
    *,
    identity: Identity,
    mcp_connections: Repository[McpConnection],
) -> list[McpConnection]:
    """Подключения из списка, которые сейчас доступны пользователю; остальные отбрасываются."""

    if not connection_ids:
        return []

    query = Condition(field="id", op="$in", value=list(connection_ids))
    return await _find_usable(mcp_connections, identity, query)


async def ensure_usable_mcp_connections(
    connection_ids: Sequence[UUID],
    *,
    identity: Identity,
    mcp_connections: Repository[McpConnection],
) -> None:
    usable = await get_usable_mcp_connections(
        connection_ids, identity=identity, mcp_connections=mcp_connections
    )

    if missing := set(connection_ids) - {connection.id for connection in usable}:
        raise McpConnectionUnavailableError(f"MCP servers {sorted(map(str, missing))} are not available.")


def to_mcp_connection_response(connection: McpConnection) -> McpConnectionResponse:
    return McpConnectionResponse.model_validate(connection)


def _is_usable(connection: McpConnection, identity: Identity) -> bool:
    return connection.enabled and is_available_to(
        connection.owner, organization_id=identity.organization_id, user_id=identity.id
    )


async def _find_usable(
    mcp_connections: Repository[McpConnection],
    identity: Identity,
    query: Expression | None = None,
) -> list[McpConnection]:
    usable = available_to(identity)
    batches = iterate_batches(
        mcp_connections,
        CursorPagination(size=100),
        query=usable if query is None else Group(op="$and", filters=(usable, query)),
        sort=Sort(field="id", direction="asc"),
    )

    return [connection async for batch in batches for connection in batch]
