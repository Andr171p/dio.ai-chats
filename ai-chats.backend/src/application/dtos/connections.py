from typing import Literal

from datetime import datetime
from uuid import UUID

from pydantic import Field, HttpUrl, SecretStr

from src.domain.connections.vo import (
    ConnectionOwner,
    EdgeModelRoute,
    Modality,
    ModelCapability,
    ModelProtocol,
    ModelSpec,
)

from .base import CamelModel


class ServerRouteInput(CamelModel):
    """Модель вызывается с сервера по OpenAI-совместимому адресу."""

    type: Literal["system"] = "system"
    base_url: HttpUrl = Field(description="Базовый URL API, например - `https://api.openai.com/v1`")
    api_key: SecretStr | None = Field(default=None, description="Не требуется для локальных моделей")


class CreateModelConnection(CamelModel):
    name: str = Field(min_length=1, max_length=100)
    protocol: ModelProtocol
    route: ServerRouteInput
    models: tuple[ModelSpec, ...] = Field(min_length=1, description="Модели, доступные через подключение")
    enabled: bool = True


class UpdateModelConnection(CamelModel):
    """Частичное изменение: не переданные поля остаются прежними."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    enabled: bool | None = None
    models: tuple[ModelSpec, ...] | None = Field(default=None, min_length=1)
    base_url: HttpUrl | None = None
    api_key: SecretStr | None = Field(default=None, description="Заменяет текущий ключ")


class ServerRouteResponse(CamelModel):
    type: Literal["system"] = "system"
    base_url: str
    has_api_key: bool


class ModelConnectionResponse(CamelModel):
    id: UUID
    owner: ConnectionOwner
    name: str
    protocol: ModelProtocol
    route: ServerRouteResponse | EdgeModelRoute
    models: tuple[ModelSpec, ...]
    enabled: bool
    created_at: datetime
    updated_at: datetime


class AvailableModel(CamelModel):
    """Модель, которую пользователь может выбрать в чате."""

    connection_id: UUID
    connection_name: str
    model_id: str
    provider: str
    input_modalities: frozenset[Modality]
    output_modalities: frozenset[Modality]
    capabilities: frozenset[ModelCapability]
    context_window: int
    max_output_tokens: int | None
