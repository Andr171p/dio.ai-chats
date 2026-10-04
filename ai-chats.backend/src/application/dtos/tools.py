from typing import Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from .inputs import MessageContent, TextContent


class ModelTool(BaseModel):
    """Tool, доступный модели во время inference (вспомогательный DTO)."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Название инструмента")
    description: str | None = Field(default=None, description="Описание для модели")
    input_schema: dict[str, JsonValue] = Field(description="Схема передаваемых аргументов")


class McpTool(ModelTool):
    """Инструмент, объявленный MCP сервером."""

    title: str | None = Field(default=None, description="Человекочитаемое название")


class McpServerDescription(BaseModel):
    """Что MCP сервер предлагает клиенту."""

    model_config = ConfigDict(frozen=True)

    instructions: str | None = Field(default=None, description="Как модели работать с сервером")
    tools: tuple[McpTool, ...] = ()


class McpToolResult(BaseModel):
    """Результат вызова MCP инструмента."""

    model_config = ConfigDict(frozen=True)

    content: tuple[MessageContent, ...] = Field(description="Результат в виде, понятном модели")
    structured_content: JsonValue = Field(default=None, description="Структурированный результат")
    is_error: bool = False

    @classmethod
    def error(cls, message: str) -> Self:
        return cls(content=(TextContent(text=message),), is_error=True)

    @property
    def text(self) -> str:
        return "\n".join(content.text for content in self.content if isinstance(content, TextContent))

    @property
    def value(self) -> JsonValue:
        """Результат для истории вызовов: структурированный, если сервер его вернул."""

        return self.structured_content if self.structured_content is not None else self.text
