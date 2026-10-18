# Project changes

This log records completed project changes, their purpose, verification, and
remaining limitations. New entries go first. It begins on 17 October 2026;
earlier history below is reconstructed from existing project records and is
not a complete commit history. Audit recommendations are not implementation.

## 2026-10-18 - Verified main publication

- Prepared the integrated project snapshot for the user-authorized commit and
  push to `origin/main`, including the previously uncommitted streaming work,
  audits, remediation, tests, prompts, dependency locks, and documentation.
- Fetched the destination refs and verified that remote main is an ancestor of
  the current branch. Committed the snapshot as `b572365`, fast-forwarded local
  main, and pushed normally without rewriting history. A subsequent
  `git ls-remote` confirmed main at
  `b57236558302dfdd0c5c22f9d6cf9bb54df32a81`, matching local HEAD.
- Excluded the unrelated local synopsis PDF, `.env`, sessions, virtual environment,
  caches, and temporary fixtures; retained historical audit/verification evidence.
- Updated `AGENTS.md` and this log to describe the publication scope and remove
  the stale assumption that the integrated source must remain uncommitted.
- Verification: 67 inventoried runtime/test/build files match their tested hashes;
  the prior 181-case results remain applicable. Reviewed 71 staged regular files
  and three deletions; staged whitespace passed and no high-confidence credential
  patterns were found. After the source push, tracked files were clean and only
  the excluded synopsis PDF remained untracked. Recorded this confirmed outcome
  in `AGENTS.md` and this log as a separate documentation-only update.
- Limitations remain those recorded in the remediation entry below. No fresh
  live inference, dependency scan, or GitHub/Linux CI result is implied.

## 2026-10-18 - Audit fixes and enforced change tracking

- Strengthened the `AGENTS.md` maintenance rule: update this log and the handoff
  before reporting a project task complete; record only actual verification.
- Implemented Git-native configuration validation, isolated fallback regex
  search, process deadlines/cancellation, session writer coordination and reset
  recovery, persist-before-publish session updates, protected file conflict checks,
  compile-based Python validation, early output limits, and newline-aware diffs.
- Added behavior-focused counterexamples in `tests/test_audit_fixes.py`.
- Added bounded streaming batches with immediate first output, stale-callback
  rejection, model-refresh event suppression, and visible-selection reconciliation
  before Send. Fixed the UI test to await actual selection before direct runtime
  calls. Preserved exact text line endings and external-tool lookup boundaries.
- Upgraded the project environment to pip 26.2.1 and pytest 9.1.1; updated development
  requirements. Added runtime/development wheel locks, a repeatable OSV checker,
  and Windows/Linux Python 3.12 CI with pinned action commits.
- Affected areas: `src/adityacli/{core,llm,services,tools,providers,ui}`,
  `cli.py`, `config.py`, `exceptions.py`, `main.py`, `tests/test_audit_fixes.py`,
  `tests/test_ui_controls.py`, `pyproject.toml`, `requirements/`,
  `scripts/dependency_audit.py`, `.github/workflows/tests.yml`, `README.md`,
  `AGENTS.md`, this log, and current architecture/tool/session/development docs.
- Verification: 178 cases passed in the final sandbox run; three link-fixture
  cases passed outside it using a verified new disposable path. All 181 tests
  passed across those runs (137 existing and 44 added cases). The full development
  lock passed clean hash-checked, wheel-only dependency resolution. OSV queried
  34 installed packages and returned zero matches; evidence is in
  [the dependency report](docs/audits/2026-10-18-dependencies.json).
- All 58 Python files compiled without execution. `pip check`, documentation
  links/fences, new-file whitespace checks, and normal `git diff --check` passed.
  Portable verification records source hashes and confirms that 38 historical
  inventory entries remained unchanged while 19 were modified for these fixes.
- Detailed implementation, validation, and limits: [fix report](docs/audits/2026-10-18-fixes.md).
- Limitations: no live inference because the LM Studio server was offline; no
  GitHub/Linux CI run or comparative performance benchmark. File conflicts are
  protected between cooperating writers; unrelated editor races remain possible.
  Crash recovery is not secure erasure or a universal power-loss guarantee.
  Journal compaction, pagination, watcher/index/RAG features remain proposals.
  No actual user session was cleared, no user-repository Git changes were made,
  and unrelated existing working-tree changes were preserved.

## 2026-10-17 - Change tracking and codebase audit

- Added this change log at the user's request.
- Added an `AGENTS.md` rule requiring future code, configuration, test,
  dependency, and documentation changes to update this log.
- Added [the full codebase audit](docs/audits/2026-10-17.md), its
  [portable evidence](docs/audits/2026-10-17-evidence.json), and
  [source inventory](docs/audits/2026-10-17-source-inventory.json). The report maps
  current algorithms to recommended practices for security, scale, and recovery.
- Reproduced two application security findings and eight reliability/correctness
  findings. A live OSV scan returned seven unique installed-tooling advisory
  matches; two do not apply to this Windows/Python environment and five concern
  conditional package installation/download operations. Categories are separate.
- Application source, test source, configuration, and dependencies were not
  changed. No recommended fix is recorded as implemented.
- Files changed: `changes.md`, `AGENTS.md`, and the three audit files linked above.
- Verification: 134 existing tests passed in the sandbox; three link-fixture
  setup failures passed on a targeted rerun outside the sandbox using verified
  new disposable paths. All 137 existing tests passed across those runs.
  All 52 Python files compiled without execution, `pip check` passed, and
  SHA-256 checks confirmed the 57 inventoried source/prompt/test/script files
  remained unchanged. Documentation links, Markdown fences, whitespace, and
  `git diff --check` passed under the normal repository settings.
- Limitations: no live model inference, long-session load benchmark, or
  comparative performance experiment was run. Findings remain open until fixes
  are implemented and verified. Existing unrelated working-tree changes remain.

## 2026-10-08 - Streaming and UI controls (reconstructed history)

Source: the existing `AGENTS.md`, `docs/architecture.md`,
`docs/development.md`, and historical audit records.

- Added incremental chat/read-analysis/web-summary replies. Incomplete replies
  remain visible and are excluded from saved model context. Generated file
  changes still require complete validation, preview, and confirmation.
- Corrected model-refresh selection handling and file-choice validation.
- Made confirmed Clear reset the transcript, multiline draft and edit history,
  active context, file cache, and stored session while retaining the system
  prompt and selected model. Removed the Prompt footer control; Ctrl+N remains.
- Relevant areas: `cli.py`, `llm/client.py`, `core/runtime.py`,
  `core/session.py`, `ui/conversation.py`, `ui/screens.py`, regression tests,
  and project documentation.
- Historical verification: 137 tests and recorded LM Studio/UI integration
  checks passed at that time. This is historical evidence, not a fresh claim
  about the current environment or every model.
