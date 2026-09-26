from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.auth import Identity, UnauthorizedError
from src.bootstrap import Container

_bearer = HTTPBearer(auto_error=False, description="Access токен DIO desk")


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


async def get_current_identity(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    container: ContainerDep,
) -> Identity:
    if credentials is None:
        raise UnauthorizedError("Authorization header is missing.")

    return await container.identity_provider.authenticate(credentials.credentials)


CurrentIdentity = Annotated[Identity, Depends(get_current_identity)]
