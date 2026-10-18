# Development and operations

[README](../README.md) · [Architecture](architecture.md) · [Tools](tools.md) · [Sessions](sessions.md)

## Local setup

Use Python 3.12 or newer. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\aditya.exe --help
```

Editable installation makes source changes available to the installed command.
The application entry point is `adityacli.main:main`. Runtime dependencies are
Rich, the OpenAI SDK, `ddgs`, and Textual; pytest is the development dependency.
Git and optional ripgrep are separate programs discovered through `PATH`.

For the tested dependency snapshot, install wheels with hashes, then install the
local project without resolving dependencies or downloading build tools:

```powershell
.\.venv\Scripts\python.exe -m pip install --require-hashes --only-binary=:all: -r requirements/dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e ".[dev]"
```

`requirements/runtime.lock` pins runtime dependencies; `dev.lock` also includes
pytest, pip, setuptools, and wheel. Hashes are from PyPI release metadata and
allow wheels only. The reviewed snapshot targets Python 3.12 on Windows/Linux;
Linux CI has been configured but was not run locally. Updates require reviewing
resolved versions, wheel hashes, advisory results, and the complete test suite.

Launch from the project whose files should be accessible. The main command
accepts `--continue` and standard help; it has no `--workspace`, `--model`, or
endpoint-selection option. Model selection takes place in the UI.

## Source layout

```text
src/adityacli/
├── main.py                  Application construction and launch arguments
├── cli.py                   Textual application and interaction workers
├── config.py                Frozen configuration dataclasses
├── error_handler.py         User-facing error formatting
├── exceptions.py            Application exception types
├── core/                    Models, parsing, runtime, context, storage, file access
├── services/                Command, chat, inference, and overwrite coordination
├── llm/                     LM Studio client and model catalog records
├── tools/                   Deterministic tool implementations and registry
├── providers/               Search provider interface and ddgs adapter
├── prompts/                 Packaged system and tool instruction text
└── ui/                      Dialogs, prompt input, and unified-diff rendering
tests/                       Automated unit, integration, and headless UI checks
scripts/audit_smoke.py        Real-tool and live-inference integration checks
docs/                        Current project documentation
```

See [architecture.md](architecture.md) for component responsibilities and control flow.

## Project handoff

Read [AGENTS.md](../AGENTS.md) at the start of a coding session. Keep it updated
when code, tests, configuration, or documentation changes, recording verified
behavior, relevant files, checks, and unresolved limits. It is repository context
for development agents, separate from the application's user-chat journal.

## Configuration

Defaults are defined in [config.py](../src/adityacli/config.py) and instantiated in
[main.py](../src/adityacli/main.py). They are source-level configuration; there is
no application `.env` loader or user configuration-file loader. If changing the
endpoint or API authentication for a custom installation, change the corresponding
`LMStudioConfig` defaults or construction in the entry point.

| Setting | Default | Meaning |
| --- | --- | --- |
| `LMStudioConfig.base_url` | `http://127.0.0.1:1234/v1` | OpenAI-compatible inference base URL; native catalogs use the sibling server root |
| `LMStudioConfig.api_key` | `lm-studio` | Value passed to the SDK; replace it when the server requires a different token |
| `LMStudioConfig.model` | Empty string | Initial selection; the UI selects a catalog model |
| `LMStudioConfig.context_window` | `15000` | Local cache-sizing default, not a model-loading parameter |
| `LMStudioConfig.timeout` | `300` seconds | Total workflow deadline and maximum inference socket timeout |
| `LMStudioConfig.max_response_bytes` | `2 * 1024 * 1024` | UTF-8 response-content limit |
| `LMStudioConfig.completion_reserve_tokens` | `512` | Reserve deducted during estimated request budgeting |
| `WorkspaceConfig.root` | Resolved launch directory | File, Git, and session scope |
| `WorkspaceConfig.max_file_size` | `2 * 1024 * 1024` bytes | Text-file read and generated-write size limit |
| `WorkspaceConfig.encoding` | `utf-8` | Project text encoding |
| `ExecutionConfig.tool_timeout` | `30` seconds | Total Git/search/web budget, including validation/scans |
| `ExecutionConfig.regex_timeout` | `2` seconds | Isolated Python fallback worker budget |
| `ExecutionConfig.max_query_chars` | `8192` | Search/web query character limit |

Catalog discovery has a five-second total deadline with no automatic retries. Inference
also disables automatic SDK retries. File generation requests temperature zero;
other sampling settings are left to the server. The smoke script uses its own
120-second inference timeout.

Unsupported security relaxations and disabling overwrite confirmation raise
`ValueError` during configuration construction. Numeric limits must be positive
and finite. Ctrl+X requests cancellation; it does not undo completed side effects.
Blocking provider/HTTP work can outlive cancellation until its socket timeout,
but cannot publish a cancelled result. One outstanding call per client/provider
prevents abandoned workers from accumulating; retry after the old call closes.

Context length, quantization, and GPU offload are configured in LM Studio. The
client reads loaded-instance metadata and never sends model-loading settings.

## Automated checks

Run from the repository root with development dependencies installed. Git is
needed for the complete suite; some search checks also exercise ripgrep when it
is available.

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=temp/pytest
.\.venv\Scripts\python.exe -m compileall -q src
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/dependency_audit.py --output temp/dependency-audit.json
git diff --check
```

The dependency check sends package names/versions to OSV, never project source.
A successful scan means no known version matches at query time, not proof that
the environment has no vulnerabilities. Network failures fail the check.
The Windows/Linux CI definition is [tests.yml](../.github/workflows/tests.yml).
The latest local results and the sandbox link-fixture limitation are recorded in
[the fix report](audits/2026-10-18-fixes.md).

Pytest discovery is restricted to `tests/`; its cache lives under `temp/pytest-cache`.
A workspace-local `--basetemp` avoids reliance on restricted system temporary
directories on Windows.

| Test area | Coverage |
| --- | --- |
| Parser and response parser | Command grammar, quoting, argument counts, content preservation, and supported syntax validation |
| Runtime and registry | Dispatch, typed results, session clearing, statistics, and registered tools |
| File management and workspace | Atomic replacement, overwrite rules, file sizes, traversal, hard links, and directory links |
| Model client | Catalog fallbacks, selected model, SDK request construction, context metadata, and errors |
| Streaming | Incremental SSE delivery, final usage, disconnects, incomplete streams, truncation, archive safety, and file-draft isolation |
| Memory and prompts | Model switching, idempotent restoration, cache budgets, migration, and duplicate context |
| Headless UI | Keyboard input, model selection, incremental replies, failure/retry, previews/diffs, confirmation, ambiguity, offline recovery, and concurrent-submit prevention |
| UI controls | Mouse/keyboard/command Clear, storage and draft reset, cancel/failure preservation, model-refresh events, empty catalogs, and valid file selection |
| Audit regressions | Previously reproduced parsing, generation, storage, context, and tool error defects |

The automated suite uses test doubles or mock transports for inference. Passing
it does not prove that an arbitrary local model follows the output contract.

## Live integration checks

Start LM Studio's API server and use a language-model ID from its catalog:

```powershell
.\.venv\Scripts\python.exe scripts/audit_smoke.py --model qwen/qwen3.5-9b
```

The model shown is an example, not an installation dependency. Substitute an exact
ID available on your server. This script exercises discovery, chat, read analysis,
JSON generation/editing, prompt deduplication, search, web retrieval, cancellation,
memory restoration, continuation, local Git workflows, and session clearing.

Fixtures are created under `temp/audit-live-*`. Exact requests, response contents,
usage, timings, and finish reasons remain in numbered JSON files under each
fixture's `requests/` directory. The default report is `AUDIT_RESULTS.json`; an
alternate existing output directory can be used:

```powershell
.\.venv\Scripts\python.exe scripts/audit_smoke.py --model qwen/qwen3.5-9b --output temp/live-results.json
```

The report records pass/fail checks, selected-model catalog data, request count,
fixture location, and timestamps. The process exits nonzero on failure and stops
at the first failed workflow, so later checks are not implied to have passed.
Git fixtures are isolated from user repositories; fetch/pull/push against user
remotes are not exercised. Live inference and search can fail because of model
output or provider behavior even when application tests pass.

## Extending the application

### Add a deterministic tool

1. Define its command identity in `Tool` and its grammar/validation in `Parser`.
2. Implement `BaseTool.execute(Command) -> ToolResult` and register it in `ToolRegistry`.
3. Use `WorkspaceGuard` for project paths. Keep execution independent of model text.
4. Populate metadata rather than making downstream services infer effects from display strings.
5. Set `requires_llm=False` for direct results. For inference, provide one task
   contract and explicitly separate untrusted evidence from the user's instructions.
6. Route proposed file changes through review and confirmation instead of writing
   during generation. Add service/UI handling only when a new result type is needed.
7. Add behavior-focused tests and update the command reference and README.

### Change model or provider plumbing

Keep model discovery/transport in `LLMClient`, prompt assembly and budgeting in
`LLMService`/`PromptBuilder`, and presentation in the UI. Do not move model load
configuration into the CLI. New search providers should implement `SearchProvider`
and return the application's `SearchResult` records.

Prompt changes affect model behavior. Verify them against real generation and edit
contracts, including marker-like literals, quotes, whitespace, and preservation
of unrelated contents. Keep raw failure evidence when investigating output errors.

## Troubleshooting

| Symptom | Check or action |
| --- | --- |
| Model catalog unavailable | Start the LM Studio API server at the configured address, then Refresh |
| Downloaded model cannot infer | Load it in LM Studio or enable JIT there; verify the selected model ID remains available |
| History is visible but not used | Submit `/remember` after continuation or a model change |
| Model uses old file contents | Reread the file; cache entries are snapshots |
| Request does not fit context | Shorten it, reduce supplied files, clear the session when appropriate, or change loaded context in LM Studio |
| Generation is truncated | Reduce requested output/prompt size or adjust loaded context in LM Studio; truncated file proposals are rejected |
| Generated Python/JSON is invalid | Refine the instructions or use a model that follows the file contract; validation prevents saving the malformed proposal |
| Save reports that a file changed | Reread/regenerate and review against the current target |
| Path is rejected | Use a workspace-relative path without traversal or links; launch from the intended project directory |
| Git rejects a repository or command | Check launch root, the allowlist, linked/shared metadata, and repository configuration restrictions |
| Git commit lacks identity | Configure `user.name` and `user.email` locally outside AdityaCLI |
| Git authentication fails | Credential helpers, interactive prompts, and SSH are disabled; use external Git for those integrations |
| Web results are absent or fail | Check network/provider availability; the tool retrieves snippets and does not browse full pages |
| Session corruption is reported | Preserve a copy for investigation; complete malformed journal lines are not silently repaired |

## Contribution checks

For code changes, run checks relevant to the changed behavior, then the full
automated suite. Exercise live inference when changing prompts, SDK requests, or
model selection. Keep examples aligned with implemented commands and document
limits rather than claiming unmeasured performance or universal model correctness.
