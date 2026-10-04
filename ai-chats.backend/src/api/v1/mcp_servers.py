from uuid import UUID

from fastapi import APIRouter

from src.api.dependencies import AccessToken, ContainerDep, CurrentIdentity
from src.application import mcp_connections
from src.application.dtos.mcp import AvailableMcpServer, McpToolResponse

router = APIRouter(prefix="/mcp-servers", tags=["MCP серверы"])


@router.get(path="", summary="MCP серверы, доступные для чата")
async def list_mcp_servers(identity: CurrentIdentity, container: ContainerDep) -> list[AvailableMcpServer]:
    return await mcp_connections.list_available_mcp_servers(
        identity=identity, mcp_connections=container.mcp_connections
    )


@router.get(
    path="/{connection_id}/tools",
    summary="Инструменты MCP сервера",
    description="Запрашиваются у сервера от имени пользователя: список зависит от его прав.",
)
async def list_mcp_tools(
    connection_id: UUID,
    identity: CurrentIdentity,
    access_token: AccessToken,
    container: ContainerDep,
) -> list[McpToolResponse]:
    return await mcp_connections.list_mcp_tools(
        connection_id,
        identity=identity,
        access_token=access_token,
        mcp_connections=container.mcp_connections,
        mcp_client=container.mcp_client,
    )
