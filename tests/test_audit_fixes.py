"""Counterexamples from the 2026-10-17 audit and recovery/limit invariants."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import asyncio
import warnings
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from time import monotonic
from unittest.mock import patch

import pytest

from adityacli.config import AppConfig, ExecutionConfig, LMStudioConfig, SecurityConfig, WorkspaceConfig
from adityacli.core.file_manager import FileManager
from adityacli.core.locking import file_lock
from adityacli.core.models import Command, Message, OverwriteRequest, Role, Tool
from adityacli.core.operations import Operation
from adityacli.core.processes import ProcessOutput, find_executable
from adityacli.core.response_parser import ResponseParser
from adityacli.core.session import Session
from adityacli.core.session_store import SessionStore
from adityacli.exceptions import FileTooLargeError, LLMError, MalformedGenerationError, OperationCancelled, OperationTimeout, ValidationError
from adityacli.services.overwrite_service import OverwriteService
from adityacli.tools.git import GitTool
from adityacli.tools.search import SearchTool
from adityacli.ui.diff import build_diff


def cfg(path, *, max_size=2 * 1024 * 1024, regex_timeout=1.0):
    return AppConfig(WorkspaceConfig(path, max_file_size=max_size), LMStudioConfig(), SecurityConfig(),
                     ExecutionConfig(regex_timeout=regex_timeout))


@pytest.mark.parametrize("section", ['filter "audit"', 'filter\t"audit"', 'FILTER\t"audit"', 'filter.audit'])
def test_git_uses_native_config_grammar_and_never_runs_filter(tmp_path, section):
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    (tmp_path / ".gitattributes").write_text("payload.txt filter=audit\n")
    (tmp_path / "payload.txt").write_text('from pathlib import Path\nPath("marker").touch()\n')
    # A single executable avoids invoking a shell even if this regression fails.
    executable = sys.executable.replace("\\", "/")
    with (tmp_path / ".git/config").open("a") as file:
        file.write(f'\n[{section}]\n clean = "{executable}"\n required = true\n')
    with pytest.raises(ValidationError, match="filters"):
        GitTool(cfg(tmp_path)).execute(Command(Tool.GIT, ["add", "payload.txt"], ""))
    assert not (tmp_path / "marker").exists()


def test_regex_fallback_is_killable_and_literal_mode_is_safe(tmp_path, monkeypatch):
    monkeypatch.setattr("adityacli.tools.search.shutil.which", lambda name: None)
    (tmp_path / "source.txt").write_text("a" * 36 + "!\n(a+)+$\n")
    search = SearchTool(cfg(tmp_path))
    start = monotonic()
    with pytest.raises(OperationTimeout):
        search.execute(Command(Tool.SEARCH, ["(a+)+$"], ""))
    assert monotonic() - start < 6
    assert "source.txt:2:" in search.execute(Command(Tool.SEARCH, ["--literal (a+)+$"], "")).prompt


def test_process_deadline_covers_blocked_stdout(tmp_path):
    start = monotonic()
    with pytest.raises(OperationTimeout):
        list(ProcessOutput([sys.executable, "-c", "import time; time.sleep(30)"], cwd=tmp_path, timeout=0.3))
    assert monotonic() - start < 5


def test_deadline_kills_descendant_after_parent_exit(tmp_path):
    code = "import subprocess,sys; subprocess.Popen([sys.executable,'-c',\"import time; time.sleep(30)\"]); print('spawned',flush=True)"
    start = monotonic()
    with pytest.raises(OperationTimeout):
        list(ProcessOutput([sys.executable, "-c", code], cwd=tmp_path, timeout=0.5))
    assert monotonic() - start < 5


def test_process_can_be_cancelled_while_no_output_arrives(tmp_path):
    operation = Operation(10)
    timer = threading.Timer(0.3, operation.cancel)
    timer.start()
    try:
        with operation.activate(), pytest.raises(OperationCancelled):
            list(ProcessOutput([sys.executable, "-c", "import time; time.sleep(30)"], cwd=tmp_path))
    finally:
        timer.cancel()


def test_concurrent_journal_writers_preserve_every_record(tmp_path):
    SessionStore(tmp_path).create("test", 8192)
    code = '''from pathlib import Path
import sys
from adityacli.core.session_store import SessionStore
from adityacli.core.models import Message, Role
store=SessionStore(Path(sys.argv[1]))
for i in range(30): store.append_message(Message(Role.USER, sys.argv[2]+str(i)))
'''
    writers = [subprocess.Popen([sys.executable, "-I", "-c", code, str(tmp_path), f"writer-{i}-"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE) for i in range(3)]
    for writer in writers:
        stdout, stderr = writer.communicate(timeout=20)
        assert writer.returncode == 0, stderr.decode()
    messages = SessionStore(tmp_path).load_messages()
    assert len(messages) == len({message.content for message in messages}) == 90


def test_workspace_lease_rejects_second_process(tmp_path):
    store = SessionStore(tmp_path)
    with store.workspace_lease():
        code = "from pathlib import Path; import sys; from adityacli.core.session_store import SessionStore; s=SessionStore(Path(sys.argv[1])); s.workspace_lease().__enter__()"
        result = subprocess.run([sys.executable, "-I", "-c", code, str(tmp_path)], capture_output=True, timeout=10)
    assert result.returncode != 0
    assert b"another process" in result.stderr


def test_failed_clear_preparation_preserves_disk_and_memory(tmp_path):
    store = SessionStore(tmp_path)
    store.create("test", 8192)
    session = Session(store)
    session.add_user("saved")
    original = (tmp_path / ".sessions/current/memory.jsonl").read_bytes()
    with patch.object(store, "_write_json", side_effect=OSError("disk full")), pytest.raises(OSError):
        session.clear("test", 8192)
    assert session.messages[0].content == "saved"
    assert (tmp_path / ".sessions/current/memory.jsonl").read_bytes() == original


def test_interrupted_clear_install_rolls_back(tmp_path):
    store = SessionStore(tmp_path)
    store.create("test", 8192)
    store.append_message(Message(Role.USER, "saved"))
    replace = os.replace
    def fail_install(source, destination):
        if Path(source).name.startswith(".new-"):
            raise OSError("injected install failure")
        return replace(source, destination)
    with patch("adityacli.core.session_store.os.replace", fail_install), pytest.raises(OSError):
        store.clear("test", 8192)
    assert [message.content for message in SessionStore(tmp_path).load_messages()] == ["saved"]


def test_failed_append_never_publishes_unsaved_message(tmp_path):
    store = SessionStore(tmp_path)
    store.create("test", 8192)
    session = Session(store)
    with patch.object(store, "append_message", side_effect=OSError("disk full")), pytest.raises(OSError):
        session.add_user("unsaved")
    assert session.messages == session.prompt_messages == store.load_messages() == []


def test_cache_eviction_and_new_contents_commit_together(tmp_path):
    store = SessionStore(tmp_path)
    store.create("test", 8192)
    session = Session(store, max_read_tokens=2)
    session.remember_file("old.txt", "12345678")
    with patch.object(store, "append_records", side_effect=OSError("disk full")), pytest.raises(OSError):
        session.remember_file("new.txt", "abcdefgh")
    assert session.read_files == store.read_memory() == {"old.txt": "12345678"}


def test_failed_journal_fsync_rolls_back_complete_operation(tmp_path):
    store = SessionStore(tmp_path)
    store.create("test", 8192)
    with patch("adityacli.core.session_store.os.fsync", side_effect=OSError("disk full")), pytest.raises(OSError):
        store.append_message(Message(Role.USER, "unsaved"))
    assert store.load_messages() == []


def test_conflict_is_checked_after_staging(tmp_path):
    path = tmp_path / "source.txt"
    path.write_text("original")
    manager = FileManager(cfg(tmp_path))
    real_fsync = os.fsync
    def external_edit(fd):
        real_fsync(fd)
        path.write_text("external edit while staging")
    with patch("adityacli.core.file_manager.os.fsync", external_edit), pytest.raises(ValidationError, match="changed"):
        manager.write_many({"source.txt": "proposal"}, overwrite=True, expected_contents={"source.txt": "original"})
    assert path.read_text() == "external edit while staging"


@pytest.mark.parametrize("source", ["return 1", "break", "await work()", "nonlocal missing"])
def test_python_proposals_must_compile_without_execution(source):
    with pytest.raises(MalformedGenerationError):
        ResponseParser().parse_write_response(source, ["output.py"])


def test_size_limit_precedes_parsing_preview_and_archiving(tmp_path):
    manager = FileManager(cfg(tmp_path, max_size=4))
    service = OverwriteService(ResponseParser(), manager)
    with pytest.raises(FileTooLargeError):
        service.create_request(Command(Tool.WRITE, ["file.txt"], ""), "12345")
    from tests.test_tui import make_app
    _, runtime, client = make_app(tmp_path)
    client.output = "x" * (2 * 1024 * 1024 + 1)
    with pytest.raises(FileTooLargeError):
        runtime.chat("/write {file.txt}\nGenerate text")
    assert not any(message.role is Role.ASSISTANT for message in runtime.session.messages)


def test_final_newline_change_is_visible():
    diff = build_diff("value = 1\n", "value = 1")
    assert "-value = 1" in diff and "+value = 1" in diff
    assert "\\ No newline at end of file" in diff


def test_reset_recovers_after_process_dies_between_renames(tmp_path):
    store = SessionStore(tmp_path)
    store.create("test", 8192)
    store.append_message(Message(Role.USER, "recover me"))
    code = '''import os,sys
from pathlib import Path
from adityacli.core.session_store import SessionStore
replace=os.replace
def crash(source,destination):
    if Path(source).name.startswith('.new-'): os._exit(47)
    return replace(source,destination)
os.replace=crash
SessionStore(Path(sys.argv[1])).clear('test',8192)
'''
    result = subprocess.run([sys.executable, "-I", "-c", code, str(tmp_path)], timeout=10)
    assert result.returncode == 47
    assert [message.content for message in SessionStore(tmp_path).load_messages()] == ["recover me"]
    assert not (tmp_path / ".sessions/reset.json").exists()


def test_incomplete_cache_batch_does_not_replay_eviction(tmp_path):
    store = SessionStore(tmp_path)
    store.create("test", 8192)
    store.cache_file("old.txt", "saved")
    with (tmp_path / ".sessions/current/memory.jsonl").open("ab") as file:
        file.write(b'{"v":1,"type":"batch","records":[{"type":"forget_file","path":"old.txt"},')
    assert store.read_memory() == {"old.txt": "saved"}
    session = Session(store, max_read_tokens=2)
    session.restore_memory()
    session.remember_file("new.txt", "abcdefgh")
    assert store.read_memory() == {"new.txt": "abcdefgh"}


@pytest.mark.parametrize("record", [[], {"v": 2}, {"type": "unknown"},
                                    {"type": "message", "role": "user", "content": []},
                                    {"type": "batch", "records": [{"type": "batch", "records": []}]}])
def test_invalid_complete_journal_record_fails_closed(tmp_path, record):
    store = SessionStore(tmp_path)
    store.create("test", 8192)
    (tmp_path / ".sessions/current/memory.jsonl").write_text(json.dumps(record) + "\n")
    with pytest.raises(ValidationError):
        store.load_state()


def test_clear_stages_system_prompt_before_commit(tmp_path):
    from tests.test_tui import make_app
    _, runtime, _ = make_app(tmp_path)
    runtime.session.add_user("preserve me")
    original = runtime.session.messages.copy()
    real_fsync = os.fsync
    calls = 0
    def fail_journal(fd):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("journal unavailable")
        return real_fsync(fd)
    with patch("adityacli.core.session_store.os.fsync", fail_journal), pytest.raises(OSError):
        runtime.clear()
    assert runtime.session.messages == original
    assert runtime._store.load_messages() == original


def test_successful_file_apply_reports_later_session_failure_truthfully(tmp_path):
    from tests.test_tui import make_app
    _, runtime, _ = make_app(tmp_path)
    request = OverwriteRequest({"file.txt": "applied"}, {"file.txt": None})
    with patch.object(runtime._store, "append_records", side_effect=OSError("disk full")):
        with pytest.raises(ValidationError, match="Files were applied, but session recording failed"):
            runtime.confirm_overwrite(request)
    assert (tmp_path / "file.txt").read_text() == "applied"


@contextmanager
def model_server(respond):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            try:
                respond(self)
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass

        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.02), daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize("streaming", [False, True])
def test_real_http_transport_stops_oversized_unknown_length_body(streaming):
    from adityacli.llm.client import LLMClient
    def respond(handler):
        handler.send_response(200)
        handler.send_header("Content-Type", "text/event-stream" if streaming else "application/json")
        handler.end_headers()
        handler.wfile.write(b"x" * 70000)
        handler.wfile.flush()
    with model_server(respond) as url:
        client = LLMClient(LMStudioConfig(base_url=url, model="fixture", max_response_bytes=8))
        try:
            with pytest.raises((FileTooLargeError, LLMError), match="byte limit"):
                client.generate([Message(Role.USER, "test")], on_chunk=(lambda _: None) if streaming else None)
        finally:
            client.close()


def test_stream_limit_counts_encoded_unicode_before_callback():
    from tests.test_streaming import stream_client, event
    client, stream, _ = stream_client([event("éé"), event("é", "stop")])
    chunks = []
    try:
        with pytest.raises(FileTooLargeError):
            client.generate([Message(Role.USER, "test")], max_response_bytes=4, on_chunk=chunks.append)
        assert chunks == ["éé"]
        assert stream.closed
    finally:
        client.close()


def test_real_http_stall_can_be_cancelled_and_client_recovers():
    from adityacli.llm.client import LLMClient
    release, started = threading.Event(), threading.Event()
    def respond(handler):
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler.end_headers()
        started.set()
        release.wait(3)
        body = {"id": "fixture", "object": "chat.completion", "created": 1, "model": "fixture",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "recovered"}, "finish_reason": "stop"}]}
        handler.wfile.write(json.dumps(body).encode())
    with model_server(respond) as url:
        client = LLMClient(LMStudioConfig(base_url=url, model="fixture", timeout=2))
        operation = Operation(2)
        timer = threading.Timer(0.3, operation.cancel)
        timer.start()
        start = monotonic()
        try:
            with operation.activate(), pytest.raises(OperationCancelled):
                client.generate([Message(Role.USER, "test")])
            assert started.is_set() and monotonic() - start < 1.5
            release.set()
            deadline = monotonic() + 4
            while client._transport_lock.locked() and monotonic() < deadline:
                release.wait(0.01)
                threading.Event().wait(0.01)
            assert client.generate([Message(Role.USER, "retry")]).content == "recovered"
        finally:
            release.set()
            timer.cancel()
            client.close()


def test_ui_cancel_releases_controls_and_excludes_partial_reply(tmp_path):
    from tests.test_tui import FakeClient, make_app, wait_until
    from adityacli.core.operations import current_operation
    from adityacli.ui.screens import PromptInput
    from adityacli.ui.conversation import ConversationMessage
    class CancellableClient(FakeClient):
        def generate(self, messages, **kwargs):
            kwargs["on_chunk"]("partial")
            self.started.set()
            operation = current_operation()
            while not operation.cancelled.wait(0.02):
                operation.check()
            operation.check()
    async def scenario():
        app, runtime, client = make_app(tmp_path, CancellableClient())
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            app.query_one("#prompt", PromptInput).load_text("Explain")
            await pilot.press("enter")
            await wait_until(client.started.is_set)
            await pilot.press("ctrl+x")
            await app.workers.wait_for_complete()
            assert not app._busy
            replies = [message for message in app.query(ConversationMessage) if message.title == "Assistant"]
            assert len(replies) == 1 and replies[0].incomplete
            assert not any(message.role is Role.ASSISTANT for message in runtime.session.messages)
    asyncio.run(scenario())


def test_file_apply_preserves_received_line_endings_and_checks_exact_snapshot(tmp_path):
    path = tmp_path / "source.txt"
    path.write_bytes(b"original\r\n")
    manager = FileManager(cfg(tmp_path))
    assert manager.read("source.txt") == "original\r\n"
    manager.write_many({"source.txt": "updated\r\n"}, overwrite=True,
                       expected_contents={"source.txt": "original\r\n"})
    assert path.read_bytes() == b"updated\r\n"


def test_ui_batches_a_thousand_deltas_without_losing_text(tmp_path):
    from tests.test_tui import FakeClient, make_app
    from adityacli.core.models import LLMResponse
    from adityacli.ui.screens import PromptInput
    from adityacli.ui.conversation import ConversationMessage
    class BurstClient(FakeClient):
        def generate(self, messages, **kwargs):
            for _ in range(1000):
                kwargs["on_chunk"]("a")
            return LLMResponse("a" * 1000, self.model, 10, 1000, 1010, 1.0)
    async def scenario():
        app, runtime, _ = make_app(tmp_path, BurstClient())
        renders = []
        original = ConversationMessage.set_text
        def record_render(self, text, **kwargs):
            renders.append(len(text))
            return original(self, text, **kwargs)
        with patch.object(ConversationMessage, "set_text", record_render):
            async with app.run_test() as pilot:
                await app.workers.wait_for_complete()
                app.query_one("#prompt", PromptInput).load_text("Explain")
                await pilot.press("enter")
                await app.workers.wait_for_complete()
                replies = [message for message in app.query(ConversationMessage) if message.title == "Assistant"]
                assert len(replies) == 1 and replies[0].text == "a" * 1000
                assert runtime.session.messages[-1].content == "a" * 1000
                assert len(renders) < 50
                # A late callback from an earlier interaction cannot create a reply.
                app._stream_queue.put((object(), "stale"))
                app._flush_stream()
                assert replies[0].text == "a" * 1000
    asyncio.run(scenario())


def test_blocked_web_provider_cancellation_releases_runtime(tmp_path):
    from adityacli.tools.web import WebTool
    class Provider:
        started = threading.Event()
        release = threading.Event()
        def search(self, query):
            self.started.set()
            self.release.wait(3)
            return []
    provider = Provider()
    tool = WebTool(cfg(tmp_path), provider)
    operation = Operation(2)
    timer = threading.Timer(0.2, operation.cancel)
    timer.start()
    try:
        with operation.activate(), pytest.raises(OperationCancelled):
            tool.execute(Command(Tool.WEB, ["fixture"], ""))
        assert provider.started.is_set()
    finally:
        provider.release.set()
        timer.cancel()


def test_unsafe_compatibility_settings_fail_at_construction():
    with pytest.raises(ValueError):
        SecurityConfig(allow_workspace_escape=True)
    with pytest.raises(ValueError):
        WorkspaceConfig(Path.cwd(), overwrite_confirmation=False)
    with pytest.raises(ValueError):
        ExecutionConfig(regex_timeout=0)
    with pytest.raises(ValueError):
        LMStudioConfig(timeout=float("nan"))
    with pytest.raises(ValueError):
        ExecutionConfig(tool_timeout=float("inf"))


def test_committed_clear_cleanup_failure_keeps_memory_and_disk_consistent(tmp_path):
    store = SessionStore(tmp_path)
    store.create("test", 8192)
    session = Session(store)
    session.add_user("old record")
    remove = store._remove_tree
    def fail_backup_cleanup(relative):
        if ".old-" in relative:
            raise OSError("backup temporarily locked")
        remove(relative)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        with patch.object(store, "_remove_tree", fail_backup_cleanup):
            session.clear("test", 8192)
            assert session.messages == store.load_messages() == []
            with pytest.raises(ValidationError, match="cleanup is pending"):
                store.clear("test", 8192)
    assert store.load_messages() == []
    assert not (tmp_path / ".sessions/reset.json").exists()


def test_initial_reset_failure_preserves_prepared_state_for_recovery(tmp_path):
    store = SessionStore(tmp_path)
    replace = os.replace
    def fail_install(source, destination):
        if Path(source).name.startswith(".new-"):
            raise OSError("initial install unavailable")
        return replace(source, destination)
    with patch("adityacli.core.session_store.os.replace", fail_install), pytest.raises(OSError):
        store.create("test", 8192)
    assert store.exists
    assert store.load_messages() == []


def test_external_tool_lookup_never_uses_workspace_or_relative_path(tmp_path, monkeypatch):
    workspace, trusted = tmp_path / "workspace", tmp_path / "external-bin"
    workspace.mkdir()
    trusted.mkdir()
    name = "git.exe" if os.name == "nt" else "git"
    for directory in (workspace, trusted):
        executable = directory / name
        executable.write_text("synthetic executable lookup fixture")
        executable.chmod(0o755)
    monkeypatch.chdir(workspace)
    monkeypatch.setenv("PATH", os.pathsep.join((".", str(workspace), str(trusted))))
    assert find_executable("git", workspace) == str((trusted / name).resolve())
    monkeypatch.setenv("PATH", ".")
    assert find_executable("git", workspace) is None


def test_immediate_send_uses_visible_model_before_queued_change_event(tmp_path):
    from tests.test_tui import make_app
    from adityacli.ui.screens import PromptInput
    from textual.widgets import Select
    async def scenario():
        app, runtime, client = make_app(tmp_path)
        async with app.run_test():
            await app.workers.wait_for_complete()
            app.query_one("#model-picker", Select).value = "model-b"
            app.query_one("#prompt", PromptInput).load_text("Explain")
            app._submit()
            await app.workers.wait_for_complete()
            assert client.calls[0][0] == "model-b"
            assert runtime.session.prompt_messages[-1].content == "reply"
    asyncio.run(scenario())
