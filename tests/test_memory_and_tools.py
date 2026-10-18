import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from adityacli.config import AppConfig, LMStudioConfig, SecurityConfig, WorkspaceConfig
from adityacli.core.file_manager import FileManager
from adityacli.core.models import Command, OverwriteRequest, Role, Tool
from adityacli.core.session import Session
from adityacli.core.session_store import SessionStore
from adityacli.core.workspace_guard import WorkspaceGuard
from adityacli.exceptions import FileTooLargeError, InvalidPathError, InvalidSyntaxError, ToolExecutionError, ValidationError
from adityacli.tools.git import GitTool
from adityacli.tools.read import ReadTool
from adityacli.tools.search import SearchTool
from tests.test_tui import make_app


def config(root, max_size=2 * 1024 * 1024):
    return AppConfig(WorkspaceConfig(root, max_file_size=max_size), LMStudioConfig(), SecurityConfig())


def request_text(client):
    return "\n".join(message.content for message in client.calls[-1][1])


def test_switch_requires_remember_and_remember_is_idempotent(tmp_path):
    (tmp_path / "source.py").write_text("FILE_SECRET = 37")
    _, runtime, client = make_app(tmp_path)
    client.select_model("model-a")
    runtime.select_model("model-a")
    runtime.chat("OLD_SECRET = 29")
    runtime.chat("/read source.py")
    client.select_model("model-b")
    runtime.select_model("model-b")
    runtime.chat("New model question")
    assert "OLD_SECRET" not in request_text(client)
    assert "FILE_SECRET" not in request_text(client)
    assert any("OLD_SECRET" in message.content for message in runtime.session.messages)
    calls = len(client.calls)
    first = runtime.chat("/remember")
    context = list(runtime.session.prompt_messages)
    second = runtime.chat("/remember")
    assert first.content == second.content
    assert runtime.session.prompt_messages == context
    assert len(client.calls) == calls
    runtime.chat("Recall prior information")
    assert request_text(client).count("OLD_SECRET") == 1
    assert request_text(client).count("FILE_SECRET") == 1
    assert (tmp_path / ".sessions/current/memory.jsonl").exists()


def test_read_request_and_duplicate_paths_are_supplied_once(tmp_path):
    (tmp_path / "source.py").write_text("unique_content = 731")
    _, runtime, client = make_app(tmp_path)
    client.select_model("model-a")
    runtime.chat("/read {source.py source.py}\nUnique user instruction")
    text = request_text(client)
    assert text.count("unique_content = 731") == 1
    assert text.count("Unique user instruction") == 1
    assert text.count("=== FILE: source.py ===") == 1


def test_active_tool_contract_uses_initial_system_message_without_accumulation(tmp_path):
    _, runtime, client = make_app(tmp_path)
    client.select_model("model-a")
    client.output = "value = 1"
    request = runtime.chat("/write {source.py}\nCreate a file")
    assert isinstance(request, OverwriteRequest)
    messages = client.calls[-1][1]
    assert messages[0].role is Role.SYSTEM
    assert sum(message.role is Role.SYSTEM for message in messages) == 1
    assert request_text(client).count("Current tool task:") == 1
    assert all("Current tool task:" not in message.content for message in runtime.session.prompt_messages)
    runtime.cancel_overwrite(request)
    client.output = "reply"
    runtime.chat("Discuss the request")
    assert "Current tool task:" not in request_text(client)


def test_edit_uses_cached_source_once_and_saved_body_is_not_duplicated(tmp_path):
    (tmp_path / "source.py").write_text("value = 'OLD_SOURCE'")
    _, runtime, client = make_app(tmp_path)
    client.select_model("model-a")
    runtime.chat("/read source.py")
    client.output = "value = 'GENERATED_SOURCE'"
    result = runtime.chat("/edit source.py\nPerform unique change")
    assert isinstance(result, OverwriteRequest)
    assert request_text(client).count("OLD_SOURCE") == 1
    assert request_text(client).count("Perform unique change") == 1
    runtime.confirm_overwrite(result)
    client.output = "reply"
    runtime.chat("Explain the saved code")
    assert request_text(client).count("GENERATED_SOURCE") == 1
    assert "OLD_SOURCE" not in request_text(client)
    runtime.chat("/remember")
    runtime.chat("Recall saved code")
    assert request_text(client).count("GENERATED_SOURCE") == 1


def test_unchanged_file_cache_does_not_rewrite_content(tmp_path):
    store = SessionStore(tmp_path)
    store.create("model", 8192)
    session = Session(store)
    session.remember_file("file.py", "code = 1")
    session.remember_file("file.py", "code = 1")
    records = [json.loads(line) for line in (tmp_path / ".sessions/current/memory.jsonl").read_text().splitlines()]
    assert len([record for record in records if record["type"] == "file"]) == 1
    assert store.read_memory() == {"file.py": "code = 1"}


def test_legacy_session_migrates_and_waits_for_remember(tmp_path):
    root = tmp_path / ".sessions/current"
    root.mkdir(parents=True)
    chat = '\n'.join(json.dumps(message) for message in [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "legacy information"},
    ]) + "\n"
    (root / "chat.jsonl").write_text(chat)
    (root / "memory.json").write_text(json.dumps({"old.py": "legacy_code = 2"}))
    session = Session(SessionStore(tmp_path))
    session.load()
    assert len(session.messages) == 2
    assert len(session.prompt_messages) == 1
    assert session.read_files == {}
    assert session.restore_memory() == (2, 1)
    assert session.read_files == {"old.py": "legacy_code = 2"}
    assert (root / "chat.jsonl").read_text() == chat


def test_large_single_file_does_not_bypass_cache_budget(tmp_path):
    store = SessionStore(tmp_path)
    store.create("model", 8192)
    session = Session(store, max_read_tokens=2)
    session.remember_file("small.py", "ok")
    session.remember_file("large.py", "x" * 100)
    assert session.read_files == {"small.py": "ok"}
    assert store.read_memory() == {"small.py": "ok"}


@pytest.mark.parametrize("path", ["../outside.txt", "C:outside.txt", "C:\\outside.txt", "\\\\server\\share\\secret", "safe.txt:stream"])
def test_invalid_paths_fail_before_read_or_write(tmp_path, path):
    guard = WorkspaceGuard(config(tmp_path))
    with pytest.raises(InvalidPathError):
        guard.read_text(path)
    with pytest.raises(InvalidPathError):
        FileManager(config(tmp_path)).write(path, "unsafe")


def test_absolute_path_inside_workspace_is_rejected(tmp_path):
    (tmp_path / "inside.txt").write_text("data")
    with pytest.raises(InvalidPathError):
        WorkspaceGuard(config(tmp_path)).read_text(str(tmp_path / "inside.txt"))


def test_hard_links_are_excluded_from_read_write_and_search(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("OUTSIDE_SECRET")
    os.link(outside, workspace / "alias.txt")
    with pytest.raises(InvalidPathError):
        ReadTool(config(workspace)).execute(Command(Tool.READ, ["alias.txt"], ""))
    with pytest.raises(InvalidPathError):
        FileManager(config(workspace)).write("alias.txt", "changed", overwrite=True)
    search = SearchTool(config(workspace)).execute(Command(Tool.SEARCH, ["OUTSIDE_SECRET"], ""))
    assert not search.metadata.search_results
    assert outside.read_text() == "OUTSIDE_SECRET"


def directory_link(link, target):
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            raise
        quoted_link = str(link).replace("'", "''")
        quoted_target = str(target).replace("'", "''")
        subprocess.run([
            "powershell", "-NoProfile", "-NonInteractive", "-Command",
            f"New-Item -ItemType Junction -Path '{quoted_link}' -Value '{quoted_target}' | Out-Null",
        ], check=True, capture_output=True)


def test_directory_links_cannot_escape_via_read_write_or_search(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.py").write_text("OUTSIDE_SECRET")
    directory_link(workspace / "linked", outside)
    with pytest.raises(InvalidPathError):
        ReadTool(config(workspace)).execute(Command(Tool.READ, ["linked/secret.py"], ""))
    with pytest.raises(InvalidPathError):
        FileManager(config(workspace)).write("linked/new.py", "unsafe")
    search = SearchTool(config(workspace))
    assert not search.execute(Command(Tool.SEARCH, ["secret.py"], "")).metadata.search_results
    assert not search.execute(Command(Tool.SEARCH, ["OUTSIDE_SECRET"], "")).metadata.search_results
    assert not (outside / "new.py").exists()


def test_session_directory_link_is_rejected(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    directory_link(workspace / ".sessions", outside)
    with pytest.raises(InvalidPathError):
        SessionStore(workspace).clear("model", 8192)
    assert not list(outside.iterdir())


@pytest.mark.parametrize("use_rg", [False, True])
def test_search_streams_and_caps_results(tmp_path, monkeypatch, use_rg):
    if use_rg and not shutil.which("rg"):
        pytest.skip("ripgrep unavailable")
    (tmp_path / "source.py").write_text("\n".join(f"bounded_match_{i}" for i in range(200)))
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules/hidden.py").write_text("hidden_only_marker")
    if not use_rg:
        monkeypatch.setattr(shutil, "which", lambda name: None)
    search = SearchTool(config(tmp_path))
    result = search.execute(Command(Tool.SEARCH, ["bounded_match"], ""))
    assert len(result.metadata.search_results) == 50
    assert result.metadata.extra["truncated"]
    assert not search.execute(Command(Tool.SEARCH, ["hidden_only_marker"], "")).metadata.search_results


def test_search_query_cannot_become_a_ripgrep_option(tmp_path):
    (tmp_path / "source.py").write_text("literal --help marker")
    result = SearchTool(config(tmp_path)).execute(Command(Tool.SEARCH, ["--help"], ""))
    assert len(result.metadata.search_results) == 1
    assert "source.py:1:" in result.prompt


def test_search_rejects_invalid_regex(tmp_path):
    (tmp_path / "source.py").write_text("text")
    with pytest.raises((InvalidSyntaxError, ToolExecutionError)):
        SearchTool(config(tmp_path)).execute(Command(Tool.SEARCH, ["["], ""))


def test_read_enforces_size_before_filename_resolution(tmp_path):
    (tmp_path / "large.py").write_text("x" * 100)
    with pytest.raises(FileTooLargeError):
        ReadTool(config(tmp_path, max_size=20)).execute(Command(Tool.READ, ["large.py"], ""))


def init_git(path):
    if not shutil.which("git"):
        pytest.skip("git unavailable")
    environment = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    subprocess.run(["git", "init", str(path)], env=environment, capture_output=True, check=True)


def test_git_is_bound_to_launch_root_and_cannot_use_parent_repo(tmp_path):
    init_git(tmp_path)
    child = tmp_path / "child"
    child.mkdir()
    with pytest.raises(InvalidPathError):
        GitTool(config(child)).execute(Command(Tool.GIT, ["status"], ""))


def test_git_works_locally_and_rejects_external_configuration(tmp_path):
    init_git(tmp_path)
    (tmp_path / "local.py").write_text("local")
    tool = GitTool(config(tmp_path))
    status = tool.execute(Command(Tool.GIT, ["status", "--short"], ""))
    assert status.metadata.extra["return_code"] == 0
    assert "local.py" in status.prompt
    added = tool.execute(Command(Tool.GIT, ["add", "local.py"], ""))
    assert added.metadata.extra["return_code"] == 0
    diff = tool.execute(Command(Tool.GIT, ["diff", "--staged"], ""))
    assert "local.py" in diff.prompt
    with (tmp_path / ".git/config").open("a") as file:
        file.write('\n[include]\n path = ../outside-config\n')
    with pytest.raises(ValidationError, match="includes"):
        tool.execute(Command(Tool.GIT, ["status"], ""))


def test_git_rejects_absolute_diff_paths_and_linked_worktrees(tmp_path):
    init_git(tmp_path)
    tool = GitTool(config(tmp_path))
    with pytest.raises(InvalidPathError):
        tool.execute(Command(Tool.GIT, ["diff", str(tmp_path.parent / "outside")], ""))
    child = tmp_path / "child"
    child.mkdir()
    (child / ".git").write_text(f"gitdir: {tmp_path / '.git'}")
    with pytest.raises(InvalidPathError):
        GitTool(config(child)).execute(Command(Tool.GIT, ["status"], ""))


def test_launcher_uses_current_directory(tmp_path, monkeypatch):
    import adityacli.main as main
    launch = tmp_path / "launch here"
    launch.mkdir()
    observed = []
    class CaptureCLI:
        def __init__(self, runtime, client):
            observed.append(runtime.config.workspace.root)
        def run(self):
            pass
    monkeypatch.chdir(launch)
    monkeypatch.setattr(sys, "argv", ["aditya"])
    monkeypatch.setattr(main, "CLI", CaptureCLI)
    main.main()
    assert observed == [launch.resolve()]
    assert (launch / ".sessions/current/memory.jsonl").exists()
