# AdityaCLI-V2 audit — 8 October 2026

## Problem statement and proposed solution

Local coding agents can spend much of a small model's context on tool definitions,
repeated file contents, and orchestration history. Allowing model text to select
and execute tools also makes application behavior harder to control and review.

AdityaCLI uses explicit slash commands and a deterministic Python runtime for
filesystem access, search, web retrieval, Git, and session storage. LM Studio
provides chat, explanation, and file generation. A Textual interface presents
model selection, responses, file previews, and edit diffs. File changes require
confirmation. Bounded file memory and request-time prompt assembly reduce
repeated context. This audit does not establish comparative speed claims.

## Verification

The existing checkout already contained substantial changes. They were preserved
and audited in place. The initial dedicated suite passed 80 tests; the current
suite passes **115 tests**, including 35 new regression cases and the existing
headless UI checks. Dependency consistency, Python compilation, command-line
startup/help, and Git whitespace checks were also checked.
Read, code search, and Git status also passed against the actual project checkout
through the tool registry, without inference or repository mutation.

The final live run passed **14 workflow checks** using **seven inference
requests** to `qwen/qwen3.5-9b` through the configured LM Studio server. Its catalog
reported Q4_K_M quantization and a loaded context of 15,104 tokens. No model
loading settings, context length, quantization, or GPU offload were changed.

| Capability | Verification |
| --- | --- |
| Model discovery | Eight language models discovered; selected model used for actual requests |
| Chat | Exact expected response returned |
| Read | Direct read avoids inference; analysis returns the expected arithmetic result |
| Write | Generated JSON parsed correctly; no file before confirmation; confirmed contents verified |
| Edit | Requested value changed; other fields preserved; saved result verified |
| Prompt assembly | Aliased file supplied once; current instruction supplied once; one system role; tool contract does not accumulate |
| Search | Filename and regex content search; both ripgrep and Python fallback covered by automated tests |
| Web | Real provider retrieval plus model response with a supplied official documentation URL |
| Cancellation | Cancelled output is not written |
| Remember | Restoration is idempotent and makes no inference request; follow-up uses current saved file |
| Continue | Persistent archive restored; active file context waits for `/remember` |
| Git | 13 local operations in an isolated repository; nonzero exit is reported as failure |
| Clear | Cached files, conversation context, and inference statistics cleared; system prompt retained once |
| UI | Existing headless model selection, keyboard, previews, diffs, confirmation, ambiguity, offline recovery, and concurrency tests pass |

Live Git operations covered status, add, staged diff, commit with a quoted message,
log, show, branch, checkout, switch, merge, rebase, reset, and restore. They ran
against a temporary repository, not the user's checkout or remotes.

Machine-readable live results are in [AUDIT_RESULTS.json](AUDIT_RESULTS.json).
Its `workspace` field locates retained fixtures and numbered exact request/response
files. Reproduce with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=temp/audit-recheck
.\.venv\Scripts\python.exe scripts/audit_smoke.py --model qwen/qwen3.5-9b
```

## Confirmed defects fixed

| Defect | Change |
| --- | --- |
| Quoted paths and multiword Git messages split on whitespace | Quote-aware parsing that preserves Windows backslashes |
| Search rejected patterns containing spaces | Treat the complete argument as the search pattern |
| Web follow-up instructions discarded | Append them outside the untrusted result block |
| `./`, case, and separator aliases could duplicate cached files and edit inputs | Canonical workspace-relative file identity across tools, cache, and journal replay |
| Short file contents mistaken for substrings of a user request and omitted | Deduplicate by file identity rather than arbitrary content substring |
| Ambiguous read selection discarded other requested files | Preserve all arguments and instructions; repeat selection when necessary; reject invalid indices |
| Generated content lost indentation, trailing whitespace, embedded marker strings, or header-looking lines | Preserve file content; keep prose fences; restrict compatibility cleanup to outer code wrappers |
| Literal end-marker text collided with the generation protocol | Remove the marker protocol and API stop sequence; retain completion-limit detection |
| Brace counts and repeated-line heuristics rejected legitimate content | Replace them with actual Python/JSON parsing where applicable |
| A model could emit invalid Python/JSON and reach preview as if valid | Reject syntax errors before returning a file proposal |
| Saved/cancelled receipts taught the model to repeat acknowledgements as file content | Archive receipts with `context=False`; restore respects that flag |
| Files changed during inference/review could be overwritten | Capture original contents before inference and compare again before writing |
| Oversized generated content bypassed the file-size policy | Validate encoded sizes before any target is written |
| In-workspace traversal paths were accepted despite the documented policy | Reject `..` path components explicitly |
| Interrupted final journal append prevented continuation | Ignore only an incomplete final record and repair its tail before appending |
| Clear retained previous inference statistics | Reset the last response on clear |
| History trimming could leave an orphan assistant reply | Remove leading assistant messages after trimming |
| Empty completion choices caused an index error or blank success | Raise an explicit inference error; reject unsupported completion statuses |
| SDK defaults could silently repeat an inference request after failure | Disable automatic retries |
| Git nonzero exits were returned as ordinary output | Raise a tool execution error containing the exit status and output |
| Default test discovery entered old inaccessible temporary folders | Restrict discovery to `tests`; put test cache under ignored `temp/` |

The initial regression batch reproduced 23 failures before fixes. Six later
regressions reproduced additional path, size, context, response, and retry defects.
These are test cases, not a claim of 29 distinct independent defects.

## Engineering assessment

The separation between UI, runtime, deterministic tools, and inference is
appropriate. The filesystem guard and Git restrictions serve concrete boundaries;
removing them solely to reduce line count would weaken the application.

Removed unused token-counter inheritance, the unused Workspace model, the obsolete
banner/version module, and the empty preview module. Removed the fragile marker
protocol and language-independent generation heuristics. Retained the current
service boundaries instead of performing a broad rewrite during a correctness
audit. Legacy security/confirmation configuration fields remain compatibility
surface; the supported UI always enforces its strict workspace and confirmation
policy. Current behavior is documented in the README and the architecture, tools,
sessions, and development references under `docs/`; this file records the audit snapshot.

## Evidence limits

- Inference connectivity and the listed workflows work on the tested model. This
  does not establish correctness for every task or every downloaded model.
- Earlier live runs exposed a repeated acknowledgement and malformed JSON. The
  acknowledgement context was removed, file generation now requests temperature
  zero, and invalid Python/JSON is rejected before writing. Temperature zero and
  syntax validity do not prove semantic correctness.
- Git fetch/pull/push against user remotes were not exercised. Git output is
  bounded, but its subprocess execution currently has no application-level timeout.
- Token budgeting still uses a character approximation, which can underestimate
  some languages/code. LM Studio remains the final authority on context limits.
- Filesystem checks and the final content comparison do not constitute an OS
  sandbox or an atomic compare-and-swap against another concurrently writing
  process. Multi-file writes are atomic per file, not a transaction.
- Web search returned usable results despite a nonfatal certificate-store warning
  in this restricted environment. Provider availability can change.
- There is no language-independent syntax or semantic validator. Non-Python/JSON
  proposals still require review and appropriate project checks.
