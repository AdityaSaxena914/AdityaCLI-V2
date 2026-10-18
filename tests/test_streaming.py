import asyncio
import json

import pytest
from openai import OpenAI, _base_client
from textual.containers import VerticalScroll
from textual.widgets import Button, Select

from adityacli.config import LMStudioConfig
from adityacli.core.models import Message, Role
from adityacli.exceptions import LLMConnectionError, LLMError, TruncatedResponseError
from adityacli.llm.client import LLMClient
from adityacli.ui.conversation import ConversationMessage
from adityacli.ui.screens import ConfirmationScreen, PromptInput
from tests.test_tui import FakeClient, make_app, wait_until

http = getattr(_base_client, "httpx", None) or _base_client.httpx2


def event(text=None, finish=None):
    return {
        "id": "test-stream", "object": "chat.completion.chunk", "created": 1,
        "model": "model-a", "choices": [{
            "index": 0, "delta": {"content": text} if text is not None else {},
            "finish_reason": finish,
        }],
    }


def stream_client(events, *, disconnect=False):
    class EventStream(http.SyncByteStream):
        closed = False

        def __iter__(self):
            for item in events:
                yield ("data: " + json.dumps(item) + "\n\n").encode()
            if disconnect:
                raise http.ReadError("connection lost")
            yield b"data: [DONE]\n\n"

        def close(self):
            self.closed = True

    stream = EventStream()
    requests = []

    def respond(request):
        if request.method == "GET":
            return http.Response(200, json={"models": [{
                "type": "llm", "key": "model-a", "display_name": "Model A",
                "loaded_instances": [{"id": "model-a", "config": {"context_length": 8192}}],
            }]})
        requests.append(json.loads(request.content))
        return http.Response(200, headers={"content-type": "text/event-stream"}, stream=stream)

    client = LLMClient(LMStudioConfig())
    client.close()
    client._client = OpenAI(
        api_key="test", base_url="http://test/v1", max_retries=0,
        http_client=http.Client(transport=http.MockTransport(respond)),
    )
    client.list_models()
    client.select_model("model-a")
    return client, stream, requests


def test_sdk_stream_delivers_deltas_and_preserves_final_usage():
    usage = event()
    usage.update(choices=[], usage={"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7})
    client, stream, requests = stream_client([
        event(), event("Hello "), event("world", "stop"), usage,
    ])
    chunks = []
    try:
        response = client.generate(
            [Message(Role.USER, "hello")], max_tokens=100, temperature=0.2,
            on_chunk=lambda text: chunks.append((text, stream.closed)),
        )
        assert chunks == [("Hello ", False), ("world", False)]
        assert response.content == "Hello world"
        assert response.finish_reason == "stop"
        assert (response.prompt_tokens, response.completion_tokens, response.total_tokens) == (3, 4, 7)
        assert response.elapsed_seconds > 0
        assert requests[0]["stream"] is True
        assert requests[0]["stream_options"] == {"include_usage": True}
        assert requests[0]["max_tokens"] == 100
        assert requests[0]["temperature"] == 0.2
        assert stream.closed
    finally:
        client.close()


def test_stream_without_usage_is_supported():
    client, stream, _ = stream_client([event("reply"), event(finish="stop")])
    try:
        response = client.generate([Message(Role.USER, "hello")], on_chunk=lambda text: None)
        assert response.content == "reply"
        assert response.total_tokens == 0
        assert stream.closed
    finally:
        client.close()


@pytest.mark.parametrize(("events", "disconnect", "error", "message"), [
    ([event("partial")], False, LLMConnectionError, "ended before completion"),
    ([event("partial")], True, LLMError, "(?i)connection"),
    ([event(finish="stop")], False, LLMError, "empty text response"),
    ([event("unexpected", "tool_calls")], False, LLMError, "unsupported completion status"),
])
def test_invalid_stream_is_closed_without_retry(events, disconnect, error, message):
    client, stream, requests = stream_client(events, disconnect=disconnect)
    try:
        with pytest.raises(error, match=message):
            client.generate([Message(Role.USER, "hello")], on_chunk=lambda text: None)
        assert stream.closed
        assert len(requests) == 1
    finally:
        client.close()


@pytest.mark.parametrize(("events", "error"), [
    ([event("partial")], LLMConnectionError),
    ([event("partial", "length")], TruncatedResponseError),
])
def test_incomplete_stream_is_never_archived(tmp_path, events, error):
    client, _, _ = stream_client(events)
    _, runtime, _ = make_app(tmp_path, client)
    runtime.select_model("model-a")
    chunks = []
    try:
        with pytest.raises(error):
            runtime.chat("Explain", on_chunk=chunks.append)
        assert chunks == ["partial"]
        assert runtime.last_response is None
        assert not any(message.role is Role.ASSISTANT for message in runtime.session.messages)
        _, continued, _ = make_app(tmp_path, client, continued=True)
        assert not any(message.role is Role.ASSISTANT for message in continued.session.messages)
    finally:
        client.close()


def test_analysis_stream_survives_ambiguous_file_selection(tmp_path):
    for folder in ("one", "two"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "source.py").write_text("value = 1")
    _, runtime, client = make_app(tmp_path)
    client.select_model("model-a")
    chunks = []
    pending = runtime.chat("/read source\nExplain this file", on_chunk=chunks.append)
    assert not chunks
    result = runtime.confirm_read_selection(pending, 0, on_chunk=chunks.append)
    assert "".join(chunks) == result.content == "reply"
    assert sum(message.role is Role.ASSISTANT for message in runtime.session.messages) == 1


def test_ui_displays_partial_reply_before_generation_finishes(tmp_path):
    async def scenario():
        app, runtime, client = make_app(tmp_path)
        client.output = "First chunk.\n\n**Final chunk.**"
        client.block = True
        async with app.run_test(size=(100, 35)) as pilot:
            await app.workers.wait_for_complete()
            app.query_one("#prompt", PromptInput).load_text("Explain")
            await pilot.press("enter")
            await wait_until(client.started.is_set)
            try:
                await pilot.pause()
                replies = [m for m in app.query(ConversationMessage) if m.title == "Assistant"]
                assert len(replies) == 1
                assert replies[0].text == client.output[:len(client.output) // 2]
                assert replies[0].region.height > 0
                assert not any(m.role is Role.ASSISTANT for m in runtime.session.messages)
                assert app.query_one("#send", Button).disabled
                assert app.query_one("#model-picker", Select).disabled
            finally:
                client.release.set()
            await app.workers.wait_for_complete()
            replies = [m for m in app.query(ConversationMessage) if m.title == "Assistant"]
            assert len(replies) == 1
            assert replies[0].text == client.output
            assert not replies[0].incomplete
            assert runtime.session.messages[-1].content == client.output
            assert not app._busy
    asyncio.run(scenario())


def test_ui_marks_interrupted_reply_and_can_retry(tmp_path):
    class InterruptedClient(FakeClient):
        def generate(self, messages, **kwargs):
            if not self.calls:
                self.calls.append((self.model, messages, kwargs))
                kwargs["on_chunk"]("partial reply")
                raise LLMConnectionError("connection lost")
            return super().generate(messages, **kwargs)

    async def scenario():
        app, runtime, client = make_app(tmp_path, InterruptedClient())
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            prompt = app.query_one("#prompt", PromptInput)
            prompt.load_text("Explain")
            await pilot.press("enter")
            await app.workers.wait_for_complete()
            partial = [m for m in app.query(ConversationMessage) if m.title == "Assistant"]
            assert len(partial) == 1 and partial[0].incomplete
            assert partial[0].text == "partial reply"
            assert runtime.last_response is None
            assert not any(m.role is Role.ASSISTANT for m in runtime.session.messages)
            prompt.load_text("Retry")
            await pilot.press("enter")
            await app.workers.wait_for_complete()
            replies = [m for m in app.query(ConversationMessage) if m.title == "Assistant"]
            assert len(replies) == 2
            assert not replies[-1].incomplete
            assert replies[-1].text == "reply"
            assert sum(m.role is Role.ASSISTANT for m in runtime.session.messages) == 1
    asyncio.run(scenario())


def test_long_stream_follows_bottom_and_preserves_manual_scroll(tmp_path):
    async def scenario():
        app, _, client = make_app(tmp_path)
        client.output = "```text\n" + "\n".join(f"Line {i:03d}" for i in range(80)) + "\n```"
        client.block = True
        async with app.run_test(size=(80, 24)) as pilot:
            await app.workers.wait_for_complete()
            app.query_one("#prompt", PromptInput).load_text("Explain")
            await pilot.press("enter")
            await wait_until(client.started.is_set)
            transcript = app.query_one("#conversation", VerticalScroll)
            try:
                await pilot.pause()
                assert transcript.max_scroll_y > 0
                assert transcript.is_vertical_scroll_end
                await pilot.resize_terminal(60, 22)
                await pilot.pause()
                assert transcript.is_vertical_scroll_end
                assert app.query_one("#send", Button).region.bottom <= 22
                transcript.scroll_home(animate=False)
                await pilot.pause()
                assert transcript.scroll_y == 0
            finally:
                client.release.set()
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert transcript.scroll_y == 0
            replies = [m for m in app.query(ConversationMessage) if m.title == "Assistant"]
            assert len(replies) == 1 and replies[0].text == client.output
    asyncio.run(scenario())


def test_file_drafts_wait_for_validation_and_confirmation(tmp_path):
    async def scenario():
        app, _, client = make_app(tmp_path)
        client.output = "print('complete')"
        client.block = True
        async with app.run_test(size=(100, 35)) as pilot:
            await app.workers.wait_for_complete()
            app.query_one("#prompt", PromptInput).load_text("/write {new.py}\nPrint complete")
            await pilot.press("enter")
            await wait_until(client.started.is_set)
            try:
                assert not client.calls[0][2].get("on_chunk")
                assert not [m for m in app.query(ConversationMessage) if m.title == "Assistant"]
                assert not (tmp_path / "new.py").exists()
            finally:
                client.release.set()
            await wait_until(lambda: isinstance(app.screen, ConfirmationScreen))
            assert not (tmp_path / "new.py").exists()
            await pilot.press("escape")
            await app.workers.wait_for_complete()
            assert not (tmp_path / "new.py").exists()
    asyncio.run(scenario())
