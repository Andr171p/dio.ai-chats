from typing import Annotated

from functools import cache
from uuid import UUID

from ddf.infra.database.mongo import MongoConfig
from dotenv import load_dotenv
from pydantic import BaseModel, Field, HttpUrl, PositiveInt, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Doc


class IamSettings(BaseSettings):
    """IAM DIO desk (легаси контракт)."""

    model_config = SettingsConfigDict(env_prefix="IAM_")

    base_url: HttpUrl
    default_organization_id: Annotated[
        UUID,
        Doc("Легаси IAM не выдаёт организацию, пока все пользователи относятся к одной"),
    ]
    identity_cache_ttl: PositiveInt = 60


class SecretsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SECRETS_")

    master_key: Annotated[SecretStr, Doc("Base64 от 32 байт ключа AES-256-GCM")]


class Settings(BaseModel):
    mongo: MongoConfig = Field(default_factory=MongoConfig)
    iam: IamSettings = Field(default_factory=IamSettings)  # type: ignore[arg-type]
    secrets: SecretsSettings = Field(default_factory=SecretsSettings)  # type: ignore[arg-type]


@cache
def get_settings() -> Settings:
    load_dotenv()
    return Settings()
