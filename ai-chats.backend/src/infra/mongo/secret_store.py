import os
from datetime import UTC, datetime
from uuid import UUID, uuid7

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from ddf.application.exceptions import NotFoundError
from pydantic import SecretStr
from pymongo.asynchronous.collection import AsyncCollection

from .models import SecretModel

FORMAT_VERSION = 1  # AES-256-GCM, 96-битный nonce, id секрета в AAD
NONCE_SIZE = 12


class MongoSecretStore:
    """Хранит секреты зашифрованными master ключом.

    ID секрета передаётся как associated data, поэтому шифротекст
    нельзя подменить документом другого секрета.
    """

    def __init__(self, collection: AsyncCollection, *, master_key: bytes, key_version: int = 1) -> None:
        self._collection = collection
        self._cipher = AESGCM(master_key)
        self._key_version = key_version

    async def create(self, secret: SecretStr) -> UUID:
        model = self._encrypt(uuid7(), secret)
        await self._collection.insert_one(model.model_dump(by_alias=True))
        return model.id

    async def get(self, secret_id: UUID) -> SecretStr:
        if (document := await self._collection.find_one({"_id": secret_id})) is None:
            raise NotFoundError(f"Secret {secret_id} not found.")

        model = SecretModel.model_validate(document)

        if model.key_version != self._key_version or model.format_version != FORMAT_VERSION:
            raise RuntimeError(f"Secret {secret_id} is encrypted with unsupported key or format version.")

        plaintext = self._cipher.decrypt(model.nonce, model.ciphertext, secret_id.bytes)
        return SecretStr(plaintext.decode())

    async def replace(self, secret_id: UUID, secret: SecretStr) -> None:
        model = self._encrypt(secret_id, secret)
        changes = model.model_dump(
            by_alias=True, include={"ciphertext", "nonce", "key_version", "format_version"}
        )

        result = await self._collection.update_one(
            {"_id": secret_id},
            {"$set": {**changes, "updatedAt": datetime.now(UTC)}},
        )

        if result.matched_count == 0:
            raise NotFoundError(f"Secret {secret_id} not found.")

    async def delete(self, secret_id: UUID) -> None:
        await self._collection.delete_one({"_id": secret_id})

    def _encrypt(self, secret_id: UUID, secret: SecretStr) -> SecretModel:
        nonce = os.urandom(NONCE_SIZE)
        ciphertext = self._cipher.encrypt(nonce, secret.get_secret_value().encode(), secret_id.bytes)

        return SecretModel(
            id=secret_id,
            ciphertext=ciphertext,
            nonce=nonce,
            key_version=self._key_version,
            format_version=FORMAT_VERSION,
        )
