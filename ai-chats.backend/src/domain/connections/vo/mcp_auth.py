"""Виды авторизации MCP клиентов."""

from typing import Literal

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class NoMcpAuth:
    type: Literal["none"] = "none"


@dataclass(frozen=True, slots=True)
class ApiKeyMcpAuth:
    credential_id: UUID
    type: Literal["api_key"] = "api_key"


@dataclass(frozen=True, slots=True)
class OAuthMcpAuth:
    authorization_id: UUID
    type: Literal["oauth"] = "oauth"


McpAuth = NoMcpAuth | ApiKeyMcpAuth | OAuthMcpAuth

__all__ = ["ApiKeyMcpAuth", "McpAuth", "NoMcpAuth", "OAuthMcpAuth"]
