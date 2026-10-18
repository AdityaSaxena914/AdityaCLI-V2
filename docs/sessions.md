# Sessions and context

[README](../README.md) · [Architecture](architecture.md) · [Tools](tools.md) · [Development](development.md)

## Session lifecycle

Each workspace has one current session. Storage belongs to the launch directory,
not to the package installation or a global user profile.

| Action | Persistent archive | Active model context |
| --- | --- | --- |
| Launch `aditya` | Replaced with a new current session | Starts with the system prompt |
| Launch `aditya --continue` | Existing messages and cached-file records loaded | Starts with the system prompt; waits for `/remember` |
| Switch to another model | Retained | Non-system messages and active file references cleared |
| Submit `/remember` | Replayed without duplicating records | Replaced with eligible messages and bounded files |
| Confirm `/clear` | Replaced with a new current session | Cleared, then the system prompt restored |

The footer's **Clear** control and Ctrl+L open the same confirmation as `/clear`.
Confirming empties the visible transcript and the complete input document,
including blank lines, cursor position, and undo/redo history. It also resets
response statistics and cached file references. Cancellation preserves the draft,
conversation, and stored memory.

Clear prepares new metadata and a journal containing the system prompt before
switching the current directory. Preparation failures preserve old memory and
disk state. A reset intent and temporary backup support recovery if the process
stops between directory renames. Old files are deleted after commit; a cleanup
failure leaves a warning and recoverable cleanup intent for the next access.
The committed current store cannot restore the old chat through `/remember` or
`--continue`. Clear is not secure erasure. Project files and the selected model
are retained.

Starting without `--continue` discards the previous current session. The application
does not maintain a session browser, historical session directory, or automatic
backup. Continuing without an existing session starts a new one.

## Archive versus model context

`Session` maintains related but distinct state:

- **Message archive:** user messages, model responses, and file-operation receipts
  retained for visible history and persistence.
- **Active messages:** only messages eligible for subsequent model requests.
- **Remembered files:** a bounded cache of canonical file paths and their contents.
- **Active files:** cached snapshots currently available to the selected model.

A visible transcript is not the complete prompt. Plain `/read`, `/search`, and
`/git` commands are archived with `context=false`; their displayed result dumps
are not persisted as assistant messages. Read file contents can instead enter the
separate cache. Search and Git output therefore do not automatically become
evidence for a later question.

Generated write/edit responses are archived with `context=false`. Applied and
cancelled receipts use the same flag. Accepted contents enter file memory; cancelled
drafts do not. Ordinary chat and analysis responses remain eligible context.

`/remember` replays the archive's context flags and restores cached files. It
replaces active state rather than appending another copy, and makes no inference
request. Restored context is included when a later message needs the model.

## Storage layout

```text
.sessions/
├── owner.lock              CLI lifetime ownership
├── store.lock              Journal/reset coordination
├── files.lock              Cooperating proposal writers
└── current/
    ├── session.json
    └── memory.jsonl
```

`session.json` is creation metadata. It contains an ISO timestamp identifier,
creation/update timestamp fields, and startup configuration values for `model`
and `context_window`. These values are a creation snapshot, not live model
telemetry: selecting a model does not update this file. Actual loaded context and
response model identity come from LM Studio and the inference response.

`memory.jsonl` is an append-oriented event journal. New records have `v: 1`;
legacy records without a version remain readable. Every line contains one JSON
object. Multi-event cache operations use a single `batch` line so an interrupted
append cannot replay just the eviction. The following legacy-compatible examples
are illustrative:

```jsonl
{"type":"message","role":"user","content":"Explain the project","context":true,"timestamp":"2026-10-08T00:00:00+00:00"}
{"type":"message","role":"user","content":"/read src/main.py","context":false,"timestamp":"2026-10-08T00:00:01+00:00"}
{"type":"file","path":"src/main.py","content":"print('example')\n"}
{"type":"touch_file","path":"src/main.py"}
{"type":"forget_file","path":"src/main.py"}
```

| Event | Replay behavior |
| --- | --- |
| `message` | Add a role/content message; `context` controls model eligibility |
| `file` | Replace the cached contents for a canonical relative path |
| `touch_file` | Refresh the recency of an unchanged cached file |
| `forget_file` | Remove the path from the effective cache |
| `batch` | Validate all nested events, then replay the complete operation |

Messages default to context eligibility when older records omit that flag. Replay
reconstructs messages and the latest effective file state in one streaming pass.
Superseded file records remain physically in the journal until the session is
replaced. No separate `index.json` is used for the current format.

### Migration and interrupted writes

When no journal exists, the store can migrate legacy `chat.jsonl` and `memory.json`
files into `memory.jsonl`. The legacy cached-file format expected by this migration
is a direct path-to-content mapping. Existing legacy files are not modified by the
migration. The completed journal is installed using a temporary file and atomic
replacement.

The CLI acquires workspace ownership before session initialization; a second
CLI process is rejected instead of resetting the live session. Store operations
share a cross-process lock, including tail repair, replay, reset, and migration.
Lock files are retained outside `current/` so reset cannot split lock ownership.

Journal appends are flushed and synchronized before publishing memory updates.
Failed appends restore the previous length. An incomplete final record is
ignored during replay and repaired before the next append. A malformed complete
line is reported as corruption rather than silently discarded. Session metadata
uses atomic replacement. Complete malformed/unknown-version records fail closed.
Temporary `.new-*`, `.old-*`, and `reset.json` entries can exist during reset or
pending recovery. New resets wait for earlier cleanup to finish.

These are application crash-recovery mechanisms, not a guarantee against disk
failure or sudden power loss on every filesystem. File application and session
recording are separate resources: if the latter fails after a successful apply,
the error explicitly says the file was already changed and requires rereading it.

## File memory policy

The runtime sets the cache budget to one quarter of
`LMStudioConfig.context_window`. With the current default of 15,000, the cache
budget is **3,750 estimated tokens**. This local configuration sizes the cache;
it does not configure or represent the loaded model's context.

File costs use `CharacterTokenCounter`, approximately one token per four
characters. A single file larger than the cache budget is not cached. When the
total exceeds the budget, the least recently cached/touched entries are removed.
Updating a path replaces its prior contents, and unchanged files get a lightweight
touch record rather than another content record.

Paths are normalized for the platform, including case and separators on Windows.
This keeps `./src/main.py` and `src/main.py` from becoming separate cache entries.
Files are snapshots, not a watcher-backed mirror. Reread a file after an external
change to refresh the model's evidence.

Eviction changes the effective cache; it does not erase old contents from the
journal. Protect session storage as source-containing local data. `/clear` replaces
the current journal but is not a secure-erasure operation.

## Request-time context budgeting

Before inference, the client refreshes model discovery. When LM Studio reports a
loaded instance's configured context length, the inference service uses that
value. A model's maximum supported context is not substituted for its configured
loaded context.

Let `C` be that context length, `R` the configured completion reserve, and `P` the
estimated tokens in the final assembled prompt. The current policy is:

```text
prompt limit      = C - R - 256
completion budget = C - P - R
default reserve R = 512
```

The current request, system instructions, and required current file references
must fit the prompt limit. Otherwise, the request fails before inference. Older
messages are trimmed from the request copy; the archive is not rewritten. Leading
orphan assistant replies are removed after trimming. There is no automatic
summary or hidden replacement conversation.

When the loaded context is unavailable, the client omits `max_tokens` and leaves
the limit to LM Studio. The estimator is not a tokenizer and can undercount some
languages and code. Server-side context rejection remains possible. Responses
that finish because of a completion limit are rejected rather than treated as
complete file proposals.

## Practical workflow

1. Launch from the intended workspace, using `--continue` to preserve its current session.
2. Select the model. Submit `/remember` if its next request should use eligible archived context.
3. Use `/read` for the specific files needed for the task.
4. Reread files after external changes; review generated replacements before saving.
5. Use confirmed `/clear` when the archive and cache should be replaced.
