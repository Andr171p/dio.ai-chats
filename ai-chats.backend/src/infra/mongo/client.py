from typing import Any

from decimal import Decimal

from bson.codec_options import TypeCodec, TypeRegistry
from bson.decimal128 import Decimal128
from ddf.infra.database.mongo import MongoConfig
from pymongo import AsyncMongoClient


class DecimalCodec(TypeCodec):
    """Хранит ``Decimal`` без потери точности (цены моделей)."""

    python_type = Decimal
    bson_type = Decimal128

    def transform_python(self, value: Decimal) -> Decimal128:
        return Decimal128(value)

    def transform_bson(self, value: Decimal128) -> Decimal:
        return value.to_decimal()


def _encode_unknown(value: Any) -> Any:
    """Множества из доменных VO (модальности, capabilities) хранятся массивами."""

    if isinstance(value, (set, frozenset)):
        return list(value)

    return value


def create_mongo_client(config: MongoConfig) -> AsyncMongoClient:
    return AsyncMongoClient(
        config.uri,
        uuidRepresentation="standard",
        tz_aware=True,
        type_registry=TypeRegistry([DecimalCodec()], fallback_encoder=_encode_unknown),
    )
