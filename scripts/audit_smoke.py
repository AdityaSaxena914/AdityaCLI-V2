"""Run real tools and LM Studio inference in a disposable project.

Run from the repository: python scripts/audit_smoke.py --model MODEL_ID
Fixtures and exact model requests remain under temp/ for inspection.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from adityacli.config import AppConfig, LMStudioConfig, SecurityConfig, WorkspaceConfig
from adityacli.core.file_manager import FileManager
from adityacli.core.models import ChatResponse, OverwriteRequest, Role
from adityacli.core.parser import Parser
from adityacli.core.prompt_builder import PromptBuilder
from adityacli.core.response_parser import ResponseParser
from adityacli.core.runtime import Runtime
from adityacli.core.session_store import SessionStore
from adityacli.exceptions import ToolExecutionError
from adityacli.llm.client import LLMClient
from adityacli.prompts import load_prompt
from adityacli.providers.duckduckgo import DuckDuckGoProvider
from adityacli.services.chat_service import ChatService
from adityacli.services.command_service import CommandService
from adityacli.services.llm_service import LLMService
from adityacli.services.overwrite_service import OverwriteService
from adityacli.tools.registry import ToolRegistry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, default=Path("AUDIT_RESULTS.json"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    temporary_root = root / "temp"
    temporary_root.mkdir(exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="audit-live-", dir=temporary_root)).resolve()
    if not workspace.is_relative_to(temporary_root.resolve()):
        raise RuntimeError("Audit fixture must remain within the repository's temp directory.")
    request_dir = workspace / "requests"
    request_dir.mkdir()
    config = AppConfig(WorkspaceConfig(workspace), LMStudioConfig(timeout=120), SecurityConfig())
    client = LLMClient(config.lmstudio)
    requests = []
    report = {
        "started_at": datetime.now(UTC).isoformat(), "model": args.model,
        "workspace": str(workspace), "checks": [],
        "limits": ["One selected model; not a benchmark of every downloaded model.",
                   "Git network synchronization is not exercised against user remotes.",
                   "Live search availability and inference outputs may vary between runs."],
    }

    def check(name, operation):
        try:
            detail = operation()
        except Exception as exc:
            report["checks"].append({"name": name, "passed": False, "error": f"{type(exc).__name__}: {exc}"})
            print(f"FAIL {name}: {exc}", flush=True)
            raise
        report["checks"].append({"name": name, "passed": True, "detail": detail})
        print(f"PASS {name}", flush=True)

    def require(condition, message):
        if not condition:
            raise AssertionError(message)

    generate = client.generate
    def recorded_generate(messages, **options):
        request = {"model": client.model, "messages": [asdict(message) for message in messages], "options": options}
        requests.append(request)
        path = request_dir / f"{len(requests):02d}.json"
        path.write_text(json.dumps(request, indent=2, ensure_ascii=False), encoding="utf-8")
        response = generate(messages, **options)
        request["response"] = asdict(response)
        path.write_text(json.dumps(request, indent=2, ensure_ascii=False), encoding="utf-8")
        return response
    client.generate = recorded_generate
    registry = ToolRegistry(config, DuckDuckGoProvider())
    command_parser = Parser()
    chat = ChatService(CommandService(command_parser, registry), LLMService(client, PromptBuilder(), config),
                       OverwriteService(ResponseParser(), FileManager(config)))
    runtime = Runtime(config=config, parser=command_parser, store=SessionStore(workspace), chat_service=chat)
    runtime.add_system_prompt(load_prompt("system"))
    (workspace / "source.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

    def inference(text, expected):
        result = runtime.chat(text)
        require(isinstance(result, ChatResponse), "Expected a chat response")
        require(result.content.strip() == expected, f"Expected {expected!r}, received {result.content!r}")
        return asdict(runtime.last_response)

    exit_code = 0
    try:
        def discovery():
            models = client.list_models()
            client.select_model(args.model)
            runtime.select_model(args.model)
            require(models, "No language models discovered")
            report["catalog"] = [asdict(model) for model in models]
            return {"language_models": len(models), "selected": args.model}
        check("model_discovery", discovery)
        check("chat_inference", lambda: inference("Reply with exactly AUDIT_OK. Do not explain.", "AUDIT_OK"))

        def read():
            before = len(requests)
            result = runtime.chat("/read source.py")
            require("return a + b" in result.content and len(requests) == before, "Plain read must avoid inference")
        check("read_without_inference", read)
        check("read_with_inference", lambda: inference("/read source.py\nWhat does add(2, 3) return? Reply exactly 5.", "5"))

        def write():
            result = runtime.chat('/write {generated.json}\nReturn a JSON object with audit_value 17, literal "=== END FILE ===", and brace "{". No other keys.')
            require(isinstance(result, OverwriteRequest), "Expected a reviewable write request")
            expected = {"audit_value": 17, "literal": "=== END FILE ===", "brace": "{"}
            require(json.loads(result.files["generated.json"]) == expected, "Generated JSON differs from the requested data")
            require(not (workspace / "generated.json").exists(), "Write happened before confirmation")
            runtime.confirm_overwrite(result)
            require(json.loads((workspace / "generated.json").read_text()) == expected, "Confirmed contents differ")
        check("write_preview_and_confirmation", write)

        def edit():
            runtime.chat("/read ./generated.json")
            result = runtime.chat("/edit ./generated.json\nChange only audit_value from 17 to 23. Preserve every other field.")
            require(isinstance(result, OverwriteRequest), "Expected an edit request")
            expected = {"audit_value": 23, "literal": "=== END FILE ===", "brace": "{"}
            require(json.loads(result.files["./generated.json"]) == expected, "Edit changed unrelated fields")
            prompt = "\n".join(message["content"] for message in requests[-1]["messages"])
            require(prompt.count("=== FILE: generated.json ===") == 1, "Target was injected more than once")
            require(prompt.count("Change only audit_value from 17 to 23.") == 1, "Instruction was injected more than once")
            require(sum(message["role"] == "system" for message in requests[-1]["messages"]) == 1, "Duplicate system messages")
            require(all("Current tool task:" not in message.content for message in runtime.session.prompt_messages), "Tool contract leaked into history")
            runtime.confirm_overwrite(result)
            require(json.loads((workspace / "generated.json").read_text()) == expected, "Edit was not saved")
        check("edit_and_prompt_deduplication", edit)

        def search():
            before = len(requests)
            by_name = runtime.chat("/search generated.json")
            by_content = runtime.chat(r'/search "audit_value"\s*:\s*23')
            require("generated.json" in by_name.content and "generated.json:" in by_content.content, "Filename or content search failed")
            require(len(requests) == before, "Search unexpectedly called the model")
        check("filename_and_content_search", search)

        def web():
            result = runtime.chat("/web Python pathlib official documentation\nReturn one supplied official docs.python.org URL and a short sentence.")
            require(isinstance(result, ChatResponse) and "https://docs.python.org/" in result.content, "Missing official URL from live web answer")
            prompt = "\n".join(message["content"] for message in requests[-1]["messages"])
            require(prompt.count("Return one supplied official docs.python.org URL and a short sentence.") == 1, "Web follow-up dropped or duplicated")
            return {"answer": result.content}
        check("live_web_search_and_inference", web)

        def cancel():
            result = runtime.chat("/write {cancelled.txt}\nWrite the word CANCELLED_DRAFT exactly once.")
            require(isinstance(result, OverwriteRequest), "Expected a pending write")
            runtime.cancel_overwrite(result)
            require(not (workspace / "cancelled.txt").exists(), "Cancelled output was saved")
        check("write_cancellation", cancel)

        def remember():
            runtime.select_model("audit-context-reset")
            require(not runtime.session.read_files, "Model switch did not clear active files")
            before = len(requests)
            first = runtime.chat("/remember")
            context = list(runtime.session.prompt_messages)
            second = runtime.chat("/remember")
            require(first.content == second.content and runtime.session.prompt_messages == context, "Remember is not idempotent")
            require(len(requests) == before, "Remember unexpectedly called the model")
            return {"restored_files": len(runtime.session.read_files)}
        check("memory_restore_without_inference", remember)
        check("restored_file_inference", lambda: inference("What is audit_value in the current generated.json reference file? Reply exactly 23.", "23"))

        def continued():
            session = SessionStore(workspace)
            messages, files = session.load_state()
            require(any(message.role is Role.ASSISTANT for message in messages), "Assistant archive missing")
            require(json.loads(files["generated.json"])["audit_value"] == 23, "Saved memory is stale")
            from adityacli.core.session import Session
            restored = Session(session)
            restored.load()
            require(not restored.read_files and all(message.role is Role.SYSTEM for message in restored.prompt_messages), "Continue must await /remember")
            restored.restore_memory()
            require(json.loads(restored.read_files["generated.json"])["audit_value"] == 23, "Continue restore failed")
        check("session_continuation", continued)

        def git():
            environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
            environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
            for command in (["git", "init", "-b", "audit-main", str(workspace)],
                            ["git", "config", "user.name", "Audit Fixture"],
                            ["git", "config", "user.email", "audit@example.invalid"]):
                subprocess.run(command, cwd=workspace, env=environment, check=True, capture_output=True)
            operations = ['status --short', 'add generated.json', 'diff --staged',
                          'commit -m "Audit temporary fixture"', 'log --oneline', 'show HEAD:generated.json',
                          'branch', 'checkout -b audit-feature', 'switch audit-main',
                          'merge --ff-only audit-feature', 'rebase audit-main', 'reset --soft HEAD',
                          'restore generated.json']
            for operation in operations:
                runtime.chat("/git {" + operation + "}")
            try:
                runtime.chat("/git {show missing-audit-ref}")
            except ToolExecutionError:
                pass
            else:
                raise AssertionError("Git failure was reported as success")
            return {"local_operations": operations, "failure_propagation": True}
        check("local_git_workflows", git)

        def clear():
            runtime.clear()
            require(runtime.last_response is None and not runtime.session.read_files, "Clear left stale state")
            require(len(runtime.session.messages) == 1 and runtime.session.messages[0].role is Role.SYSTEM, "Clear lost or duplicated the system prompt")
        check("clear_session", clear)
    except Exception:
        exit_code = 1
    finally:
        client.close()
        report["finished_at"] = datetime.now(UTC).isoformat()
        report["inference_requests"] = len(requests)
        report["passed"] = not exit_code
        args.output.resolve().write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Report: {args.output.resolve()}", flush=True)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
