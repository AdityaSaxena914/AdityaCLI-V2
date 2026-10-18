# Tool reference

[README](../README.md) · [Architecture](architecture.md) · [Sessions](sessions.md) · [Development](development.md)

## Input format

Ordinary text goes to the selected model. A leading `/` selects an explicit
command. The first line contains the command and arguments; subsequent lines
contain instructions for commands that use them. Insert a newline with Ctrl+J.

```text
/read src/adityacli/main.py
Explain the dependency setup.
```

Arguments for `/write` and `/git` must be enclosed in braces. Braces are optional
for `/read`; `/edit` takes a path directly. Quote paths or Git arguments containing
spaces. Backslashes in file arguments are preserved for Windows paths, although
paths must still be relative to the workspace.

```text
/read {"folder/first file.py" "folder/second file.py"}
/write {"folder/new file.py"}
/edit "folder/existing file.py"
/git {commit -m "Describe the change"}
```

Commands are case-sensitive. Unknown commands and invalid argument counts fail
before dispatch. `/clear`, `/help`, and `/exit` are UI commands; `/remember` is
handled by the chat service. The registry contains read, write, edit, search, web,
and Git implementations.

## Command overview

| Command | Inference | Side effect |
| --- | --- | --- |
| `/read` | Only when instructions follow | Refreshes bounded file memory |
| `/search` | No | Displays matches |
| `/write` | Yes | Writes after confirmation |
| `/edit` | Yes | Replaces a file after confirmation |
| `/web` | Yes | Performs an external search |
| `/git` | No | Executes the submitted Git operation immediately |
| `/remember` | No | Replaces active context with eligible archived context |
| `/clear` | No | Replaces session storage after confirmation |
| `/help` | No | Displays help |
| `/exit` | No | Exits when idle |

## `/read`: read and analyze files

```text
/read README.md
/read {src/adityacli/main.py src/adityacli/config.py}
/read runtime
```

An exact relative file path is tried first. If it does not exist, the resolver
looks for a matching filename or filename stem, case-insensitively, in the pruned
workspace tree. Multiple matches open a selection dialog. Selection preserves the
other requested files and the original instructions.

Without instructions, contents are displayed directly and no inference occurs.
Read files enter the bounded cache when they fit its budget. Instructions on the
following lines turn the read into an analysis request:

```text
/read src/adityacli/core/session.py
Explain the difference between archived and active context.
```

Canonical paths prevent duplicate aliases from supplying the same file twice.
Refresh a file with `/read` after editing it externally; cached contents are snapshots.

## `/search`: find files or search contents

```text
/search runtime
/search TODO
/search def\s+main
/search error message
/search --literal (a+)+$
```

The complete argument is one search pattern, including spaces and regex
backslashes. Matching outer quotes are optional. The search order is:

1. For a bare name without `/`, `\`, or `:`, look for matching filenames or stems.
2. If filename matches exist, return those paths.
3. Otherwise, perform regex content search using ripgrep when available, or a
   Python regex fallback running in an isolated, killable subprocess.

Use `--literal ` before a query to search plain text without regex interpretation.
Queries are limited to 8,192 characters. Search has a 30-second total budget;
the fallback worker has a two-second limit, including startup and scanning.
Ctrl+X cancels a running request.

Content search uses smart case: a lowercase pattern is case-insensitive; a pattern
containing uppercase characters is case-sensitive. Regex capabilities depend on
the backend. A content match includes the relative path, line number, and preview.

Results are capped at 50, with a notice when additional matches are omitted.
Native line previews use a 300-column setting; the fallback limits preview text
to 300 characters. Large files, linked paths, and `.pyc`/`.pyo` files are excluded.
Both filename discovery and content scanning prune these directories:

```text
.git  .venv  venv  node_modules  __pycache__
.pytest_cache  .sessions  build  dist
```

Search uses this fixed pruning policy, not the repository's complete `.gitignore`
rules. Other hidden files and directories can be included. Search results are
displayed directly and are not retained as model evidence. Use `/read` on a result
to make its file contents available to later inference.

## `/write`: generate one file

```text
/write {examples/settings.json}
Create a JSON object with a name and an enabled boolean.
```

Exactly one target is supported. The path is validated, and its existing contents
or absence are captured before inference. The model receives the destination as
metadata and returns complete file text. `/write` generates fresh contents; use
`/edit` when the existing code must be supplied as the editing input.

The UI displays a syntax-highlighted proposal. Confirm to write or overwrite the
target, or cancel to leave it untouched. Missing parent directories are created
only during the confirmed write. Submitting the command without instructions
opens a follow-up dialog.

## `/edit`: replace one existing file

```text
/edit examples/settings.json
Change only the enabled value to false.
```

The tool reads exactly one explicit path and supplies the file as untrusted
reference data. The model is asked for the complete replacement, preserving
unrelated code and formatting. `/edit` does not apply model-generated patches.

The UI displays a unified diff before confirmation. Editing a missing file fails;
use `/write` to create a file. Omitting instructions opens a follow-up dialog.

### Generation and save rules

- File generation uses temperature zero, with no application end-marker protocol.
- Empty responses and completion-limit truncation are rejected. Python is checked
  with `compile(..., 'exec')` without execution, and JSON with `json.loads`, before preview.
- Complete outer code wrappers can be removed for code files. Markdown and plain
  text files preserve their content, including legitimate code fences.
- The default size limit is 2 MiB of encoded content. Accepted writes use an atomic
  replacement for each target. Receiving, parsing, and preview preparation enforce
  output limits before a proposal is archived or displayed. Text reads preserve
  line endings; writes retain the generated text's line endings on Windows too.
  A missing final newline is marked explicitly in the diff.
- Confirmation rechecks the target against the original snapshot. A changed,
  deleted, or newly created target causes a conflict instead of a silent overwrite.
  The check and replacement share a lock between AdityaCLI writers. An unrelated
  editor can still change the path between the final comparison and replacement.
- Generated file bodies and acceptance/cancellation receipts stay out of active
  model history. Accepted file contents update the bounded cache.

Review remains necessary. Syntax checks do not establish correctness, and formats
other than Python and JSON have no built-in syntax validator.

## `/web`: retrieve search evidence

```text
/web Python pathlib documentation
Summarize path resolution and cite the supplied official documentation URL.
```

The provider uses `ddgs` to retrieve up to five results by default. Each result
contains a title, URL, and body/snippet. The tool supplies those results to the
model with an instruction to cite only supplied URLs. Optional follow-up
instructions are appended outside the untrusted result block.

This is search-result retrieval, not a browser or a full-page crawler. Queries
leave the local machine. No-results responses are passed to the model as an
explicit lack of evidence; model answers still require verification.

## `/git`: explicit Git operations

```text
/git {status --short}
/git {diff --stat}
/git {add src/example.py}
/git {commit -m "Update example handling"}
/git {log --oneline -n 10}
```

Git requires a `.git` directory inside the launch directory. A repository in a
parent directory is not adopted. Linked worktrees and shared/external metadata
are rejected. Git must be installed and available on `PATH`.

The operation runs immediately when submitted. There is no extra confirmation
dialog for commits, branch changes, restores, resets, or network synchronization.
Git output is displayed directly; it is not sent to the model or retained as
model evidence. Nonzero exit status produces a tool execution error.

### Allowed commands and flags

Positional paths, refs, and remotes remain subject to validation and Git's own
syntax. Flags outside this table are rejected. `--` may separate path arguments.

| Subcommand | Allowed flags |
| --- | --- |
| `status` | `--short`, `--porcelain`, `--branch` |
| `diff` | `--cached`, `--staged`, `--stat`, `--name-only` |
| `log` | `--oneline`, `--graph`, `--decorate`, `-n`, `--all` |
| `show` | None |
| `branch` | `-a`, `-r`, `-d`, `-D` |
| `checkout` | `-b` |
| `switch` | `-c` |
| `add` | None |
| `restore` | `--staged` |
| `reset` | `--soft`, `--mixed` |
| `commit` | `-m`, `--amend` |
| `fetch`, `pull`, `push` | None |
| `merge` | `--no-ff`, `--ff-only` |
| `rebase` | `--continue`, `--abort`, `--skip` |

The `-c` option is allowed only as the branch-creation flag for `switch`; arbitrary
Git configuration overrides are not accepted. The application defaults `log` to
50 commits unless `-n` is supplied and caps retained output at 128 × 1024 decoded
bytes. Git validation, metadata scans, and subprocesses share a 30-second total
deadline. Ctrl+X terminates a running operation; inspect repository state after
an interruption because completed Git side effects are not rolled back.

### Isolation and identity

The wrapper disables global/system Git configuration, hooks, fsmonitor, signing,
external diffs, text conversion, and credential helpers. Repository config
includes, custom filters/merge drivers, and rebase execution steps are rejected.
Configuration policy uses Git's canonical parser with includes disabled, covering
quoted, tab-separated, case-varied, and deprecated dotted section syntax.
Network transports are restricted to HTTP(S); SSH and interactive credential
prompts are unavailable.

Configure commit identity locally using Git outside the application:

```powershell
git config --local user.name "Your Name"
git config --local user.email "you@example.com"
```

Authentication that depends on credential helpers or prompts will not work inside
this wrapper. Use external Git for operations requiring those integrations.

## Session and UI commands

`/remember` accepts no arguments. It reloads eligible archived messages and bounded
file memory for the next inference request. Repeating it does not duplicate
context or call the model.

`/clear` asks for confirmation, then replaces current session storage and clears
the visible transcript, multiline draft, input edit history, cached files, and
response statistics while retaining the system prompt and selected model. The
footer's **Clear** control and Ctrl+L perform the same reset. `/help`
shows command help. `/exit` exits when no interaction is running; Escape cancels
an open dialog. See [sessions.md](sessions.md) for retention details.
