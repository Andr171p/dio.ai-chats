from typing import Protocol

from pydantic import JsonValue, SecretStr

from src.application.dtos.tools import McpServerDescription, McpToolResult
from src.domain.connections.models import McpConnection


class McpClient(Protocol):
    """Обращения к MCP серверам от имени пользователя.

    ``access_token`` - токен пользователя DIOS, нужен серверам экосистемы (``DiosMcpAuth``).
    """

    async def describe(self, connection: McpConnection, *, access_token: SecretStr) -> McpServerDescription:
        """Инструкции и инструменты сервера."""
        ...

    async def call_tool(
        self,
        connection: McpConnection,
        name: str,
        arguments: dict[str, JsonValue],
        *,
        access_token: SecretStr,
    ) -> McpToolResult:
        """Вызывает инструмент. Ошибку самого инструмента возвращает в результате с ``is_error``."""
        ...
