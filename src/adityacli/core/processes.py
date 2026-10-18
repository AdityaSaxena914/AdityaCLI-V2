"""Stream subprocess output with bounded buffering, deadlines, and cleanup."""
from __future__ import annotations

from collections.abc import Iterator
import os
from pathlib import Path
from queue import Empty, Full, Queue
import signal
import subprocess
import threading
from time import monotonic

from adityacli.core.operations import check_operation
from adityacli.exceptions import OperationTimeout, ToolExecutionError


def find_executable(name: str, workspace: Path) -> str | None:
    """Resolve external tools from absolute PATH entries, never implicit cwd.

    Windows otherwise searches the working directory before PATH, even with
    shell=False. Batch wrappers are excluded because Windows may invoke a shell.
    """
    suffixes = [".exe"] if os.name == "nt" else [""]
    workspace = workspace.resolve()
    for directory in os.get_exec_path():
        base = Path(directory.strip('"'))
        if not base.is_absolute():
            continue
        for suffix in suffixes:
            candidate = base / (name + suffix)
            if candidate.is_file() and os.access(candidate, os.X_OK):
                resolved = candidate.resolve()
                if not resolved.is_relative_to(workspace):
                    return str(resolved)
    return None


class _WindowsJob:
    """Kill descendants even when the original parent has already exited."""
    def __init__(self, process):
        import ctypes
        from ctypes import wintypes

        class BasicLimits(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                        ("flags", wintypes.DWORD), ("min_working", ctypes.c_size_t),
                        ("max_working", ctypes.c_size_t), ("active", wintypes.DWORD),
                        ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                        ("scheduling", wintypes.DWORD)]

        class IoCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in
                        ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [("basic", BasicLimits), ("io", IoCounters), ("process_memory", ctypes.c_size_t),
                        ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t),
                        ("peak_job", ctypes.c_size_t)]

        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.api.CreateJobObjectW.restype = wintypes.HANDLE
        self.api.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        self.api.SetInformationJobObject.restype = wintypes.BOOL
        self.api.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.api.AssignProcessToJobObject.restype = wintypes.BOOL
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]
        self.handle = self.api.CreateJobObjectW(None, None)
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)) or not self.api.AssignProcessToJobObject(self.handle, wintypes.HANDLE(process._handle)):
            error = ctypes.get_last_error()
            self.close()
            raise ctypes.WinError(error)

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def _stop_tree(process: subprocess.Popen, job=None) -> None:
    if os.name == "nt":
        if job is not None:
            job.close()
        elif process.poll() is None:
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        process.kill()
    process.wait(timeout=3)


class ProcessOutput:
    def __init__(self, args: list[str], *, cwd: Path, env: dict[str, str] | None = None,
                 timeout: float = 30.0, input_bytes: bytes | None = None) -> None:
        self.args, self.cwd, self.env = args, cwd, env
        self.timeout, self.input_bytes = timeout, input_bytes
        self.returncode: int | None = None

    def __iter__(self) -> Iterator[bytes]:
        check_operation()
        args = list(self.args)
        if not Path(args[0]).is_absolute():
            executable = find_executable(args[0], self.cwd)
            if executable is None:
                raise ToolExecutionError(f"External tool {args[0]} was not found outside the workspace on an absolute PATH.")
            args[0] = executable
        deadline = monotonic() + self.timeout
        queue: Queue[bytes | BaseException | None] = Queue(maxsize=8)
        stopped = threading.Event()
        try:
            process = subprocess.Popen(args, cwd=self.cwd, env=self.env,
                                       stdin=subprocess.PIPE if self.input_bytes is not None else subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                                       start_new_session=os.name != "nt", bufsize=0)
        except OSError as exc:
            raise ToolExecutionError(f"Unable to start {Path(self.args[0]).name}: {exc}") from exc
        job = None
        if os.name == "nt":
            try:
                job = _WindowsJob(process)
            except OSError as exc:
                process.kill()
                process.wait(timeout=3)
                if process.stdout is not None:
                    process.stdout.close()
                if process.stdin is not None:
                    process.stdin.close()
                raise ToolExecutionError(f"Cannot supervise the child process tree: {exc}") from exc

        def put(value):
            while not stopped.is_set():
                try:
                    queue.put(value, timeout=0.05)
                    return
                except Full:
                    pass

        def read():
            try:
                assert process.stdout is not None
                if self.input_bytes is not None:
                    assert process.stdin is not None
                    process.stdin.write(self.input_bytes)
                    process.stdin.close()
                while chunk := process.stdout.read(8192):
                    put(chunk)
                put(None)
            except BaseException as exc:
                put(exc)

        reader = threading.Thread(target=read, daemon=True, name="adityacli-process-output")
        reader.start()
        try:
            while True:
                check_operation()
                if monotonic() >= deadline:
                    raise OperationTimeout(f"{Path(self.args[0]).name} exceeded its {self.timeout:g}-second deadline.")
                try:
                    chunk = queue.get(timeout=min(0.05, max(0.001, deadline - monotonic())))
                except Empty:
                    continue
                if chunk is None:
                    break
                if isinstance(chunk, BaseException):
                    raise ToolExecutionError(f"Cannot read process output: {chunk}") from chunk
                yield chunk
            # stdout can close before the child exits: keep the same deadline.
            while process.poll() is None:
                check_operation()
                if monotonic() >= deadline:
                    raise OperationTimeout(f"{Path(self.args[0]).name} exceeded its execution deadline.")
                stopped.wait(0.02)
            self.returncode = process.returncode
        finally:
            stopped.set()
            try:
                _stop_tree(process, job)
            finally:
                reader.join(timeout=1)
                if process.stdout is not None:
                    process.stdout.close()
                if process.stdin is not None and not process.stdin.closed:
                    process.stdin.close()


def capture_process(args: list[str], *, cwd: Path, env: dict[str, str] | None = None,
                    timeout: float = 30.0, max_bytes: int = 128 * 1024) -> tuple[int, bytes, bool]:
    output = ProcessOutput(args, cwd=cwd, env=env, timeout=timeout)
    chunks = []
    size, truncated = 0, False
    for chunk in output:
        available = max(0, max_bytes - size)
        if available:
            chunks.append(chunk[:available])
        size += min(available, len(chunk))
        truncated |= len(chunk) > available
    return output.returncode or 0, b"".join(chunks), truncated
