from uuid import UUID

from ddf.application.dtos import Page, PaginationQuery
from fastapi import APIRouter, status

from src.api.dependencies import ContainerDep, CurrentIdentity
from src.application import mcp_connections
from src.application.dtos.mcp import CreateMcpConnection, McpConnectionResponse, UpdateMcpConnection

router = APIRouter(prefix="/mcp-connections", tags=["Подключения MCP серверов"])


@router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    summary="Подключить MCP сервер",
    description="Доступно администратору. Сервер становится доступен для чатов всех пользователей.",
)
async def create_mcp_connection(
    command: CreateMcpConnection,
    identity: CurrentIdentity,
    container: ContainerDep,
) -> McpConnectionResponse:
    return await mcp_connections.create_mcp_connection(
        command, identity=identity, mcp_connections=container.mcp_connections
    )


@router.get(path="", summary="Подключения MCP серверов")
async def list_mcp_connections(
    pagination: PaginationQuery,
    identity: CurrentIdentity,
    container: ContainerDep,
) -> Page[McpConnectionResponse]:
    return await mcp_connections.list_mcp_connections(
        pagination, identity=identity, mcp_connections=container.mcp_connections
    )


@router.patch(path="/{connection_id}", summary="Изменить подключение MCP сервера")
async def update_mcp_connection(
    connection_id: UUID,
    command: UpdateMcpConnection,
    identity: CurrentIdentity,
    container: ContainerDep,
) -> McpConnectionResponse:
    return await mcp_connections.update_mcp_connection(
        connection_id, command, identity=identity, mcp_connections=container.mcp_connections
    )


@router.delete(path="/{connection_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить подключение")
async def delete_mcp_connection(
    connection_id: UUID, identity: CurrentIdentity, container: ContainerDep
) -> None:
    await mcp_connections.delete_mcp_connection(
        connection_id, identity=identity, mcp_connections=container.mcp_connections
    )
