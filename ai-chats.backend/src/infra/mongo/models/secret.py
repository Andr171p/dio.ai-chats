from typing import ClassVar

from ddf.infra.database.mongo import MongoBaseModel, MongoEntityMixin
from pydantic import Field, PositiveInt


class SecretModel(MongoBaseModel, MongoEntityMixin):
    __collection_name__: ClassVar[str] = "secrets"

    ciphertext: bytes = Field(description="Зашифрованные данные")
    nonce: bytes

    key_version: PositiveInt = Field(description="Версия Master ключа, которым был зашифрован секрет")
    format_version: PositiveInt = Field(description="Версия способа шифрования")
