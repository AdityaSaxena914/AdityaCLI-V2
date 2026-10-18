# AdityaCLI

**A terminal development assistant powered by local models in LM Studio.**

AdityaCLI combines a full-screen terminal interface with explicit commands for
reading, searching, generating, and editing project files. Python controls tool
execution and persistence. The language model supplies explanations and generated
content; file changes are previewed and saved only after confirmation.

[Getting started](#getting-started) · [Usage](#usage) · [Commands](#commands) ·
[Documentation](#documentation) · [Development](#development)

## Why AdityaCLI

Small local models have limited context and inference capacity. Tool schemas,
repeated file dumps, and orchestration history can consume resources before the
model reaches the actual development task.

AdityaCLI makes tool selection explicit. Slash commands select predictable Python
operations, while bounded file memory and request-time prompt assembly control
what reaches the model. Natural-language messages remain ordinary chat; they do
not trigger filesystem or Git operations.

This design prioritizes visible actions, reviewable changes, and local inference.
It does not rely on an autonomous planning loop or model-generated tool calls.

## Features

- **Local inference:** connect to downloaded language models served by LM Studio,
  including models available through its Just-In-Time loading feature.
- **Terminal workspace:** a Textual interface with model selection, keyboard
  controls, conversation history, file previews, and edit diffs.
- **Streaming replies:** chat and analysis text appears as LM Studio generates
  it, with Markdown rendering and final response statistics.
- **Explicit tools:** read files, search code, generate or edit one file at a time,
  retrieve web results, and execute allowlisted Git commands.
- **Review before saving:** accept or cancel proposed file contents; changes to a
  target during generation or review cause the save to be rejected.
- **Controlled context:** canonical file identities prevent duplicate tool/cache
  injection; active tool instructions do not accumulate in conversation history.
- **Session persistence:** continue visible history and explicitly restore model
  context with `/remember`.
- **Validation:** workspace path checks, file-size limits, atomic file replacement,
  and syntax checks for generated Python and JSON.

## Getting started

### Requirements

| Requirement | Purpose |
| --- | --- |
| Python 3.12 or newer | Application runtime |
| LM Studio with its API server running | Local model discovery and inference |
| A downloaded language model | Chat, analysis, and file generation |
| Git on `PATH` | Required when using `/git` |
| ripgrep (`rg`) on `PATH` | Optional; enables the native code-search backend |
| Internet access | Required for `/web` and Git network operations |

The installation examples below use PowerShell. Git and ripgrep are external
programs; installing the Python package does not install them.

### Install from a local clone

Run these commands from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

### Prepare LM Studio

1. Download a language model in LM Studio.
2. Start its API server. AdityaCLI defaults to `http://127.0.0.1:1234`.
3. Load the model in LM Studio, or enable Just-In-Time loading there.
4. Set model context length, GPU offload, and quantization in LM Studio.

AdityaCLI discovers models and reads available metadata. It does not send model
load/unload requests or change model-loading settings.

### Launch in the project you want to work on

For this repository:

```powershell
.\.venv\Scripts\aditya.exe
```

For another project, change to that directory and invoke the installed executable
by its full path, or activate this virtual environment before changing directories
and run `aditya`.

**The launch directory is the workspace.** It determines file access, Git scope,
and where session data is stored. Select a model from the dropdown beneath the
prompt; Refresh updates the catalog after changes in LM Studio.

## Usage

Read a file and ask for an explanation in the same request:

```text
/read src/adityacli/core/runtime.py
Explain how a request moves through the runtime.
```

Generate a file, inspect its preview, and confirm the write:

```text
/write {examples/greeting.py}
Create a Python script that prints a greeting from a main function.
```

Modify an existing file and review the diff:

```text
/edit examples/greeting.py
Accept the greeting name as a command-line argument. Preserve the main function.
```

Use **Ctrl+J** to insert the newline between the command and its instructions.
Submitting `/write` or `/edit` without instructions opens a follow-up dialog.
Quote paths containing spaces, for example `/write {"examples/my script.py"}`.

## Commands

| Input | Behavior | Uses inference? |
| --- | --- | --- |
| Ordinary text | Chat with the selected model | Yes |
| `/read path` | Display files and update bounded file memory | No |
| `/read path` followed by instructions | Analyze the supplied files | Yes |
| `/search pattern` | Find filenames or search file contents | No |
| `/write {path}` | Propose the complete contents of one file | Yes |
| `/edit path` | Propose a complete replacement for one existing file | Yes |
| `/web search words` | Retrieve search results and ask the model to answer | Yes |
| `/git {status}` | Execute an allowlisted Git operation | No |
| `/remember` | Restore archived context and bounded file memory | No |
| `/clear` | Clear the current session after confirmation | No |
| `/help` | Display command help | No |
| `/exit` | Exit when no interaction is running | No |

Git commands run when submitted, including commands that modify the repository
or synchronize remotes. The file-preview confirmation flow applies to `/write`
and `/edit`. See the [tool reference](docs/tools.md) for syntax and restrictions.

### Keyboard controls

| Key | Action |
| --- | --- |
| Enter | Submit the prompt |
| Ctrl+J | Insert a newline |
| Tab | Move focus between controls |
| Ctrl+N | Focus the main prompt |
| Ctrl+R | Refresh the model catalog |
| Ctrl+L | Open the clear-session confirmation |
| Ctrl+Q | Exit when idle |
| Ctrl+X | Cancel the running request |
| F1 | Show command help |
| Escape | Cancel an open dialog |

Click **Clear** in the footer or press Ctrl+L, then confirm. This empties the
conversation and prompt, including added newlines and undo history, and replaces
the saved chat and file cache with a fresh session. The selected model remains
available. Ctrl+N focuses the input; it has no separate footer item.

## Sessions and model context

`aditya` starts a fresh session and replaces the previous current session in that
workspace. To continue it, use:

```powershell
.\.venv\Scripts\aditya.exe --continue
```

Continuation restores visible conversation history. Submit `/remember` to make
eligible archived messages and cached files available to subsequent inference.
Switching models also starts fresh active context while preserving the archive;
`/remember` restores it without a separate inference call.

Sessions live in `.sessions/current/`. They can contain source code and generated
content. Cached files are snapshots; use `/read` again after external file changes.
See [sessions and context](docs/sessions.md) for storage and retention behavior.

## Workspace and data boundaries

Project file access uses workspace-relative paths and rejects absolute paths,
`..` traversal, linked paths, binary reads, and files above the configured limit.
Each accepted file write uses atomic replacement. Python and JSON proposals are
syntax-checked before preview; syntax validity does not establish correctness.
File checks and replacement share a lock between AdityaCLI writers. Unrelated
editors do not participate in that lock; a final external-write race remains.

Inference requests go to the configured LM Studio endpoint, which is local by
default. `/web` sends its query to the search provider, and Git network operations
contact their configured remotes. AdityaCLI does not provide an operating-system
sandbox. Review generated changes and run the target project's checks.

## Current scope

- One current session per workspace; `/write` and `/edit` handle one file per request.
- Chat and analysis replies stream incrementally. File drafts appear as complete,
  validated previews before confirmation.
- Context budgeting uses a character-based estimate, not the selected model's tokenizer.
- Git requires repository metadata inside the launch directory. Linked worktrees,
  shared object stores, SSH transports, hooks, and credential helpers are unsupported.
- Model output quality and live web availability depend on the selected model and provider.

## Documentation

| Document | Contents |
| --- | --- |
| [Architecture](docs/architecture.md) | System design, components, request flows, inference, and trust boundaries |
| [Tools](docs/tools.md) | Every command, examples, Git allowlist, and operational limits |
| [Sessions and context](docs/sessions.md) | Persistence, continuation, model switching, cache, and prompt budgeting |
| [Development](docs/development.md) | Source layout, configuration, testing, extension points, and troubleshooting |
| [Audit fixes](docs/audits/2026-10-18-fixes.md) | Security/reliability fixes, regression evidence, and remaining boundaries |
| [Agent context](AGENTS.md) | Current project state, working rules, and verified handoff for future coding sessions |

## Development

Install development dependencies and run the automated suite from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q --basetemp=temp/pytest
```

For an integration check using real tools and a downloaded LM Studio model:

```powershell
.\.venv\Scripts\python.exe scripts/audit_smoke.py --model qwen/qwen3.5-9b
```

Use an exact model ID available on your server. The script creates an isolated
project under `temp/`, retains request/response records, and writes
`AUDIT_RESULTS.json`. Its Git checks use a temporary repository and do not
synchronize user remotes. Full instructions are in the
[development guide](docs/development.md).
