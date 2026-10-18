# AdityaCLI project context

This is the durable handoff for coding agents working in this repository.
Read it and [changes.md](changes.md) at the start of each session, then inspect
the relevant source files.

## Working rules

- Keep responses formal, concise, factual, and task-focused. No praise or filler.
- Update this file whenever project code, configuration, tests, or documentation
  changes. Record final behavior, relevant files, verification, and unresolved
  limitations. Replace stale facts instead of accumulating a long activity log.
- Maintain [changes.md](changes.md) for every project code, configuration, test,
  dependency, or documentation change. Add a dated entry describing what changed,
  why, affected files, verification actually performed, and unresolved limitations.
  Record completed changes separately from audit findings and proposed work;
  never describe a recommendation as implemented. Preserve earlier entries and
  label any history reconstructed from older project records. Keep credentials,
  user chats, and private source excerpts out of the log.
- Before reporting a project task complete, update `changes.md` and this handoff
  with the final result and checks actually run. A task is not complete while
  its change-log entry is missing or describes unverified work as finished.
- Preserve unrelated working-tree changes. The integrated publication snapshot
  includes the earlier audit, documentation rewrite, streaming implementation,
  and remediation; inspect Git status to identify any subsequent local changes.
- Keep LM Studio context length, GPU offload, quantization, and model loading
  under LM Studio's control. Do not add an Ollama integration.
- Preserve deterministic tool contracts, workspace validation, and explicit
  review/confirmation for generated file changes.
- Never record credentials, user chat contents, or private source excerpts here.
  Application chat memory belongs in its workspace-local session storage.
- Do not update global assistant memory without an explicit user request.

## Project and design

AdityaCLI is a Python 3.12+ terminal development assistant using Textual and
local LM Studio inference. Slash commands select Python tools; the model does
not autonomously invoke tools. See [README.md](README.md) and
[docs/architecture.md](docs/architecture.md) for the system design.

| Area | Current implementation |
| --- | --- |
| Entry point and UI | `src/adityacli/main.py`, `cli.py`, `ui/conversation.py`, `ui/screens.py` |
| Request coordination | `core/runtime.py`, `services/chat_service.py`, `services/llm_service.py` |
| Inference | `llm/client.py`, `llm/models.py`; native model catalogs with compatibility fallbacks; OpenAI-compatible completions |
| Prompts | `core/prompt_builder.py`, `prompts/*.txt`; one system message, request-scoped tool contract, canonical file references |
| Sessions | `core/session.py`, `core/session_store.py`; archive separated from active model context |
| Tools | `/read`, `/search`, `/write`, `/edit`, `/web`, `/git`, `/remember`; see `docs/tools.md` |
| Generated files | Complete proposals, supported syntax validation, preview/diff, confirmation, changed-target checks, atomic replacement |

## Established behavior

- The launch directory is the workspace. `aditya --continue` restores visible
  archived history; `/remember` restores eligible model context and file cache.
- Session data is under `.sessions/current/`: `session.json` and `memory.jsonl`.
  Older `chat.jsonl` and `memory.json` are migration inputs.
- Model switches clear active context while retaining archived history.
  Refreshing the same selected model must preserve context and response metadata.
- Chat, read analysis, and web summaries stream into one Markdown message.
  Incomplete streams remain visibly marked and are excluded from saved context.
  `/write` and `/edit` collect complete output before validation and preview.
- A confirmed Clear must empty the transcript, draft including newlines and
  undo history, active context, cached files, and old session records. It retains
  the system prompt and selected model. Cancel preserves existing state.
- The Prompt footer item is removed; Ctrl+N remains the input-focus shortcut.
- Documentation is maintained in `docs/architecture.md`, `tools.md`,
  `sessions.md`, and `development.md`. Historical audit evidence is in
  `AUDIT_REPORT.md` and `AUDIT_RESULTS.json`.

## Current change: audit remediation (2026-10-18)

- [Fix report](docs/audits/2026-10-18-fixes.md) maps S1-S2 and R1-R8 to
  implementation, checks, and remaining boundaries. The 17 October audit,
  evidence, and inventory remain historical; do not overwrite their baseline.
- Git uses its native config parser with includes disabled. Fallback regex
  matching runs in an isolated, killable worker; `/search --literal ...` is
  supported. External Git/ripgrep executables resolve from absolute PATH entries
  outside the workspace, avoiding Windows' implicit current-directory search.
- CLI initialization has a workspace ownership lease. Session operations use
  cross-process locks and versioned records. Cache batches use one journal line;
  persistence precedes memory publication. Clear prepares the system prompt and
  replacement before switching, with reset intent/backup recovery.
- File proposals use locked expected-content checks after staging, compile-based
  Python validation without execution, early receive/preview/write size checks,
  and newline-aware diffs. Reads/writes preserve received line endings.
- Default deadlines: workflow 300 seconds, catalog 5, Git/search/web 30, fallback
  worker 2. Ctrl+X cancels requests. Completed side effects are not rolled back.
  Network workers can outlive cancellation until socket return; one outstanding
  call per client/provider prevents accumulation.
- Streams show the first delta immediately and batch later Markdown updates at
  50 ms through a bounded queue. Late callbacks are discarded. Programmatic
  refresh events cannot act as model switches; Send reconciles visible selection.
- Unsupported security relaxations and invalid numeric limits fail at config
  construction. LM Studio loading settings remain controlled by LM Studio.
- Upgraded project tooling to pip 26.2.1 and pytest 9.1.1. Added hash-pinned wheel
  locks, a repeatable OSV checker, and Windows/Linux Python 3.12 CI. The fresh
  [dependency scan](docs/audits/2026-10-18-dependencies.json) returned no matches
  across 34 installed packages. This does not prove absence of vulnerabilities.
- Verification: 178 tests passed in the sandbox; the three link-safety cases
  passed on a targeted run outside it using verified disposable paths. All 181
  tests (137 existing plus 44 added cases) passed across these final runs. The
  development lock passed a clean hash-checked, wheel-only dependency resolution.
  All 58 Python files compiled without execution; `pip check`, documentation
  links/fences, new-file whitespace checks, and normal `git diff --check` passed.
  [Verification JSON](docs/audits/2026-10-18-verification.json) preserves counts
  and source hashes; 38 of the 57 historical inventory entries remain unchanged.
  CI is configured but has not run on GitHub/Linux in this task.
- Important boundary: expected-file checks protect cooperating AdityaCLI writers;
  unrelated editors retain a final comparison/replacement race. Storage recovery
  is not a universal power-loss guarantee or secure erasure. Journal compaction,
  transcript pagination, cache watchers, exact tokenization, and RAG are proposed.
- LM Studio's server refused the catalog connection, so no live inference is
  claimed. During remediation, no actual user-session Clear, user-repository
  staging/commits, or Git remote operations were performed.

## Current change: verified main publication (2026-10-18)

- The user explicitly authorized committing the integrated project and pushing
  to `origin/main`. Committed the integrated snapshot as `b572365`, fast-forwarded
  local main, and pushed it normally. `git ls-remote` confirmed remote main at
  `b57236558302dfdd0c5c22f9d6cf9bb54df32a81`; local main matched that hash.
- Publication includes the implementation, tests, prompts, dependency locks,
  CI definition, audits, and project documentation. The unrelated local synopsis
  PDF, `.env`, session data, virtual environment, and temporary fixtures are
  excluded. Existing historical audit/verification evidence is preserved.
- Verified that all 67 runtime/test/build files covered by the remediation
  inventory still match their tested hashes. Publication changes only the
  handoff/change log; the 181-case validation remains applicable. Staged content
  and whitespace checks passed, with no high-confidence credential matches.
  Tracked files were clean after the source push; only the excluded local
  synopsis PDF remained untracked. Remote CI results have not been checked.

## UI controls notes

- In Textual 8.2.8, `Select.NULL` is the empty value; `Select.BLANK` is an
  inherited boolean. Ignore empty/stale model events, and use public clear.
- File selection must accept only real valid integer indexes, including 0.
- Clear prepares disk state before changing memory. An interrupted directory
  switch is recovered from `reset.json`; post-commit cleanup can retain an old
  directory temporarily. Do not remove reset/lock files while the CLI is open.

## Verification and operation

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=temp/pytest
.\.venv\Scripts\python.exe -m compileall -q src
.\.venv\Scripts\python.exe -m pip check
git diff --check
```

All **181 tests** passed across the final sandbox run (178) and targeted link-test
rerun (3) on 2026-10-18; see the fix report for the fixture limitation. Earlier live
streaming verification with `qwen/qwen3.5-9b` established 80 text chunks, one
final reply, completion metadata, and read-analysis streaming. Those live
checks could not be rerun with the server offline and do not cover every installed model.
Model/server state must be rechecked when needed.

Use disposable workspaces under `temp/` for integration checks. Do not clear
the user's actual session to test Clear. Restart an already-running CLI to load
source changes. Keep verification commands and limitations in
[docs/development.md](docs/development.md).
