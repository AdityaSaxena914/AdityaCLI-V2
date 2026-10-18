from __future__ import annotations

from adityacli.core.models import Message, Role
from adityacli.core.session_store import SessionStore
from adityacli.core.token_counter import CharacterTokenCounter


class Session:
    """Persistent archive and separately controlled active model context."""

    def __init__(self, store: SessionStore, max_read_tokens: int = 4000) -> None:
        self._store = store
        self._messages: list[Message] = []
        self._context_messages: list[Message] = []
        self._read_files: dict[str, str] = {}
        self._active_files: dict[str, str] = {}
        self._max_read_tokens = max_read_tokens
        self._read_tokens = 0
        self._file_tokens: dict[str, int] = {}
        self._counter = CharacterTokenCounter()
        self._model: str | None = None

    @property
    def messages(self) -> list[Message]:
        return self._messages

    @property
    def prompt_messages(self) -> list[Message]:
        return self._context_messages

    @property
    def read_files(self) -> dict[str, str]:
        return self._active_files

    def activate_model(self, model: str) -> bool:
        if model == self._model:
            return False
        self._model = model
        self._context_messages = [message for message in self._messages if message.role is Role.SYSTEM]
        self._active_files.clear()
        return True

    def load(self) -> None:
        self._messages, files = self._store.load_state()
        self._context_messages = [message for message in self._messages if message.role is Role.SYSTEM]
        self._load_files(files)
        self._active_files.clear()

    def restore_memory(self) -> tuple[int, int]:
        # Replace rather than append: repeated /remember is idempotent.
        self._context_messages, files = self._store.load_state(context_only=True)
        self._load_files(files)
        self._active_files = dict(self._read_files)
        return len(self._context_messages), len(self._active_files)

    def _load_files(self, files: dict[str, str]) -> None:
        self._read_files.clear()
        self._file_tokens.clear()
        self._read_tokens = 0
        for path, content in files.items():
            self._cache(path, content)

    def add_user(self, content: str, *, context: bool = True) -> None:
        self._append(Message(Role.USER, content), context=context)

    def add_assistant(self, content: str, *, context: bool = True) -> None:
        self._append(Message(Role.ASSISTANT, content), context=context)

    def add_system(self, content: str) -> None:
        if self._messages and self._messages[0].role is Role.SYSTEM:
            if not self._context_messages:
                self._context_messages = [self._messages[0]]
            return
        self._append(Message(Role.SYSTEM, content))

    def _cache(self, path: str, content: str) -> bool:
        path = self._store.canonical_file_path(path)
        self._read_tokens -= self._file_tokens.pop(path, 0)
        self._read_files.pop(path, None)
        self._active_files.pop(path, None)
        tokens = self._counter.count_text(content)
        if tokens > self._max_read_tokens:
            return False
        self._read_files[path] = content
        self._file_tokens[path] = tokens
        self._read_tokens += tokens
        while self._read_tokens > self._max_read_tokens:
            oldest = next(iter(self._read_files))
            del self._read_files[oldest]
            self._read_tokens -= self._file_tokens.pop(oldest)
            self._active_files.pop(oldest, None)
        return True

    def remember_file(self, path: str, content: str) -> None:
        path = self._store.canonical_file_path(path)
        unchanged = self._read_files.get(path) == content
        # Build a prospective state without exposing it before persistence.
        files = dict(self._read_files)
        costs = dict(self._file_tokens)
        active = dict(self._active_files)
        total = self._read_tokens - costs.pop(path, 0)
        files.pop(path, None)
        active.pop(path, None)
        tokens = self._counter.count_text(content)
        cached = tokens <= self._max_read_tokens
        if cached:
            files[path], costs[path] = content, tokens
            total += tokens
            active[path] = content
        while total > self._max_read_tokens:
            oldest = next(iter(files))
            del files[oldest]
            total -= costs.pop(oldest)
            active.pop(oldest, None)
        records = [{"type": "forget_file", "path": removed} for removed in self._read_files.keys() - files.keys()]
        if cached:
            records.append({"type": "touch_file", "path": path} if unchanged else
                           {"type": "file", "path": path, "content": content})
        self._store.append_records(records)
        self._read_files, self._file_tokens, self._active_files = files, costs, active
        self._read_tokens = total

    def clear(self, model: str, context_window: int, *, system_prompts: list[str] | None = None) -> None:
        # Keep in-memory state intact if clearing persistent storage fails.
        messages = [Message(Role.SYSTEM, text) for text in system_prompts or []]
        if system_prompts is None:
            self._store.clear(model=model, context_window=context_window)
        else:
            self._store.clear(model=model, context_window=context_window, initial_messages=messages)
        self._messages.clear()
        self._context_messages.clear()
        self._read_files.clear()
        self._active_files.clear()
        self._file_tokens.clear()
        self._read_tokens = 0
        self._messages.extend(messages)
        self._context_messages.extend(messages)

    def _append(self, message: Message, *, context: bool = True) -> None:
        self._store.append_message(message, context=context)
        self._messages.append(message)
        if context:
            self._context_messages.append(message)
