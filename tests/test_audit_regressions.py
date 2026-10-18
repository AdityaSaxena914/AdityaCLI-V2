import json
import subprocess

import pytest

from adityacli.config import AppConfig, LMStudioConfig, SecurityConfig, WorkspaceConfig
from adityacli.core.models import Command, OverwriteRequest, PendingSelectionRequest, SearchResult, Tool
from adityacli.core.parser import Parser
from adityacli.core.response_parser import ResponseParser
from adityacli.core.session import Session
from adityacli.core.session_store import SessionStore
from adityacli.exceptions import FileTooLargeError, InvalidPathError, InvalidSyntaxError, LLMError, MalformedGenerationError, ValidationError
from adityacli.tools.git import GitTool
from adityacli.tools.web import WebTool
from tests.test_tui import make_app


@pytest.mark.parametrize(("text", "arguments"), [
    ('/git {commit -m "Fix two defects"}', ["commit", "-m", "Fix two defects"]),
    ('/write {"folder/my file.py"}', ["folder/my file.py"]),
    ('/read "folder/my file.py"', ["folder/my file.py"]),
    (r'/edit "folder\my file.py"', [r"folder\my file.py"]),
    ('/search hello world', ["hello world"]),
])
def test_argument_parsing_preserves_spaces_and_backslashes(text, arguments):
    command = Parser().parse(text)
    assert command.arguments == arguments
    Parser().validate(command)


def test_unclosed_argument_quote_is_rejected():
    with pytest.raises(InvalidSyntaxError):
        Parser().parse('/read "unfinished.py')


def test_web_includes_followup_outside_untrusted_results(tmp_path):
    class Provider:
        def search(self, query):
            return [SearchResult("Title", "https://example.com", "untrusted body")]
    config = AppConfig(WorkspaceConfig(tmp_path), LMStudioConfig(), SecurityConfig())
    result = WebTool(config, Provider()).execute(Command(Tool.WEB, ["topic"], "Compare the evidence"))
    assert result.prompt.count("Compare the evidence") == 1
    assert result.prompt.index("Compare the evidence") > result.prompt.index("END UNTRUSTED WEB DATA")


def test_alias_paths_do_not_duplicate_file_context(tmp_path):
    (tmp_path / "dir").mkdir()
    (tmp_path / "dir/source.py").write_text("UNIQUE_ALIAS_SOURCE = 1")
    _, runtime, client = make_app(tmp_path)
    client.select_model("model-a")
    runtime.chat("/read dir/source.py")
    client.output = "UNIQUE_ALIAS_SOURCE = 2"
    runtime.chat("/edit ./dir/source.py\nChange 1 to 2")
    prompt = "\n".join(message.content for message in client.calls[-1][1])
    assert prompt.count("UNIQUE_ALIAS_SOURCE = 1") == 1
    assert len(runtime.session.read_files) == 1


def test_short_file_content_is_not_mistaken_for_request_text(tmp_path):
    (tmp_path / "number.txt").write_text("1")
    _, runtime, client = make_app(tmp_path)
    client.select_model("model-a")
    runtime.chat("/read number.txt")
    runtime.chat("Explain 1 file")
    prompt = "\n".join(message.content for message in client.calls[-1][1])
    assert "=== FILE: number.txt ===\n1" in prompt


def test_ambiguous_read_preserves_other_files_and_instructions(tmp_path):
    for directory in ("one", "two"):
        (tmp_path / directory).mkdir()
        (tmp_path / directory / "source.py").write_text(f"{directory.upper()}_SOURCE = 1")
    (tmp_path / "other.py").write_text("OTHER_SOURCE = 2")
    _, runtime, client = make_app(tmp_path)
    client.select_model("model-a")
    pending = runtime.chat("/read {source other.py}\nExplain both files")
    assert isinstance(pending, PendingSelectionRequest)
    runtime.confirm_read_selection(pending, 0)
    prompt = "\n".join(message.content for message in client.calls[-1][1])
    assert "OTHER_SOURCE = 2" in prompt
    assert prompt.count("Explain both files") == 1
    assert "other.py" in runtime.session.prompt_messages[-2].content


@pytest.mark.parametrize("body", [
    'print("{")',
    'marker = "=== END FILE ==="',
    '    indented text  \n\n',
    'text\n=== FILE: example ===\nbody',
    "\n".join(["one", "two", "three", "four", "five", "six"] * 4),
])
def test_generated_content_is_preserved(body):
    parser = ResponseParser()
    assert parser.parse_write_response(body, ["output.txt"])["output.txt"] == body
    assert parser.parse_edit_response(body) == body


def test_marker_like_data_is_preserved_without_a_sentinel_protocol():
    body = "literal text\n=== END FILE ===\n"
    assert ResponseParser().parse_edit_response(body, "output.txt") == body


def test_file_prompts_do_not_request_collision_prone_markers():
    from adityacli.prompts import load_prompt
    assert all("=== END FILE ===" not in load_prompt(name) for name in ("system", "write", "edit"))


@pytest.mark.parametrize("path", ["output.md", "output.txt"])
def test_fences_are_preserved_in_prose_files(path):
    body = "```python\nprint('example')\n```\n"
    parser = ResponseParser()
    assert parser.parse_write_response(body, [path])[path] == body
    assert parser.parse_edit_response(body, path) == body


@pytest.mark.parametrize(("path", "content"), [
    ("bad.json", '{"key": 1} extraneous output'),
    ("bad.py", "def unfinished("),
])
def test_invalid_source_is_rejected_before_preview(path, content):
    with pytest.raises(MalformedGenerationError):
        ResponseParser().parse_write_response(content, [path])
    with pytest.raises(MalformedGenerationError):
        ResponseParser().parse_edit_response(content, path)


def test_unclosed_code_fence_is_rejected():
    with pytest.raises(MalformedGenerationError):
        ResponseParser().parse_edit_response("```python\nprint('unfinished')")


def test_generation_does_not_stop_at_literal_marker(tmp_path):
    _, runtime, client = make_app(tmp_path)
    client.select_model("model-a")
    client.output = 'marker = "=== END FILE ==="'
    result = runtime.chat("/write {marker.py}\nDefine the literal marker")
    assert isinstance(result, OverwriteRequest)
    assert result.files["marker.py"] == client.output
    assert client.calls[-1][2].get("stop") is None
    assert client.calls[-1][2]["temperature"] == 0.0


def test_file_receipts_do_not_teach_the_model_to_repeat_acknowledgements(tmp_path):
    _, runtime, client = make_app(tmp_path)
    client.select_model("model-a")
    client.output = "value = 1"
    accepted = runtime.chat("/write {source.py}\nCreate a file")
    runtime.confirm_overwrite(accepted)
    cancelled = runtime.chat("/write {cancelled.py}\nCreate another file")
    runtime.cancel_overwrite(cancelled)
    runtime.chat("/remember")
    assert any("Applied changes" in message.content for message in runtime.session.messages)
    assert all("Applied changes" not in message.content and "Cancelled changes" not in message.content
               for message in runtime.session.prompt_messages)


@pytest.mark.parametrize("operation", ["edit", "write"])
def test_confirm_rejects_file_changed_during_generation(tmp_path, operation):
    path = tmp_path / "source.py"
    path.write_text("original = 1")
    _, runtime, client = make_app(tmp_path)
    client.select_model("model-a")
    generate = client.generate
    def change_during_generation(*args, **kwargs):
        path.write_text("external = 2")
        return generate(*args, **kwargs)
    client.generate = change_during_generation
    client.output = "generated = 3"
    command = "/edit source.py" if operation == "edit" else "/write {source.py}"
    result = runtime.chat(command + "\nUpdate the file")
    assert isinstance(result, OverwriteRequest)
    with pytest.raises(ValidationError, match="changed"):
        runtime.confirm_overwrite(result)
    assert path.read_text() == "external = 2"


def test_clear_resets_inference_metadata(tmp_path):
    _, runtime, client = make_app(tmp_path)
    client.select_model("model-a")
    runtime.chat("hello")
    assert runtime.last_response is not None
    runtime.clear()
    assert runtime.last_response is None
    assert runtime.response_stats is None


def test_partial_last_journal_record_recovers_before_append(tmp_path):
    store = SessionStore(tmp_path)
    store.create("model", 8192)
    session = Session(store)
    session.add_system("system")
    journal = tmp_path / ".sessions/current/memory.jsonl"
    with journal.open("ab") as file:
        file.write(b'{"type":"message","content":"partial')
    restored = Session(store)
    restored.load()
    restored.add_user("after recovery")
    messages, _ = store.load_state()
    assert [message.content for message in messages] == ["system", "after recovery"]
    assert all(json.loads(line) for line in journal.read_text().splitlines())


def test_git_reports_nonzero_exit_as_failure(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    config = AppConfig(WorkspaceConfig(tmp_path), LMStudioConfig(), SecurityConfig())
    from adityacli.exceptions import ToolExecutionError
    with pytest.raises(ToolExecutionError):
        GitTool(config).execute(Command(Tool.GIT, ["show", "missing-ref"], ""))


def test_traversal_is_rejected_even_when_it_returns_inside_workspace(tmp_path):
    from adityacli.core.workspace_guard import WorkspaceGuard
    with pytest.raises(InvalidPathError):
        WorkspaceGuard(tmp_path).resolve("dir/../file.py")


def test_oversized_generated_file_is_rejected_before_write(tmp_path):
    from adityacli.core.file_manager import FileManager
    config = AppConfig(WorkspaceConfig(tmp_path, max_file_size=4), LMStudioConfig(), SecurityConfig())
    with pytest.raises(FileTooLargeError):
        FileManager(config).write("file.txt", "12345")
    assert not (tmp_path / "file.txt").exists()


def test_context_trim_does_not_keep_an_orphan_assistant_reply():
    from adityacli.core.context_manager import ContextManager
    from adityacli.core.models import Message, Role
    messages = [Message(Role.SYSTEM, "system"), Message(Role.USER, "old" * 100),
                Message(Role.ASSISTANT, "orphan reply"), Message(Role.USER, "current")]
    trimmed = ContextManager(16).trim(messages)
    assert trimmed == [messages[0], messages[-1]]


@pytest.mark.parametrize("choices", [[], [{"message": {"content": None}, "finish_reason": "stop"}]])
def test_empty_inference_response_is_reported_as_an_error(choices):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from adityacli.llm.client import LLMClient
    from adityacli.core.models import Message, Role
    client = LLMClient(LMStudioConfig(model="fixture"))
    client.close()
    client._client = Mock()
    parsed = [SimpleNamespace(message=SimpleNamespace(**item["message"]), finish_reason=item["finish_reason"]) for item in choices]
    client._client.chat.completions.create.return_value = SimpleNamespace(model="fixture", choices=parsed, usage=None)
    with pytest.raises(LLMError):
        client.generate([Message(Role.USER, "hello")])


def test_inference_does_not_silently_retry_requests():
    from adityacli.llm.client import LLMClient
    client = LLMClient(LMStudioConfig())
    try:
        assert client._client.max_retries == 0
    finally:
        client.close()
