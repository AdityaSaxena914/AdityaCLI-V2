from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai import APIStatusError

from adityacli.config import LMStudioConfig
from adityacli.core.models import Message, Role
from adityacli.exceptions import LLMError
from adityacli.llm.client import LLMClient
from adityacli.core.prompt_builder import PromptBuilder
from adityacli.core.session import Session
from adityacli.core.session_store import SessionStore
from adityacli.config import AppConfig, SecurityConfig, WorkspaceConfig
from adityacli.services.llm_service import LLMService
from openai import OpenAI, _base_client


@pytest.fixture
def client():
    client = LLMClient(LMStudioConfig())
    client.close()
    client._client = Mock()
    client._client.with_options.return_value = client._client
    return client


def catalog():
    return {"models": [
        {"type": "llm", "key": "downloaded-model", "display_name": "Downloaded",
         "max_context_length": 131072, "loaded_instances": [], "quantization": {"name": "Q8_0"}},
        {"type": "llm", "key": "loaded-model", "display_name": "Loaded",
         "max_context_length": 32768, "loaded_instances": [
             {"id": "custom-instance", "config": {"context_length": 4096}}]},
        {"type": "embedding", "key": "embedding", "loaded_instances": []},
    ]}


def test_discovery_includes_downloaded_models_and_reads_actual_context(client):
    client._client.get.return_value = catalog()
    models = client.list_models()
    assert [model.id for model in models] == ["custom-instance", "downloaded-model"]
    assert models[0].context_window == 4096
    assert models[1].context_window is None
    assert models[1].quantization == "Q8_0"
    client._client.get.assert_called_once_with("http://127.0.0.1:1234/api/v1/models", cast_to=dict)


def test_selection_controls_request_model_without_load_settings(client):
    client._client.get.return_value = catalog()
    client.list_models()
    client.select_model("downloaded-model")
    client._client.chat.completions.create.return_value = SimpleNamespace(
        model="downloaded-model", usage=None,
        choices=[SimpleNamespace(message=SimpleNamespace(content="reply"), finish_reason="stop")],
    )
    response = client.generate([Message(Role.USER, "hello")])
    request = client._client.chat.completions.create.call_args.kwargs
    assert request["model"] == "downloaded-model"
    assert "max_tokens" not in request
    assert response.content == "reply"
    assert not {"context_length", "gpu_offload", "quantization"}.intersection(request)
    assert not client._client.post.called
    with pytest.raises(LLMError):
        client.select_model("missing")


def unavailable():
    return APIStatusError("Not found", response=Mock(status_code=404), body=None)


def test_older_native_api_fallback(client):
    client._client.get.side_effect = [unavailable(), {"data": [
        {"id": "older-model", "type": "vlm", "state": "loaded", "max_context_length": 32768},
        {"id": "embedding", "type": "embeddings"},
    ]}]
    models = client.list_models()
    assert len(models) == 1
    assert models[0].id == "older-model"
    assert models[0].loaded
    assert models[0].context_window is None


def test_openai_only_fallback(client):
    client._client.get.side_effect = [unavailable(), unavailable()]
    client._client.models.list.return_value = SimpleNamespace(data=[SimpleNamespace(id="legacy-model")])
    assert client.list_models()[0].id == "legacy-model"


def test_authentication_failure_does_not_silently_fall_back(client):
    client._client.get.side_effect = APIStatusError("Unauthorized", response=Mock(status_code=401), body=None)
    with pytest.raises(LLMError, match="Unauthorized"):
        client.list_models()
    assert client._client.get.call_count == 1
    assert not client._client.models.list.called


def test_budget_follows_server_context_when_switching_models(client, tmp_path):
    payload = catalog()
    payload["models"][0]["loaded_instances"] = [
        {"id": "downloaded-model", "config": {"context_length": 8192}},
    ]
    client._client.get.return_value = payload
    client.list_models()
    config = AppConfig(WorkspaceConfig(tmp_path), LMStudioConfig(), SecurityConfig())
    store = SessionStore(tmp_path)
    store.create("", 15000)
    session = Session(store)
    session.add_system("system")
    session.add_user("hello")
    service = LLMService(client, PromptBuilder(), config)
    client.generate = Mock(return_value=SimpleNamespace(content="reply", finish_reason="stop"))
    client.select_model("custom-instance")
    service.generate(session=session, tool_result=None)
    small_budget = client.generate.call_args.kwargs["max_tokens"]
    client.select_model("downloaded-model")
    session.add_user("hello again")
    service.generate(session=session, tool_result=None)
    large_budget = client.generate.call_args.kwargs["max_tokens"]
    assert 0 < small_budget < 4096
    assert small_budget < large_budget < 8192
    assert not client._client.post.called


def test_small_selected_context_does_not_discard_current_request(client, tmp_path):
    client._client.get.return_value = catalog()
    client.list_models()
    client.select_model("custom-instance")
    config = AppConfig(WorkspaceConfig(tmp_path), LMStudioConfig(), SecurityConfig())
    store = SessionStore(tmp_path)
    store.create("", 15000)
    session = Session(store, max_read_tokens=16000)
    session.add_system("system")
    session.add_user("Explain this")
    session.remember_file("large.py", "x" * 20000)
    service = LLMService(client, PromptBuilder(), config)
    with pytest.raises(LLMError, match="do not fit"):
        service.generate(session=session, tool_result=None)
    assert not client._client.chat.completions.create.called


def test_real_sdk_routes_catalog_and_chat_without_model_configuration():
    # Exercise SDK URL construction/serialization without a running server.
    http = getattr(_base_client, "httpx", None) or _base_client.httpx2
    requests = []

    def respond(request):
        import json
        requests.append(request)
        if request.url.path == "/api/v1/models":
            return http.Response(200, json=catalog())
        if request.url.path == "/v1/chat/completions":
            body = json.loads(request.content)
            assert body["model"] == "downloaded-model"
            assert "max_tokens" not in body
            assert not {"context_length", "gpu_offload", "quantization"}.intersection(body)
            return http.Response(200, json={
                "id": "test", "object": "chat.completion", "created": 0,
                "model": "downloaded-model",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "reply"}, "finish_reason": "stop"}],
            })
        raise AssertionError(f"Unexpected endpoint: {request.url}")

    client = LLMClient(LMStudioConfig())
    client.close()
    client._client = OpenAI(
        base_url="http://127.0.0.1:1234/v1", api_key="test", max_retries=0,
        http_client=http.Client(transport=http.MockTransport(respond)),
    )
    try:
        client.list_models()
        client.select_model("downloaded-model")
        assert client.generate([Message(Role.USER, "hello")]).content == "reply"
        assert [request.method for request in requests] == ["GET", "POST"]
    finally:
        client.close()
