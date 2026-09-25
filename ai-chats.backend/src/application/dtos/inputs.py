"""
Input DTO для application слоя, не являются строгой реализацией
под конкретного провайдера, а описывают семантику передаваемого контекста.
"""

from typing import Annotated, Literal

from uuid import UUID

from pydantic import Base64Str, BaseModel, Field, HttpUrl, JsonValue


class InstructionsInput(BaseModel):
    type: Literal["instructions"] = "instructions"
    text: str


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class AttachmentContent(BaseModel):
    type: Literal["content"] = "content"
    attachment_id: UUID = Field(description="Идентификатор вложения из Media Service")
    content_type: str
    filename: str | None = None


class JsonContent(BaseModel):
    type: Literal["json"] = "json"
    value: JsonValue


type MessageContent = Annotated[
    TextContent | AttachmentContent | JsonContent,
    Field(discriminator="type"),
]


class MessageInput(BaseModel):
    type: Literal["message"] = "message"
    role: Literal["user", "assistant"]
    content: tuple[MessageContent, ...]


class ToolCallInput(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    call_id: str
    name: str
    arguments: dict[str, JsonValue]


class ToolResultInput(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    call_id: str
    content: tuple[MessageContent, ...]
    is_error: bool = False


type ModelInput = Annotated[
    InstructionsInput
    | MessageInput
    | ToolCallInput
    | ToolResultInput,
    Field(discriminator="type"),
]

__all__ = [
    "AttachmentContent",
    "InstructionsInput",
    "JsonContent",
    "MessageContent",
    "MessageInput",
    "ModelInput",
    "TextContent",
    "ToolCallInput",
    "ToolResultInput",
]
