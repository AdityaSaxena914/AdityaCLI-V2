import asyncio
import json
from unittest.mock import patch

import pytest
from textual.containers import VerticalScroll
from textual.widgets import Button, Select, Static

from adityacli.core.models import Role
from adityacli.core.session import Session
from adityacli.core.session_store import SessionStore
from adityacli.ui.conversation import ConversationMessage
from adityacli.ui.screens import ConfirmationScreen, FileSelectionScreen, PromptInput
from tests.test_tui import make_app, wait_until


def errors(app):
    return [message.text for message in app.query(ConversationMessage) if message.title == "Error"]


@pytest.mark.parametrize("trigger", ["footer", "keyboard", "command"])
def test_clear_resets_transcript_draft_and_persistent_memory(tmp_path, trigger):
    (tmp_path / "source.py").write_text("FILE_CLEAR_SENTINEL = 17")
    _, original, _ = make_app(tmp_path)
    original.session.add_user("CHAT_CLEAR_SENTINEL")
    original.session.add_assistant("OLD_REPLY_SENTINEL")
    original.session.remember_file("source.py", "FILE_CLEAR_SENTINEL = 17")

    async def scenario():
        app, runtime, client = make_app(tmp_path, continued=True)
        async with app.run_test(size=(100, 35)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            runtime.chat("/remember")
            runtime.chat("Retain this history")
            previous_id = json.loads((tmp_path / ".sessions/current/session.json").read_text())["id"]
            # Reset must also remove legacy migration files and other chat data.
            (tmp_path / ".sessions/current/chat.jsonl").write_text("LEGACY_CLEAR_SENTINEL")
            (tmp_path / ".sessions/current/memory.json").write_text("LEGACY_CACHE_SENTINEL")
            prompt = app.query_one("#prompt", PromptInput)
            prompt.load_text("draft")
            prompt.move_cursor(prompt.document.end)
            prompt.focus()
            await pilot.press("ctrl+j", "ctrl+j")
            assert prompt.text == "draft\n\n"
            if trigger == "footer":
                key = next(key for key in app.query("FooterKey") if key.description == "Clear")
                await pilot.click(key)
            elif trigger == "keyboard":
                await pilot.press("ctrl+l")
            else:
                prompt.load_text("/clear")
                await pilot.press("enter")
            await wait_until(lambda: isinstance(app.screen, ConfirmationScreen))
            await pilot.pause()
            assert runtime.session.read_files
            await pilot.click("#confirm")
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert not list(app.query(ConversationMessage))
            assert not app.query_one("#conversation", VerticalScroll).children
            assert prompt.text == ""
            assert prompt.cursor_location == (0, 0)
            assert prompt.document.line_count == 1
            assert prompt.scroll_y == 0
            await pilot.press("ctrl+z")
            assert prompt.text == ""  # Clearing cannot be undone into an old draft.
            assert runtime.session.read_files == {}
            assert all(message.role is Role.SYSTEM for message in runtime.session.messages)
            assert runtime.session.prompt_messages == runtime.session.messages
            assert runtime.response_stats is None
            assert not runtime.continued_session
            assert client.model == "model-a"
            assert "cleared" in str(app.query_one("#status", Static).render())
            assert not errors(app)

            root = tmp_path / ".sessions/current"
            assert {path.name for path in root.iterdir()} == {"session.json", "memory.jsonl"}
            assert json.loads((root / "session.json").read_text())["id"] != previous_id
            journal = (root / "memory.jsonl").read_text()
            assert "SENTINEL" not in journal
            records = [json.loads(line) for line in journal.splitlines()]
            assert len(records) == 1 and records[0]["role"] == "system"
            runtime.chat("/remember")
            assert runtime.session.read_files == {}
            assert all(message.role is Role.SYSTEM for message in runtime.session.prompt_messages)
            loaded = Session(SessionStore(tmp_path))
            loaded.load()
            assert loaded.messages == runtime.session.messages
            assert loaded.restore_memory() == (1, 0)
            assert (tmp_path / "source.py").read_text() == "FILE_CLEAR_SENTINEL = 17"
    asyncio.run(scenario())


def test_cancel_clear_preserves_chat_cache_and_multiline_draft(tmp_path):
    async def scenario():
        app, runtime, _ = make_app(tmp_path)
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            runtime.session.add_user("previous chat")
            runtime.session.remember_file("source.py", "source = 1")
            app._write_message("You", "previous chat")
            prompt = app.query_one("#prompt", PromptInput)
            prompt.load_text("unfinished\n\ndraft")
            journal = (tmp_path / ".sessions/current/memory.jsonl").read_bytes()
            await pilot.press("ctrl+l")
            await wait_until(lambda: isinstance(app.screen, ConfirmationScreen))
            await pilot.press("escape")
            await app.workers.wait_for_complete()
            assert prompt.text == "unfinished\n\ndraft"
            assert runtime.session.read_files == {"source.py": "source = 1"}
            assert any(message.text == "previous chat" for message in app.query(ConversationMessage))
            assert (tmp_path / ".sessions/current/memory.jsonl").read_bytes() == journal
    asyncio.run(scenario())


def test_clear_storage_failure_preserves_existing_state_and_draft(tmp_path):
    async def scenario():
        app, runtime, _ = make_app(tmp_path)
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            runtime.chat("previous question")
            runtime.session.remember_file("source.py", "source = 1")
            messages = list(runtime.session.messages)
            response = runtime.last_response
            prompt = app.query_one("#prompt", PromptInput)
            prompt.load_text("unfinished\n\n")
            app._write_message("You", "previous question")
            with patch.object(runtime._store, "clear", side_effect=OSError("storage unavailable")):
                await pilot.press("ctrl+l")
                await wait_until(lambda: isinstance(app.screen, ConfirmationScreen))
                await pilot.pause()
                await pilot.click("#confirm")
                await app.workers.wait_for_complete()
            assert runtime.session.messages == messages
            assert runtime.session.read_files == {"source.py": "source = 1"}
            assert runtime.last_response is response
            assert prompt.text == "unfinished\n\n"
            assert errors(app) == ["storage unavailable"]
            assert not app._busy
    asyncio.run(scenario())


def test_refresh_preserves_selected_model_context_and_statistics(tmp_path):
    async def scenario():
        app, runtime, client = make_app(tmp_path)
        async with app.run_test(size=(100, 35)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert not errors(app)
            picker = app.query_one("#model-picker", Select)
            picker.value = "model-b"
            # Selection is asynchronous; do not call the runtime directly until
            # the UI has applied this switch.
            await wait_until(lambda: client.model == "model-b")
            runtime.chat("keep this context")
            runtime.session.remember_file("source.py", "source = 1")
            context = list(runtime.session.prompt_messages)
            response = runtime.last_response
            for _ in range(3):
                await pilot.click("#refresh-models")
                await app.workers.wait_for_complete()
                await pilot.pause()
                assert picker.value == client.model == "model-b"
                assert not errors(app)
                assert runtime.session.prompt_messages == context
                assert runtime.session.read_files == {"source.py": "source = 1"}
                assert runtime.last_response is response
                assert not picker.disabled
            assert len(client.calls) == 1
    asyncio.run(scenario())


def test_refresh_handles_removed_models_empty_catalog_and_recovery(tmp_path):
    async def scenario():
        app, runtime, client = make_app(tmp_path)
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            picker = app.query_one("#model-picker", Select)
            picker.value = "model-b"
            await pilot.pause()
            runtime.chat("old model context")
            client.models = client.models[:1]
            await pilot.press("ctrl+r")
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert picker.value == client.model == "model-a"
            assert all(message.role is Role.SYSTEM for message in runtime.session.prompt_messages)
            assert any(message.content == "old model context" for message in runtime.session.messages)
            models = client.models
            client.models = []
            await pilot.press("ctrl+r")
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert picker.disabled
            assert not isinstance(picker.value, str)
            client.models = models
            await pilot.click("#refresh-models")
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert picker.value == "model-a" and not picker.disabled
            assert not errors(app)
    asyncio.run(scenario())


def test_prompt_footer_removed_and_focus_shortcut_retained(tmp_path):
    async def scenario():
        app, _, _ = make_app(tmp_path)
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert not any(key.description in {"Prompt", "Focus input"} for key in app.query("FooterKey"))
            picker = app.query_one("#model-picker", Select)
            picker.focus()
            await pilot.pause()
            assert picker.has_focus
            await pilot.press("ctrl+n")
            assert app.query_one("#prompt", PromptInput).has_focus
    asyncio.run(scenario())


def test_file_selection_waits_for_valid_index_including_zero(tmp_path):
    for folder in ("one", "two"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "source.py").write_text(folder)
    async def scenario():
        app, runtime, _ = make_app(tmp_path)
        async with app.run_test(size=(100, 35)) as pilot:
            await app.workers.wait_for_complete()
            app.query_one("#prompt", PromptInput).load_text("/read source")
            await pilot.press("enter")
            await wait_until(lambda: isinstance(app.screen, FileSelectionScreen))
            await pilot.pause()
            screen = app.screen
            assert screen.query_one("#read-file", Button).disabled
            screen.select_file()  # Blank selection must not dismiss or crash.
            assert app.screen is screen
            screen.query_one("#file-choice", Select).value = 0
            await pilot.pause()
            assert not screen.query_one("#read-file", Button).disabled
            selected = screen.request.candidates[0]
            await pilot.click("#read-file")
            await app.workers.wait_for_complete()
            assert selected in runtime.session.read_files
            assert not errors(app)
    asyncio.run(scenario())
