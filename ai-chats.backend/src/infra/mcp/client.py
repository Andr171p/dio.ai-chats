from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx2
from ddf.application.exceptions import ApplicationError
from mcp import Client, MCPError
from mcp import types as mcp_types
from mcp.client.streamable_http import streamable_http_client
from pydantic import JsonValue, SecretStr

from src.application.dtos.inputs import JsonContent, MessageContent, TextContent
from src.application.dtos.tools import McpServerDescription, McpTool, McpToolResult
from src.application.mcp.exceptions import McpConnectionNotSupportedError, McpServerUnavailableError
from src.domain.connections.models import McpConnection
from src.domain.connections.vo import DiosMcpAuth, NoMcpAuth, RemoteMcpRoute, SystemMcpRoute

CLIENT_INFO = mcp_types.Implementation(name="dios-ai-chats", title="DIOS AI Chats", version="0.1.0")

# Инструменты вроде подбора исполнителей считают аналитику - даём им время
HTTP_TIMEOUT = httpx2.Timeout(30, read=120)


class StreamableHttpMcpClient:
    """MCP клиент поверх Streamable HTTP.

    Сессия живёт одно обращение: серверы экосистемы stateless, а токен
    пользователя у каждого запроса свой.
    """

    async def describe(self, connection: McpConnection, *, access_token: SecretStr) -> McpServerDescription:
        try:
            async with self._session(connection, access_token) as client:
                tools = [tool async for tool in _list_tools(client)]
                return McpServerDescription(instructions=client.instructions, tools=tuple(tools))

        except ApplicationError:
            raise
        except Exception as error:
            raise _unavailable(connection) from error

    async def call_tool(
        self,
        connection: McpConnection,
        name: str,
        arguments: dict[str, JsonValue],
        *,
        access_token: SecretStr,
    ) -> McpToolResult:
        try:
            async with self._session(connection, access_token) as client:
                try:
                    result = await client.call_tool(name, arguments)
                except MCPError as error:
                    # Сервер ответил ошибкой протокола (неверные аргументы, нет инструмента)
                    return McpToolResult.error(error.error.message)

        except ApplicationError:
            raise
        except Exception as error:
            raise _unavailable(connection) from error

        return _to_tool_result(result)

    @asynccontextmanager
    async def _session(self, connection: McpConnection, access_token: SecretStr) -> AsyncIterator[Client]:
        headers = _auth_headers(connection, access_token)
        http_client = httpx2.AsyncClient(headers=headers, timeout=HTTP_TIMEOUT)

        async with (
            http_client,
            Client(
                streamable_http_client(_endpoint(connection), http_client=http_client),
                client_info=CLIENT_INFO,
            ) as client,
        ):
            yield client


async def _list_tools(client: Client) -> AsyncIterator[McpTool]:
    cursor: str | None = None

    while True:
        page = await client.list_tools(cursor=cursor)

        for tool in page.tools:
            yield McpTool(
                name=tool.name,
                title=tool.title or (tool.annotations.title if tool.annotations else None),
                description=tool.description,
                input_schema=tool.input_schema,
            )

        if (cursor := page.next_cursor) is None:
            return


def _endpoint(connection: McpConnection) -> str:
    match connection.route:
        case SystemMcpRoute(target=url) | RemoteMcpRoute(url=url):
            return url

    raise McpConnectionNotSupportedError(f"MCP route {connection.route.type!r} is not supported yet.")


def _auth_headers(connection: McpConnection, access_token: SecretStr) -> dict[str, str]:
    match connection.auth:
        case NoMcpAuth():
            return {}

        case DiosMcpAuth():
            return {"Authorization": f"Bearer {access_token.get_secret_value()}"}

    raise McpConnectionNotSupportedError(f"MCP auth {connection.auth.type!r} is not supported yet.")


def _to_tool_result(result: mcp_types.CallToolResult) -> McpToolResult:
    content: list[MessageContent] = [
        TextContent(text=block.text) for block in result.content if isinstance(block, mcp_types.TextContent)
    ]

    if not content and result.structured_content is not None:
        content.append(JsonContent(value=result.structured_content))

    return McpToolResult(
        content=tuple(content),
        structured_content=result.structured_content,
        is_error=result.is_error,
    )


def _unavailable(connection: McpConnection) -> McpServerUnavailableError:
    return McpServerUnavailableError(f"MCP server {connection.name!r} is unavailable.")
