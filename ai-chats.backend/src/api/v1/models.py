from fastapi import APIRouter

from src.api.dependencies import ContainerDep, CurrentIdentity
from src.application import connections
from src.application.dtos.connections import AvailableModel

router = APIRouter(prefix="/models", tags=["Модели"])


@router.get(path="", summary="Модели, доступные для чата")
async def list_models(identity: CurrentIdentity, container: ContainerDep) -> list[AvailableModel]:
    return await connections.list_available_models(identity=identity, connections=container.connections)
