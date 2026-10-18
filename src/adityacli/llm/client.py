from collections.abc import Callable

from openai import OpenAI, DefaultHttpxClient, _base_client
from openai import OpenAIError, APIStatusError
from openai.types.chat import ChatCompletionMessageParam
from adityacli.config import LMStudioConfig
from adityacli.exceptions import (
    LLMConnectionError,
    LLMError,
)
from adityacli.core.models import (
    LLMResponse,
    Message,
)
from typing import cast
from time import perf_counter
import threading
from adityacli.llm.models import AvailableModel
from adityacli.core.operations import Operation, current_operation, check_operation
from adityacli.exceptions import FileTooLargeError, OperationCancelled, OperationTimeout
from contextvars import ContextVar

# Use the HTTP implementation bundled with the installed SDK. It can differ
# from a separately installed httpx package.
_http = getattr(_base_client, "httpx", None) or _base_client.httpx2
_wire_limit: ContextVar[int | None] = ContextVar("adityacli_wire_limit", default=None)


class _BoundedStream(_http.SyncByteStream):
    def __init__(self, stream, limit: int, operation: Operation | None):
        self.stream, self.limit, self.operation = stream, limit, operation

    def __iter__(self):
        size = 0
        try:
            for chunk in self.stream:
                if self.operation:
                    self.operation.check()
                size += len(chunk)
                if size > self.limit:
                    raise FileTooLargeError("HTTP response exceeds the transport byte limit.")
                yield chunk
        finally:
            self.close()

    def close(self):
        self.stream.close()

class LLMClient:
    """LM Studio client."""

    def __init__(self, config: LMStudioConfig) -> None:
        self._config = config
        self._transport_lock = threading.Lock()
        self._client: OpenAI = self._new_api()

        self._model: str = config.model
        # Native catalog endpoints live beside /v1, not underneath it.
        self._server_url = config.base_url.rstrip("/").removesuffix("/v1")
        self._models: list[AvailableModel] = []

    def _new_api(self) -> OpenAI:
        config = self._config
        return OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=0,
            default_headers={"Accept-Encoding": "identity"},
            http_client=DefaultHttpxClient(event_hooks={"response": [self._guard_response]}),
        )

    def _guard_response(self, response) -> None:
        # Reject compression rather than allowing a small wire body to expand
        # without a bound inside the HTTP decoder.
        limit = _wire_limit.get() or max(65536, 8 * self._config.max_response_bytes)
        if response.headers.get("content-encoding", "identity").lower() not in {"", "identity"}:
            response.close()
            raise LLMError("Compressed LM Studio responses are unsupported; use identity encoding.")
        try:
            declared = int(response.headers.get("content-length", "0"))
        except ValueError:
            declared = 0
        if declared > limit:
            response.close()
            raise FileTooLargeError("HTTP response exceeds the transport byte limit.")
        response.stream = _BoundedStream(response.stream, limit, current_operation())

    @property
    def model(self) -> str:
        return self._model

    @property
    def selected_model(self) -> AvailableModel | None:
        return next((model for model in self._models if model.id == self._model), None)

    @property
    def context_window(self) -> int | None:
        model = self.selected_model
        return model.context_window if model else None

    def select_model(self, model_id: str) -> None:
        """Select the request target without loading or configuring a model."""
        if not any(model.id == model_id for model in self._models):
            raise LLMError(f"Model '{model_id}' is not available in LM Studio. Refresh models.")
        self._model = model_id

    def close(self) -> None:
        self._client.close()

    def list_models(self) -> list[AvailableModel]:
        """Prefer the downloaded-model catalog, with older-server fallbacks."""
        operation = Operation(5.0, parent=current_operation())
        models = self._run_request(self._list_models, operation)
        operation.check()
        self._models = models
        return list(models)

    def _list_models(self, api) -> list[AvailableModel]:
        try:
            api = api.with_options(timeout=5.0, max_retries=0)
            for version in ("v1", "v0"):
                try:
                    payload = api.get(
                        f"{self._server_url}/api/{version}/models",
                        cast_to=dict,
                    )
                except APIStatusError as exc:
                    if exc.status_code in (404, 405):
                        continue
                    raise
                models = self._parse_catalog(payload, version)
                break
            else:
                # Older OpenAI-only servers may expose loaded models only.
                models = [
                    AvailableModel(id=item.id, name=item.id)
                    for item in api.models.list().data
                    if getattr(item, "type", None) not in ("embedding", "embeddings")
                ]
        except OpenAIError as exc:
            raise LLMConnectionError(f"Unable to list LM Studio models: {exc}") from exc

        return sorted(models, key=lambda model: (not model.loaded, model.name.lower(), model.id))

    @staticmethod
    def _parse_catalog(payload: dict, version: str) -> list[AvailableModel]:
        models: list[AvailableModel] = []
        for item in payload.get("models" if version == "v1" else "data", []):
            if item.get("type") not in ("llm", "vlm"):
                continue
            model_id = item.get("key" if version == "v1" else "id")
            if not model_id:
                continue
            name = item.get("display_name") or model_id
            quantization = item.get("quantization")
            if isinstance(quantization, dict):
                quantization = quantization.get("name")
            instances = item.get("loaded_instances", []) if version == "v1" else []
            if instances:
                for instance in instances:
                    context = instance.get("config", {}).get("context_length")
                    models.append(AvailableModel(
                        id=instance["id"],
                        name=f"{name} · {instance['id']}" if len(instances) > 1 else name,
                        loaded=True,
                        context_window=context if isinstance(context, int) and context > 0 else None,
                        quantization=quantization,
                    ))
            else:
                loaded = item.get("state") == "loaded"
                # max_context_length describes model capacity, not the
                # context configured in LM Studio. Never use it as such.
                context = item.get("loaded_context_length") if loaded else None
                models.append(AvailableModel(
                    id=model_id, name=name, loaded=loaded,
                    context_window=context if isinstance(context, int) and context > 0 else None,
                    quantization=quantization,
                ))
        return models

    def generate(
        self, messages: list[Message], *, max_tokens: int | None = None,
        stop: list[str] | None = None, temperature: float | None = None,
        on_chunk: Callable[[str], None] | None = None, max_response_bytes: int | None = None,
    ) -> LLMResponse:
        operation = current_operation() or Operation(self._config.timeout)
        limit = min(max_response_bytes or self._config.max_response_bytes, self._config.max_response_bytes)

        def request(api):
            token = _wire_limit.set(max(65536, 8 * limit))
            try:
                return self._generate(messages, max_tokens=max_tokens, stop=stop, temperature=temperature,
                                      on_chunk=on_chunk, max_response_bytes=limit, api=api)
            finally:
                _wire_limit.reset(token)

        return self._run_request(request, operation)

    def _run_request(self, function, operation: Operation):
        if not self._transport_lock.acquire(blocking=False):
            raise LLMError("The previous inference connection is still closing. Retry after it closes.")
        api = self._client

        def request():
            try:
                with operation.activate():
                    return function(api)
            finally:
                self._transport_lock.release()

        try:
            return operation.run_io(request, interrupt=api.close)
        except (OperationCancelled, OperationTimeout):
            # Replace the pool before returning control; closing a blocked
            # connection happens in a daemon and cannot reset a newer pool.
            if self._client is api:
                self._client = self._new_api()
            raise

    def _generate(
        self,
        messages: list[Message],
        *,
        max_tokens: int | None = None,
        stop: list[str] | None = None,
        temperature: float | None = None,
        on_chunk: Callable[[str], None] | None = None,
        max_response_bytes: int | None = None,
        api=None,
    ) -> LLMResponse:
        """
        Generate a response, optionally delivering text deltas as they arrive.
        """
        # LLMService refreshes the catalog before constructing the prompt.
        # No load/unload requests or load-time parameters are sent here.
        if not self._model:
            raise LLMError("Select a model before sending a message.")
        api = api or self._client
        limit = min(max_response_bytes or self._config.max_response_bytes, self._config.max_response_bytes)

        try:
            payload = cast(
                list[ChatCompletionMessageParam],
                [
                    {
                        "role": message.role.value,
                        "content": message.content,
                    }
                    for message in messages
                ],
            )

            start = perf_counter()
            options = {}
            operation = current_operation()
            if operation:
                options["timeout"] = min(self._config.timeout, operation.remaining)
            if max_tokens is not None:
                options["max_tokens"] = max_tokens
            if stop is not None:
                options["stop"] = stop
            if temperature is not None:
                options["temperature"] = temperature
            if on_chunk is None:
                response = api.chat.completions.create(
                    model=self._model, messages=payload, **options,
                )
                if not response.choices:
                    raise LLMError("LM Studio returned no completion choices.")
                choice = response.choices[0]
                content = choice.message.content or ""
                if len(content.encode("utf-8")) > limit:
                    raise FileTooLargeError("Model response exceeds the output byte limit.")
                finish_reason = choice.finish_reason
                model = response.model
                usage = response.usage
            else:
                parts: list[str] = []
                finish_reason = None
                model = self._model
                usage = None
                size = 0
                with api.chat.completions.create(
                    model=self._model, messages=payload, stream=True,
                    stream_options={"include_usage": True}, **options,
                ) as stream:
                    for chunk in stream:
                        check_operation()
                        model = chunk.model or model
                        if chunk.usage is not None:
                            usage = chunk.usage
                        if not chunk.choices:
                            continue  # The final usage event has no choices.
                        choice = chunk.choices[0]
                        if choice.delta.content:
                            size += len(choice.delta.content.encode("utf-8"))
                            if size > limit:
                                raise FileTooLargeError("Model response exceeds the output byte limit.")
                            parts.append(choice.delta.content)
                            on_chunk(choice.delta.content)
                        if choice.finish_reason is not None:
                            finish_reason = choice.finish_reason
                if finish_reason is None:
                    raise LLMConnectionError(
                        "LM Studio's response stream ended before completion. Retry the request."
                    )
                content = "".join(parts)

            elapsed = perf_counter() - start
            check_operation()
        except OpenAIError as exc:
            raise LLMConnectionError(str(exc)) from exc
        except (LLMError, FileTooLargeError, OperationCancelled, OperationTimeout):
            raise
        except Exception as exc:
            raise LLMError(str(exc)) from exc

        if not content.strip() and finish_reason != "length":
            raise LLMError("LM Studio returned an empty text response. Try another request or model.")
        if finish_reason not in {"stop", "length", None}:
            raise LLMError(f"LM Studio returned unsupported completion status: {finish_reason}.")

        return LLMResponse(
            content=content,
            model=model,
            prompt_tokens=(
                usage.prompt_tokens if usage else 0
            ),
            completion_tokens=(
                usage.completion_tokens if usage else 0
            ),
            total_tokens=(
                usage.total_tokens if usage else 0
            ),
            elapsed_seconds=elapsed,
            finish_reason=finish_reason or "stop",
        )

    def health_check(self) -> None:
        """
        Verify that LM Studio is reachable and the configured model exists.
        """

        available = self.list_models()
        if not self._model and available:
            self._model = available[0].id
        if not self._model or not any(model.id == self._model for model in available):
            raise LLMError(
                "Selected model is unavailable. Refresh models and select a model "
                "downloaded in LM Studio. Enable Just-In-Time loading there for unloaded models."
            )
