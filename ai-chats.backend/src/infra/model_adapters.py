from collections.abc import Awaitable, Callable
from uuid import UUID

from openai import AsyncOpenAI, DefaultAsyncHttpxClient

from src.application.genai.exceptions import EdgeExecutionNotConfiguredError, ModelProtocolNotSupportedError
from src.application.genai.model_adapter import ModelAdapter
from src.application.secrets.secret_store import SecretStore
from src.domain.connections.models import ModelConnection
from src.domain.connections.vo import ModelProtocol, ServerModelRoute

from .openai import OpenAIResponsesAdapter
from .services.media import MediaClient


class ServerModelAdapterResolver:
    """Адаптеры моделей, которые вызываются с сервера.

    Все клиенты провайдеров используют общий HTTP пул, а API ключ
    читается из хранилища секретов на каждый запрос к модели.
    """

    def __init__(
        self,
        *,
        secret_store: SecretStore,
        http_client: DefaultAsyncHttpxClient,
        media_client: MediaClient,
    ) -> None:
        self._secret_store = secret_store
        self._http_client = http_client
        self._media_client = media_client

    def __call__(self, connection: ModelConnection) -> ModelAdapter:
        route = connection.route

        if not isinstance(route, ServerModelRoute):
            raise EdgeExecutionNotConfiguredError("Edge model execution is not configured yet.")

        match connection.protocol:
            case ModelProtocol.OPENAI_RESPONSES:
                client = AsyncOpenAI(
                    base_url=route.base_url,
                    api_key=self._api_key(route.credential_id),
                    http_client=self._http_client,
                )
                return OpenAIResponsesAdapter(client, self._media_client)

        raise ModelProtocolNotSupportedError(f"Model protocol {connection.protocol!r} is not supported yet.")

    def _api_key(self, credential_id: UUID | None) -> str | Callable[[], Awaitable[str]]:
        # Пустой ключ: без заголовка Authorization и без подстановки OPENAI_API_KEY из окружения
        if credential_id is None:
            return ""

        async def read_api_key() -> str:
            secret = await self._secret_store.get(credential_id)
            return secret.get_secret_value()

        return read_api_key
