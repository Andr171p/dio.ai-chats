from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import SecretStr

from src.application.auth import Identity, UnauthorizedError
from src.bootstrap import Container

_bearer = HTTPBearer(auto_error=False, description="Access токен DIO desk")


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_access_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> SecretStr:
    if credentials is None:
        raise UnauthorizedError("Authorization header is missing.")

    return SecretStr(credentials.credentials)


AccessToken = Annotated[SecretStr, Depends(get_access_token)]
"""Токен пользователя DIOS: с ним сервис обращается к MCP серверам экосистемы."""


async def get_current_identity(access_token: AccessToken, container: ContainerDep) -> Identity:
    return await container.identity_provider.authenticate(access_token.get_secret_value())


CurrentIdentity = Annotated[Identity, Depends(get_current_identity)]
