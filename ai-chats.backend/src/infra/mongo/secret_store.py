from uuid import UUID

from pymongo.asynchronous.collection import AsyncCollection


class MongoSecretStore:
    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def create(self, value: str) -> UUID:
        ...
