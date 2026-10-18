"""Cross-process, reentrant locks for cooperating workspace writers."""
from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import threading
from time import monotonic, sleep

from adityacli.exceptions import ValidationError
from adityacli.core.operations import check_operation

_mutexes: dict[str, threading.RLock] = {}
_registry_lock = threading.Lock()
_held = threading.local()


@contextmanager
def file_lock(path: Path, *, timeout: float = 5.0):
    """Lock byte zero on Windows, or the open file on POSIX. Never unlink locks."""
    key = os.path.normcase(str(path.absolute()))
    with _registry_lock:
        mutex = _mutexes.setdefault(key, threading.RLock())
    deadline = monotonic() + timeout
    while not mutex.acquire(blocking=False):
        check_operation()
        if monotonic() >= deadline:
            raise ValidationError("The workspace is busy in another operation.")
        sleep(0.02)
    held = getattr(_held, "files", None)
    if held is None:
        held = _held.files = {}
    try:
        if key in held:
            yield
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a+b") as stream:
            if not stream.seek(0, os.SEEK_END):
                stream.write(b"\0")
                stream.flush()
            while True:
                check_operation()
                try:
                    if os.name == "nt":
                        import msvcrt
                        stream.seek(0)
                        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError as exc:
                    if monotonic() >= deadline:
                        raise ValidationError("This workspace is already open or busy in another process.") from exc
                    sleep(0.02)
            held[key] = stream
            try:
                yield
            finally:
                del held[key]
                if os.name == "nt":
                    import msvcrt
                    stream.seek(0)
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream, fcntl.LOCK_UN)
    finally:
        mutex.release()
