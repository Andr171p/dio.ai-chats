from uuid import UUID

from ddf.application.dtos import Page, PaginationQuery
from fastapi import APIRouter, status

from src.api.dependencies import ContainerDep, CurrentIdentity
from src.application import connections
from src.application.dtos.connections import (
    CreateModelConnection,
    ModelConnectionResponse,
    UpdateModelConnection,
)

router = APIRouter(prefix="/model-connections", tags=["Подключения моделей"])


@router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    summary="Подключить источник моделей",
    description="Доступно администратору. Подключение становится доступно всем пользователям.",
)
async def create_model_connection(
    command: CreateModelConnection,
    identity: CurrentIdentity,
    container: ContainerDep,
) -> ModelConnectionResponse:
    return await connections.create_model_connection(
        command,
        identity=identity,
        connections=container.connections,
        secret_store=container.secret_store,
    )


@router.get(path="", summary="Подключения моделей")
async def list_model_connections(
    pagination: PaginationQuery,
    identity: CurrentIdentity,
    container: ContainerDep,
) -> Page[ModelConnectionResponse]:
    return await connections.list_model_connections(
        pagination,
        identity=identity,
        connections=container.connections,
    )


@router.get(path="/{connection_id}", summary="Подключение моделей")
async def get_model_connection(
    connection_id: UUID,
    identity: CurrentIdentity,
    container: ContainerDep,
) -> ModelConnectionResponse:
    return await connections.get_model_connection(
        connection_id,
        identity=identity,
        connections=container.connections,
    )


@router.patch(path="/{connection_id}", summary="Изменить подключение моделей")
async def update_model_connection(
    connection_id: UUID,
    command: UpdateModelConnection,
    identity: CurrentIdentity,
    container: ContainerDep,
) -> ModelConnectionResponse:
    return await connections.update_model_connection(
        connection_id,
        command,
        identity=identity,
        connections=container.connections,
        secret_store=container.secret_store,
    )


@router.delete(path="/{connection_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить подключение")
async def delete_model_connection(
    connection_id: UUID, identity: CurrentIdentity, container: ContainerDep
) -> None:
    await connections.delete_model_connection(
        connection_id,
        identity=identity,
        connections=container.connections,
        secret_store=container.secret_store,
    )
