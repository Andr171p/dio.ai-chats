from collections.abc import AsyncIterator, Sequence

import openai
from openai import AsyncOpenAI, omit

from src.application.dtos.events import ModelEvent
from src.application.dtos.inputs import ModelInput
from src.application.dtos.tools import ModelTool
from src.application.genai.exceptions import ModelStreamFailedError
from src.domain.connections.vo import ModelProtocol
from src.infra.services.media import MediaClient

from .responses_builders import build_model_event, build_openai_input, build_openai_tools


class OpenAIResponsesAdapter:
    def __init__(self, openai_client: AsyncOpenAI, media_client: MediaClient) -> None:
        self._openai_client = openai_client
        self._media_client = media_client

    @property
    def protocol(self) -> ModelProtocol:
        return ModelProtocol.OPENAI_RESPONSES

    async def stream(
        self,
        model_id: str,
        inputs: Sequence[ModelInput],
        tools: Sequence[ModelTool] | None = None,
    ) -> AsyncIterator[ModelEvent]:
        openai_input = await build_openai_input(inputs, media_client=self._media_client)
        openai_tools = build_openai_tools(tools or ())

        try:
            stream = await self._openai_client.responses.create(
                model=model_id,
                input=openai_input,
                tools=openai_tools or omit,
                stream=True,
                store=False,
            )

            async with stream:
                async for event in stream:
                    if model_event := build_model_event(event):
                        yield model_event

        except openai.APIError as error:
            raise ModelStreamFailedError(error.message) from error
