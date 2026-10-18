import asyncio
from pathlib import Path
from threading import Event

from textual.widgets import Button, RichLog, Select

from adityacli.cli import CLI
from adityacli.config import AppConfig, LMStudioConfig, SecurityConfig, WorkspaceConfig
from adityacli.core.file_manager import FileManager
from adityacli.core.models import LLMResponse
from adityacli.core.parser import Parser
from adityacli.core.prompt_builder import PromptBuilder
from adityacli.core.response_parser import ResponseParser
from adityacli.core.runtime import Runtime
from adityacli.core.session_store import SessionStore
from adityacli.llm.models import AvailableModel
from adityacli.services.chat_service import ChatService
from adityacli.services.command_service import CommandService
from adityacli.services.llm_service import LLMService
from adityacli.services.overwrite_service import OverwriteService
from adityacli.tools.registry import ToolRegistry
from adityacli.ui.conversation import ConversationMessage
from adityacli.ui.screens import ConfirmationScreen, FileSelectionScreen, FollowupScreen, PromptInput


class FakeClient:
    def __init__(self) -> None:
        self.model = ""
        self.models = [
            AvailableModel("model-a", "Model A", True, 8192, "Q4_K_M"),
            AvailableModel("model-b", "Model B", False),
        ]
        self.calls = []
        self.output = "reply"
        self.offline = False
        self.started = Event()
        self.release = Event()
        self.block = False

    @property
    def selected_model(self):
        return next((model for model in self.models if model.id == self.model), None)

    @property
    def context_window(self):
        return self.selected_model.context_window if self.selected_model else None

    def list_models(self):
        if self.offline:
            raise ConnectionError("LM Studio offline")
        return list(self.models)

    def select_model(self, model_id):
        assert any(model.id == model_id for model in self.models)
        self.model = model_id

    def health_check(self):
        self.list_models()

    def generate(self, messages, **kwargs):
        self.calls.append((self.model, messages, kwargs))
        on_chunk = kwargs.get("on_chunk")
        split = max(1, len(self.output) // 2)
        if on_chunk:
            on_chunk(self.output[:split])
        self.started.set()
        if self.block:
            assert self.release.wait(5), "test did not release generation"
        if on_chunk:
            on_chunk(self.output[split:])
        return LLMResponse(self.output, self.model, 10, 20, 30, 1.0)


def make_app(workspace: Path, client: FakeClient | None = None, *, continued=False):
    client = client or FakeClient()
    config = AppConfig(WorkspaceConfig(workspace), LMStudioConfig(), SecurityConfig())
    parser = Parser()
    chat = ChatService(
        CommandService(parser, ToolRegistry(config)),
        LLMService(client, PromptBuilder(), config),
        OverwriteService(ResponseParser(), FileManager(config)),
    )
    runtime = Runtime(
        config=config, parser=parser, store=SessionStore(workspace),
        chat_service=chat, continue_session=continued,
    )
    runtime.add_system_prompt("system")
    return CLI(runtime, client), runtime, client


async def wait_until(predicate):
    async with asyncio.timeout(5):
        while not predicate():
            await asyncio.sleep(0.02)


def test_model_dropdown_and_keyboard_submission(tmp_path):
    async def scenario():
        app, runtime, client = make_app(tmp_path)
        async with app.run_test(size=(100, 35)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert client.model == "model-a"
            picker = app.query_one("#model-picker", Select)
            await pilot.click("#model-picker")
            await pilot.press("down", "enter")
            await pilot.pause()
            assert client.model == "model-b"
            prompt = app.query_one("#prompt", PromptInput)
            prompt.focus()
            await pilot.press("h", "i", "ctrl+j", "t", "h", "e", "r", "e")
            assert prompt.text == "hi\nthere"
            await pilot.press("enter")
            await app.workers.wait_for_complete()
            assert client.calls[0][0] == "model-b"
            assert client.calls[0][2]["max_tokens"] is None
            assert runtime.session.messages[-2].content == "hi\nthere"
            assert prompt.text == ""
            assert not app._busy
    asyncio.run(scenario())


def test_direct_read_does_not_call_model(tmp_path):
    (tmp_path / "example.py").write_text("print('example')", encoding="utf-8")
    async def scenario():
        app, runtime, client = make_app(tmp_path)
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            app.query_one("#prompt", PromptInput).load_text("/read example.py")
            await pilot.press("enter")
            await app.workers.wait_for_complete()
            assert not client.calls
            assert runtime.session.read_files["example.py"] == "print('example')"
    asyncio.run(scenario())


def test_write_preview_requires_explicit_confirmation(tmp_path):
    async def scenario():
        app, runtime, client = make_app(tmp_path)
        client.output = "print('new')"
        async with app.run_test(size=(100, 35)) as pilot:
            await app.workers.wait_for_complete()
            prompt = app.query_one("#prompt", PromptInput)
            prompt.load_text("/write {new.py}\nGenerate a greeting")
            await pilot.press("enter")
            await wait_until(lambda: isinstance(app.screen, ConfirmationScreen))
            await pilot.pause()
            assert not (tmp_path / "new.py").exists()
            assert app.screen.query_one("#preview", RichLog).lines
            await pilot.click("#cancel")
            await app.workers.wait_for_complete()
            assert not (tmp_path / "new.py").exists()
            prompt.load_text("/write {new.py}\nGenerate a greeting")
            await pilot.press("enter")
            await wait_until(lambda: isinstance(app.screen, ConfirmationScreen))
            await pilot.pause()
            await pilot.click("#confirm")
            await app.workers.wait_for_complete()
            assert (tmp_path / "new.py").read_text() == "print('new')"
    asyncio.run(scenario())


def test_edit_shows_diff_before_saving(tmp_path):
    (tmp_path / "example.py").write_text("print('old')", encoding="utf-8")
    async def scenario():
        app, _, client = make_app(tmp_path)
        client.output = "print('updated')"
        async with app.run_test(size=(100, 35)) as pilot:
            await app.workers.wait_for_complete()
            app.query_one("#prompt", PromptInput).load_text("/edit example.py\nUpdate text")
            await pilot.press("enter")
            await wait_until(lambda: isinstance(app.screen, ConfirmationScreen))
            await pilot.pause()
            lines = app.screen.query_one("#preview", RichLog).lines
            text = "\n".join(line.text for line in lines)
            assert "-print('old')" in text and "+print('updated')" in text
            assert (tmp_path / "example.py").read_text() == "print('old')"
            await pilot.click("#confirm")
            await app.workers.wait_for_complete()
            assert (tmp_path / "example.py").read_text() == "print('updated')"
    asyncio.run(scenario())


def test_followup_can_be_cancelled_or_submitted(tmp_path):
    async def scenario():
        app, _, client = make_app(tmp_path)
        client.output = "print('hello')"
        async with app.run_test(size=(100, 35)) as pilot:
            await app.workers.wait_for_complete()
            prompt = app.query_one("#prompt", PromptInput)
            prompt.load_text("/write {hello.py}")
            await pilot.press("enter")
            await wait_until(lambda: isinstance(app.screen, FollowupScreen))
            await pilot.press("escape")
            await app.workers.wait_for_complete()
            assert not client.calls
            assert prompt.text == "/write {hello.py}"
            await pilot.press("enter")
            await wait_until(lambda: isinstance(app.screen, FollowupScreen))
            await pilot.pause()
            app.screen.query_one("#followup", PromptInput).load_text("Print hello")
            await pilot.press("enter")
            await wait_until(lambda: isinstance(app.screen, ConfirmationScreen))
            await pilot.pause()
            await pilot.press("escape")
            await app.workers.wait_for_complete()
            assert len(client.calls) == 1
            assert not (tmp_path / "hello.py").exists()
    asyncio.run(scenario())


def test_ambiguous_read_selection(tmp_path):
    for directory in ("one", "two"):
        (tmp_path / directory).mkdir()
        (tmp_path / directory / "example.py").write_text(directory)
    async def scenario():
        app, runtime, client = make_app(tmp_path)
        async with app.run_test(size=(100, 35)) as pilot:
            await app.workers.wait_for_complete()
            app.query_one("#prompt", PromptInput).load_text("/read example")
            await pilot.press("enter")
            await wait_until(lambda: isinstance(app.screen, FileSelectionScreen))
            await pilot.pause()
            app.screen.query_one("#file-choice", Select).value = 1
            await pilot.pause()
            selected = app.screen.request.candidates[1]
            await pilot.click("#read-file")
            await app.workers.wait_for_complete()
            assert selected in runtime.session.read_files
            assert not client.calls
    asyncio.run(scenario())


def test_clear_confirmation_and_continued_history(tmp_path):
    app, runtime, _ = make_app(tmp_path)
    runtime.session.add_user("Previous question")
    runtime.session.add_assistant("Previous answer")
    async def scenario():
        app, runtime, _ = make_app(tmp_path, continued=True)
        async with app.run_test(size=(100, 35)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            text = "\n".join(message.text for message in app.query(ConversationMessage))
            assert "Previous question" in text and "Previous answer" in text
            await pilot.press("ctrl+l")
            await wait_until(lambda: isinstance(app.screen, ConfirmationScreen))
            await pilot.pause()
            await pilot.press("escape")
            await app.workers.wait_for_complete()
            assert len(runtime.session.messages) == 3
            await pilot.press("ctrl+l")
            await wait_until(lambda: isinstance(app.screen, ConfirmationScreen))
            await pilot.pause()
            await pilot.click("#confirm")
            await app.workers.wait_for_complete()
            assert len(runtime.session.messages) == 1
    asyncio.run(scenario())


def test_ui_stays_responsive_and_prevents_concurrent_requests(tmp_path):
    async def scenario():
        app, _, client = make_app(tmp_path)
        client.block = True
        async with app.run_test(size=(100, 35)) as pilot:
            await app.workers.wait_for_complete()
            prompt = app.query_one("#prompt", PromptInput)
            prompt.load_text("Explain")
            await pilot.press("enter")
            await wait_until(client.started.is_set)
            try:
                assert app.query_one("#model-picker", Select).disabled
                assert app.query_one("#send", Button).disabled
                await pilot.press("n", "e", "x", "t", "enter")
                assert prompt.text == "next"
                assert len(client.calls) == 1
            finally:
                client.release.set()
            await app.workers.wait_for_complete()
            assert not app.query_one("#send", Button).disabled
    asyncio.run(scenario())


def test_offline_startup_recovers_after_refresh(tmp_path):
    async def scenario():
        client = FakeClient()
        client.offline = True
        app, _, _ = make_app(tmp_path, client)
        async with app.run_test(size=(80, 24)) as pilot:
            await app.workers.wait_for_complete()
            assert app.query_one("#model-picker", Select).disabled
            client.offline = False
            await pilot.click("#refresh-models")
            await app.workers.wait_for_complete()
            assert client.model == "model-a"
            assert not app.query_one("#model-picker", Select).disabled
            assert app.query_one("#send", Button).region.bottom <= 24
    asyncio.run(scenario())
