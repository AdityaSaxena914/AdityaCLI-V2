"""Bounded operations shared by tools, inference, and UI cancellation."""
from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar, copy_context
from functools import wraps
from queue import Empty, Queue
import threading
from time import monotonic
from typing import TypeVar

from adityacli.exceptions import OperationCancelled, OperationTimeout

T = TypeVar("T")
_current: ContextVar[Operation | None] = ContextVar("adityacli_operation", default=None)


class Operation:
    def __init__(self, timeout: float = 300.0, *, parent: Operation | None = None) -> None:
        self.deadline = min(monotonic() + timeout, parent.deadline) if parent else monotonic() + timeout
        self.cancelled = parent.cancelled if parent else threading.Event()

    def cancel(self) -> None:
        self.cancelled.set()

    def check(self) -> None:
        if self.cancelled.is_set():
            raise OperationCancelled("Operation cancelled; no incomplete reply was saved.")
        if monotonic() >= self.deadline:
            raise OperationTimeout("Operation exceeded its execution deadline.")

    @property
    def remaining(self) -> float:
        self.check()
        return max(0.001, self.deadline - monotonic())

    @contextmanager
    def activate(self):
        token = _current.set(self)
        try:
            self.check()
            yield self
        finally:
            _current.reset(token)

    def run_io(self, function: Callable[[], T], *, interrupt: Callable[[], None]) -> T:
        """Bound a blocking transport call; abandoned work cannot publish a result.

        Transport close is attempted off the UI thread. The caller must bound
        transport timeouts and allow at most one outstanding call per client.
        """
        result: Queue[tuple[bool, object]] = Queue(maxsize=1)
        context = copy_context()

        def worker():
            try:
                result.put((True, context.run(function)))
            except BaseException as exc:
                result.put((False, exc))

        threading.Thread(target=worker, daemon=True, name="adityacli-transport").start()
        try:
            while True:
                self.check()
                try:
                    success, value = result.get(timeout=min(0.05, self.remaining))
                except Empty:
                    continue
                self.check()
                if not success:
                    raise value  # type: ignore[misc]
                return value  # type: ignore[return-value]
        except (OperationCancelled, OperationTimeout):
            threading.Thread(target=interrupt, daemon=True, name="adityacli-close").start()
            raise


def current_operation() -> Operation | None:
    return _current.get()


def check_operation() -> None:
    if operation := current_operation():
        operation.check()


def bounded_tool(function):
    """Include validation, directory traversal, and all process batches in one budget."""
    @wraps(function)
    def run(self, *args, **kwargs):
        with Operation(self._config.execution.tool_timeout, parent=current_operation()).activate():
            return function(self, *args, **kwargs)
    return run
