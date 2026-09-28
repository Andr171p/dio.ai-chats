"""Composition root: собирает инфраструктуру и связывает её с application слоем."""

import base64
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import aiohttp
from ddf.application.repositories import Repository
from ddf.infra.cache.in_memory import InMemoryCache
from ddf.infra.database.mongo import initialize_mongo_models
from fastapi import FastAPI
from openai import DefaultAsyncHttpxClient, Timeout
from pymongo.asynchronous.database import AsyncDatabase

from src.application.auth import Identity, IdentityProvider
from src.application.runtime import ChatRuntime
from src.application.secrets.secret_store import SecretStore
from src.domain.connections.models import ModelConnection
from src.domain.conversations import Conversation, Message, Thread
from src.domain.runs import Run
from src.infra.model_adapters import ServerModelAdapterResolver
from src.infra.mongo.client import create_mongo_client
from src.infra.mongo.models import (
    MONGO_MODELS,
    ConversationModel,
    MessageModel,
    ModelConnectionModel,
    RunModel,
    SecretModel,
    ThreadModel,
)
from src.infra.mongo.repositories import (
    MongoConversationRepository,
    MongoMessageRepository,
    MongoModelConnectionRepository,
    MongoRunRepository,
    MongoThreadRepository,
)
from src.infra.mongo.secret_store import MongoSecretStore
from src.infra.services.iam import DioDeskIdentityProvider
from src.infra.services.media import MediaClient
from src.settings import Settings, get_settings

# Reasoning модели могут долго молчать перед первым токеном
MODEL_HTTP_TIMEOUT = Timeout(300, connect=10)


@dataclass(frozen=True, slots=True)
class Container:
    identity_provider: IdentityProvider
    secret_store: SecretStore
    connections: Repository[ModelConnection]
    conversations: Repository[Conversation]
    threads: Repository[Thread]
    messages: Repository[Message]
    runs: Repository[Run]
    chat_runtime: ChatRuntime


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    identity_cache = InMemoryCache[Identity]()

    async with (
        create_mongo_client(settings.mongo) as mongo_client,
        aiohttp.ClientSession() as iam_session,
        DefaultAsyncHttpxClient(timeout=MODEL_HTTP_TIMEOUT) as model_http_client,
    ):
        database = mongo_client.get_database(settings.mongo.db)
        await initialize_mongo_models(database, MONGO_MODELS)

        identity_provider = DioDeskIdentityProvider(
            iam_session,
            base_url=str(settings.iam.base_url),
            default_organization_id=settings.iam.default_organization_id,
            cache=identity_cache,
            cache_ttl=settings.iam.identity_cache_ttl,
        )
        app.state.container = _build_container(database, settings, identity_provider, model_http_client)

        identity_cache.start()
        try:
            yield
        finally:
            await identity_cache.close()


def _build_container(
    database: AsyncDatabase,
    settings: Settings,
    identity_provider: IdentityProvider,
    model_http_client: DefaultAsyncHttpxClient,
) -> Container:
    secret_store = MongoSecretStore(
        database.get_collection(SecretModel.__collection_name__),
        master_key=base64.b64decode(settings.secrets.master_key.get_secret_value()),
    )
    connections = MongoModelConnectionRepository(
        database.get_collection(ModelConnectionModel.__collection_name__)
    )
    conversations = MongoConversationRepository(
        database.get_collection(ConversationModel.__collection_name__)
    )
    threads = MongoThreadRepository(database.get_collection(ThreadModel.__collection_name__))
    messages = MongoMessageRepository(database.get_collection(MessageModel.__collection_name__))
    runs = MongoRunRepository(database.get_collection(RunModel.__collection_name__))

    resolve_adapter = ServerModelAdapterResolver(
        secret_store=secret_store,
        http_client=model_http_client,
        media_client=MediaClient(),
    )

    return Container(
        identity_provider=identity_provider,
        secret_store=secret_store,
        connections=connections,
        conversations=conversations,
        threads=threads,
        messages=messages,
        runs=runs,
        chat_runtime=ChatRuntime(
            conversations=conversations,
            threads=threads,
            messages=messages,
            runs=runs,
            connections=connections,
            resolve_adapter=resolve_adapter,
        ),
    )
