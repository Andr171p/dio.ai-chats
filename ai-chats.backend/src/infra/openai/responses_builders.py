from typing import cast

import base64
import json
from collections.abc import Buffer, Sequence

from openai.types.responses import FunctionToolParam, ResponseInputItemParam, ResponseStreamEvent
from pydantic import JsonValue

from src.application.dtos.events import ModelCompleted, ModelEvent, ModelTextDelta, ModelToolCall
from src.application.dtos.inputs import (
    AttachmentContent,
    InstructionsInput,
    JsonContent,
    MessageContent,
    MessageInput,
    ModelInput,
    TextContent,
    ToolCallInput,
    ToolResultInput,
)
from src.application.dtos.tools import ModelTool
from src.application.genai.exceptions import ModelStreamFailedError
from src.domain.connections.vo import Usage
from src.domain.runs.vo import FinishReason
from src.infra.services.media import MediaClient, download_file_from_url


def _encode_base64(raw_bytes: Buffer, content_type: str) -> str:
    encoded = base64.b64encode(raw_bytes).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


async def _build_openai_attachment(
    content: AttachmentContent,
    *,
    media_client: MediaClient,
) -> dict[str, object]:
    url = await media_client.get_download_url(content.attachment_id)
    raw_bytes = await download_file_from_url(url)
    content_type = content.content_type

    file_url = _encode_base64(raw_bytes, content_type)

    if content_type.startswith("image/"):
        return {
            "type": "input_image",
            "image_url": file_url,
            "detail": "auto",
        }

    if content_type.startswith(("audio/", "video/")):
        raise ValueError(f"OpenAI Responses does not support {content_type!r} as this input type.")

    if content.filename is None:
        raise ValueError("Filename is required for OpenAI file input.")

    return {
        "type": "input_file",
        "filename": content.filename,
        "file_data": file_url,
    }


async def _build_openai_content(
    content: Sequence[MessageContent],
    *,
    media_client: MediaClient,
) -> list[dict[str, object]]:
    """"""

    result: list[dict[str, object]] = []

    for c in content:
        match c:
            case TextContent():
                result.append({"type": "input_text", "text": c.text})

            case JsonContent():
                result.append(
                    {
                        "type": "input_text",
                        "text": json.dumps(c.value, ensure_ascii=False, separators=(",", ":")),
                    }
                )

            case AttachmentContent():
                file = await _build_openai_attachment(c, media_client=media_client)
                result.append(file)

    return result


async def build_openai_input(
    inputs: Sequence[ModelInput],
    *,
    media_client: MediaClient,
) -> list[ResponseInputItemParam]:
    result: list[ResponseInputItemParam] = []

    for input_ in inputs:
        match input_:
            case InstructionsInput():
                result.append(
                    {
                        "type": "message",
                        "role": "developer",
                        "content": input_.text,
                    }
                )

            case MessageInput(role="assistant"):
                # История ассистента принимается только как output_text, строка - самый совместимый вариант
                result.append(
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": "".join(c.text for c in input_.content if isinstance(c, TextContent)),
                    }
                )

            case MessageInput():
                content = await _build_openai_content(input_.content, media_client=media_client)

                result.append(
                    {
                        "type": "message",
                        "role": input_.role,
                        "content": content,
                    }
                )

            case ToolCallInput():
                result.append(
                    {
                        "type": "function_call",
                        "call_id": input_.call_id,
                        "name": input_.name,
                        "arguments": json.dumps(
                            input_.arguments,
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                    }
                )

            case ToolResultInput():
                output = await _build_openai_content(input_.content, media_client=media_client)

                if input_.is_error:
                    output.insert(
                        0,
                        {
                            "type": "input_text",
                            "text": "Tool execution failed.",
                        },
                    )

                result.append(
                    {
                        "type": "function_call_output",
                        "call_id": input_.call_id,
                        "output": output,
                    }
                )

    return result


def build_openai_tools(tools: Sequence[ModelTool],) -> list[FunctionToolParam]:
    return [
        {
            "type": "function",
            "name": tool.name,
            "description": tool.description,
            "parameters": cast(dict[str, object], tool.input_schema),
            "strict": False,
        }
        for tool in tools
    ]


def _build_usage(response_usage: object | None) -> Usage | None:
    if response_usage is None:
        return None

    input_details = getattr(response_usage, "input_tokens_details", None)
    output_details = getattr(response_usage, "output_tokens_details", None)

    return Usage(
        input_tokens=getattr(response_usage, "input_tokens", 0),
        output_tokens=getattr(response_usage, "output_tokens", 0),
        cached_input_tokens=(
            getattr(input_details, "cached_tokens", 0)
            if input_details is not None
            else 0
        ),
        cache_write_input_tokens=0,
        reasoning_tokens=(
            getattr(output_details, "reasoning_tokens", 0)
            if output_details is not None
            else 0
        ),
    )


def _get_finish_reason(response: object) -> FinishReason:
    output = getattr(response, "output", ())

    if any(getattr(o, "type", None) == "function_call" for o in output):
        return FinishReason.TOOL_CALLS

    status = getattr(response, "status", None)

    if status == "cancelled":
        return FinishReason.CANCELLED

    if status == "incomplete":
        details = getattr(response, "incomplete_details", None)
        reason = getattr(details, "reason", None)

        if reason in {"max_output_tokens", "max_messages"}:
            return FinishReason.LENGTH

        if reason == "content_filter":
            return FinishReason.CONTENT_FILTER

        return FinishReason.UNKNOWN

    return FinishReason.STOP


def _parse_tool_arguments(value: str) -> dict[str, JsonValue]:
    try:
        arguments = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError("Model returned invalid tool arguments.") from exc

    if not isinstance(arguments, dict):
        raise TypeError("Model tool arguments must be a JSON object.")

    return arguments


def build_model_event(event: ResponseStreamEvent) -> ModelEvent | None:
    match event.type:
        case "response.output_text.delta":
            return ModelTextDelta(delta=event.delta)

        case "response.output_item.done":
            item = event.item

            if item.type != "function_call":
                return None

            arguments = _parse_tool_arguments(item.arguments)

            return ModelToolCall(
                call_id=item.call_id,
                name=item.name,
                arguments=arguments,
            )

        case "response.completed":
            response = event.response

            return ModelCompleted(
                finish_reason=_get_finish_reason(response),
                usage=_build_usage(response.usage),
                provider_request_id=response.id,
            )

        case "response.incomplete":
            response = event.response

            return ModelCompleted(
                finish_reason=_get_finish_reason(response),
                usage=_build_usage(response.usage),
                provider_request_id=response.id,
            )

        case "response.failed":
            error = event.response.error

            if error is None:
                raise ValueError("OpenAI response failed")

            raise ModelStreamFailedError(f"{error.code}: {error.message}")

        case "error":
            code = f"{event.code}: " if event.code else ""
            raise ModelStreamFailedError(f"{code}{event.message}")

    return None
