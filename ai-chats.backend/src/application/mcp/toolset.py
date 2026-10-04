from typing import Self

import asyncio
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ddf.application.exceptions import ApplicationError
from pydantic import JsonValue, SecretStr

from src.application.dtos.tools import McpServerDescription, McpTool, McpToolResult, ModelTool
from src.domain.connections.models import McpConnection

from .client import McpClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class BoundTool:
    """Инструмент MCP сервера под именем, уникальным среди инструментов чата."""

    name: str
    connection: McpConnection
    tool: McpTool


class Toolset:
    """Инструменты MCP серверов, подключённых к чату, и их инструкции для модели."""

    def __init__(
        self,
        client: McpClient,
        *,
        access_token: SecretStr,
        tools: Mapping[str, BoundTool],
        instructions: Sequence[str],
    ) -> None:
        self._client = client
        self._access_token = access_token
        self._tools = tools
        self._instructions = instructions

    @classmethod
    async def load(
        cls,
        client: McpClient,
        connections: Sequence[McpConnection],
        *,
        access_token: SecretStr,
    ) -> Self:
        """Опрашивает серверы параллельно; недоступный сервер пропускается, чтобы не ломать диалог."""

        descriptions = await asyncio.gather(
            *(_describe(client, connection, access_token) for connection in connections)
        )
        tools: dict[str, BoundTool] = {}
        instructions: list[str] = []

        for connection, description in zip(connections, descriptions, strict=True):
            if description is None:
                continue

            if description.instructions:
                instructions.append(f"# {connection.name}\n\n{description.instructions}")

            for tool in description.tools:
                name = _unique_name(tool.name, tools)
                tools[name] = BoundTool(name=name, connection=connection, tool=tool)

        return cls(client, access_token=access_token, tools=tools, instructions=instructions)

    @property
    def tools(self) -> list[ModelTool]:
        return [
            ModelTool(
                name=bound.name,
                description=bound.tool.description,
                input_schema=bound.tool.input_schema,
            )
            for bound in self._tools.values()
        ]

    @property
    def instructions(self) -> str | None:
        return "\n\n".join(self._instructions) or None

    def get(self, name: str) -> BoundTool | None:
        return self._tools.get(name)

    async def call(self, tool: BoundTool, arguments: dict[str, JsonValue]) -> McpToolResult:
        """Недоступность сервера - тоже результат: модель объяснит её пользователю."""

        try:
            return await self._client.call_tool(
                tool.connection, tool.tool.name, arguments, access_token=self._access_token
            )
        except ApplicationError as error:
            logger.warning("MCP tool %s call failed", tool.tool.name, exc_info=True)
            return McpToolResult.error(error.message or error.error_code)


async def _describe(
    client: McpClient, connection: McpConnection, access_token: SecretStr
) -> McpServerDescription | None:
    try:
        return await client.describe(connection, access_token=access_token)
    except ApplicationError:
        logger.warning("MCP server %s is unavailable, its tools are skipped", connection.id, exc_info=True)
        return None


def _unique_name(name: str, taken: Mapping[str, object]) -> str:
    """Одноимённые инструменты разных серверов получают суффикс: ``create_task_2``."""

    candidate, index = name, 1
    while candidate in taken:
        index += 1
        candidate = f"{name}_{index}"

    return candidate
