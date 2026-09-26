import hashlib
from http import HTTPStatus
from uuid import UUID

import aiohttp
from ddf.application.cache import Cache
from ddf.domain.vo.email import Email
from pydantic import BaseModel

from src.application.auth import Identity, IdentityType, UnauthorizedError


class _UserInfo(BaseModel):
    id: UUID
    email: str
    roles: frozenset[str]


class DioDeskIdentityProvider:
    """Аутентификация через легаси IAM DIO desk (``GET /api/v1/auth/userinfo``).

    Легаси токен не содержит организацию, поэтому все пользователи
    относятся к организации по умолчанию.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        *,
        base_url: str,
        default_organization_id: UUID,
        cache: Cache[Identity],
        cache_ttl: int,
    ) -> None:
        self._session = session
        self._userinfo_url = f"{base_url.rstrip('/')}/api/v1/auth/userinfo"
        self._default_organization_id = default_organization_id
        self._cache = cache
        self._cache_ttl = cache_ttl

    async def authenticate(self, token: str) -> Identity:
        cache_key = f"iam:identity:{hashlib.sha256(token.encode()).hexdigest()}"

        if (identity := await self._cache.get(cache_key)) is not None:
            return identity

        identity = await self._fetch_identity(token)
        await self._cache.set(cache_key, identity, ttl=self._cache_ttl)

        return identity

    async def _fetch_identity(self, token: str) -> Identity:
        headers = {"Authorization": f"Bearer {token}"}

        async with self._session.get(self._userinfo_url, headers=headers) as response:
            if response.status == HTTPStatus.UNAUTHORIZED:
                raise UnauthorizedError("Invalid or expired access token.")

            response.raise_for_status()
            userinfo = _UserInfo.model_validate(await response.json())

        return Identity(
            id=userinfo.id,
            type=IdentityType.USER,
            organization_id=self._default_organization_id,
            email=Email(userinfo.email),
            roles=userinfo.roles,
        )
