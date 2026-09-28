"""Подключения моделей: администрирование и каталог моделей для пользователя."""

from collections.abc import Mapping
from dataclasses import replace
from http import HTTPStatus
from uuid import UUID

from ddf.application.dsl import Condition, Expression, Group
from ddf.application.dtos import CursorPagination, Page, Pagination, Sort
from ddf.application.exceptions import ApplicationError
from ddf.application.repositories import Repository
from ddf.application.utils import get_or_raise_not_found, iterate_batches
from ddf.domain.utils import apply_changes
from pydantic import HttpUrl, SecretStr

from src.domain.connections.models import ModelConnection
from src.domain.connections.services import is_available_to
from src.domain.connections.vo import (
    EdgeModelRoute,
    ModelRoute,
    ModelSelection,
    ServerModelRoute,
    SystemOwner,
)

from .auth import Identity, ensure_admin
from .dtos.connections import (
    AvailableModel,
    CreateModelConnection,
    ModelConnectionResponse,
    ServerRouteResponse,
    UpdateModelConnection,
)
from .secrets.secret_store import SecretStore


class ModelUnavailableError(ApplicationError):
    status_code = HTTPStatus.UNPROCESSABLE_CONTENT
    error_code = "model_unavailable"


class RouteNotEditableError(ApplicationError):
    status_code = HTTPStatus.CONFLICT
    error_code = "route_not_editable"


async def create_model_connection(
    command: CreateModelConnection,
    *,
    identity: Identity,
    connections: Repository[ModelConnection],
    secret_store: SecretStore,
) -> ModelConnectionResponse:
    ensure_admin(identity)

    api_key = command.route.api_key
    credential_id = await secret_store.create(api_key) if api_key is not None else None

    connection = ModelConnection(
        owner=SystemOwner(),
        name=command.name,
        protocol=command.protocol,
        route=ServerModelRoute(base_url=str(command.route.base_url), credential_id=credential_id),
        models=command.models,
        enabled=command.enabled,
    )
    await connections.create(connection)

    return to_connection_response(connection)


async def list_model_connections(
    pagination: Pagination,
    *,
    identity: Identity,
    connections: Repository[ModelConnection],
) -> Page[ModelConnectionResponse]:
    ensure_admin(identity)

    page = await connections.find(pagination, sort=Sort(field="id", direction="desc"))
    return page.map(to_connection_response)


async def get_model_connection(
    connection_id: UUID,
    *,
    identity: Identity,
    connections: Repository[ModelConnection],
) -> ModelConnectionResponse:
    ensure_admin(identity)

    connection = await get_or_raise_not_found(connections.read, connection_id, ModelConnection)
    return to_connection_response(connection)


async def update_model_connection(
    connection_id: UUID,
    command: UpdateModelConnection,
    *,
    identity: Identity,
    connections: Repository[ModelConnection],
    secret_store: SecretStore,
) -> ModelConnectionResponse:
    ensure_admin(identity)

    connection = await get_or_raise_not_found(connections.read, connection_id, ModelConnection)

    route = connection.route
    if command.base_url is not None or command.api_key is not None:
        route = await _change_server_route(
            route,
            base_url=command.base_url,
            api_key=command.api_key,
            secret_store=secret_store,
        )

    apply_changes(connection, name=command.name, enabled=command.enabled, models=command.models, route=route)
    await connections.update(connection)

    return to_connection_response(connection)


async def delete_model_connection(
    connection_id: UUID,
    *,
    identity: Identity,
    connections: Repository[ModelConnection],
    secret_store: SecretStore,
) -> None:
    ensure_admin(identity)

    connection = await get_or_raise_not_found(connections.read, connection_id, ModelConnection)
    await connections.delete(connection.id)

    if isinstance(connection.route, ServerModelRoute) and connection.route.credential_id is not None:
        await secret_store.delete(connection.route.credential_id)


async def list_available_models(
    *,
    identity: Identity,
    connections: Repository[ModelConnection],
) -> list[AvailableModel]:
    """Каталог моделей для выбора в чате."""

    batches = iterate_batches(
        connections,
        CursorPagination(size=100),
        query=_available_to(identity),
        sort=Sort(field="id", direction="asc"),
    )

    return [
        AvailableModel(
            connection_id=connection.id,
            connection_name=connection.name,
            model_id=spec.id,
            provider=spec.provider,
            input_modalities=spec.input_modalities,
            output_modalities=spec.output_modalities,
            capabilities=spec.capabilities,
            context_window=spec.context_window,
            max_output_tokens=spec.max_output_tokens,
        )
        async for batch in batches
        for connection in batch
        for spec in connection.models
    ]


async def get_usable_connection(
    selection: ModelSelection,
    *,
    identity: Identity,
    connections: Repository[ModelConnection],
) -> ModelConnection:
    """Подключение, через которое пользователь может вызвать выбранную модель."""

    connection = await connections.read(selection.connection_id)

    if (
        connection is None
        or not connection.enabled
        or not connection.has_model(selection.model_id)
        or not is_available_to(
            connection.owner, organization_id=identity.organization_id, user_id=identity.id
        )
    ):
        raise ModelUnavailableError(f"Model {selection.model_id!r} is not available.")

    return connection


def to_connection_response(connection: ModelConnection) -> ModelConnectionResponse:
    route: ServerRouteResponse | EdgeModelRoute

    match connection.route:
        case ServerModelRoute(base_url=base_url, credential_id=credential_id):
            route = ServerRouteResponse(base_url=base_url, has_api_key=credential_id is not None)
        case edge_route:
            route = edge_route

    return ModelConnectionResponse(
        id=connection.id,
        owner=connection.owner,
        name=connection.name,
        protocol=connection.protocol,
        route=route,
        models=connection.models,
        enabled=connection.enabled,
        created_at=connection.created_at,
        updated_at=connection.updated_at,
    )


async def _change_server_route(
    route: ModelRoute,
    *,
    base_url: HttpUrl | None,
    api_key: SecretStr | None,
    secret_store: SecretStore,
) -> ServerModelRoute:
    if not isinstance(route, ServerModelRoute):
        raise RouteNotEditableError("Only server routes have base URL and API key.")

    credential_id = route.credential_id

    if api_key is not None:
        if credential_id is None:
            credential_id = await secret_store.create(api_key)
        else:
            await secret_store.replace(credential_id, api_key)

    return replace(
        route,
        base_url=str(base_url) if base_url is not None else route.base_url,
        credential_id=credential_id,
    )


def _available_to(identity: Identity) -> Expression:
    """DSL-версия ``is_available_to`` для выборки включённых подключений."""

    return Group(
        op="$and",
        filters=(
            Condition(field="enabled", op="$eq", value=True),
            Group(
                op="$or",
                filters=(
                    _matches({"owner.scope": "system"}),
                    _matches(
                        {
                            "owner.scope": "organization",
                            "owner.organization_id": identity.organization_id,
                        }
                    ),
                    _matches(
                        {
                            "owner.scope": "user",
                            "owner.organization_id": identity.organization_id,
                            "owner.user_id": identity.id,
                        }
                    ),
                ),
            ),
        ),
    )


def _matches(values: Mapping[str, object]) -> Group:
    return Group(
        op="$and",
        filters=tuple(Condition(field=field, op="$eq", value=value) for field, value in values.items()),
    )
