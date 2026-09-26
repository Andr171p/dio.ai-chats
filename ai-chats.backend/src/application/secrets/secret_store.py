from typing import Protocol

from uuid import UUID

from pydantic import SecretStr


class SecretStore(Protocol):
    """Абстракция для безопасного менеджера секретов."""

    async def create(self, secret: SecretStr) -> UUID: ...

    async def get(self, secret_id: UUID) -> SecretStr: ...

    async def replace(self, secret_id: UUID, secret: SecretStr) -> None: ...

    async def delete(self, secret_id: UUID) -> None: ...
