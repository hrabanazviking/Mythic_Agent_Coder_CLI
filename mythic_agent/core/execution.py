"""Owned, cancellable I/O for synchronous harness adapters."""

__all__ = [
    "Any",
    "Callable",
    "CancellableChatClient",
    "Path",
    "ProcessResult",
    "ThreadPoolExecutor",
    "TurnCancelled",
    "cancellable_http_post",
    "dataclass",
    "is_loopback_url",
    "run_cancellable_async",
    "run_process",
    "urlsplit",
]

import asyncio
import codecs
import ipaddress
import logging
import os
import signal
import subprocess
import threading
import time
from concurrent.futures import CancelledError as futures_CancelledError
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from .runtime import TurnCancelled
from .thread_audit import LoopAffinity


def run_cancellable_async(factory: Callable[[], Any], cancel: threading.Event,
                          interval: float = 0.05) -> Any:
    """Run a coroutine factory on an event loop owned by this call, with cancellation.

    The coroutine always runs on a fresh loop owned by this call; the calling
    thread never needs (or borrows) a running loop:

    * With no running loop in this thread, ``asyncio.run`` drives the
      operation directly.
    * From inside a running event loop, the operation is offloaded to a
      single worker thread that owns its loop, so the caller never sees a
      confusing "event loop is already running" error -- the embedded call
      simply works.

    Contract:

    * Exceptions raised by the coroutine propagate to the caller UNCHANGED:
      same object, same type, same message, on both paths.
    * A set ``cancel`` event -- before the call, or from another thread
      mid-flight -- raises :class:`TurnCancelled` on the sync side once the
      owned tasks drain; the coroutine's ``finally`` blocks still run.
    * Only genuine cancellation (or the caller being interrupted while
      blocked) marks the shared ``cancel`` event.  An ordinary coroutine
      failure never poisons it: the caller owns retry policy, and a failed
      request must not look like the user pressed stop.
    """
    async def operation() -> Any:
        if cancel.is_set():
            raise TurnCancelled("Operation cancelled before execution")
        task = asyncio.create_task(factory())
        async def watch() -> None:
            while not cancel.is_set():
                await asyncio.sleep(interval)
        watcher = asyncio.create_task(watch())
        try:
            await asyncio.wait({task, watcher}, return_when=asyncio.FIRST_COMPLETED)
            if cancel.is_set():
                raise TurnCancelled("Operation cancelled by user")
            return await task
        finally:
            for owned in (task, watcher):
                if not owned.done():
                    owned.cancel()
            await asyncio.gather(task, watcher, return_exceptions=True)

    def drive() -> Any:
        # Own the event loop outright: create AND drive it on this thread.
        # LoopAffinity records the creating thread and raises
        # ThreadAffinityError if any other thread tries to drive the loop.
        loop = asyncio.new_event_loop()
        affinity = LoopAffinity()
        affinity.bind(loop)
        try:
            affinity.check()
            return loop.run_until_complete(operation())
        finally:
            loop.close()
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return drive()
    # A synchronous embedding call may arrive from an already-running event loop.
    # Construct all loop-bound resources in the owned thread, not in the caller.
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="mythic-request") as pool:
        future = pool.submit(drive)
        try:
            return future.result()
        except (TurnCancelled, asyncio.CancelledError, futures_CancelledError,
                KeyboardInterrupt, SystemExit):
            # Genuine cancellation (or the caller being interrupted while
            # blocked): propagate it to the owned operation so its watcher
            # drains promptly.  Ordinary coroutine failures must NOT mark the
            # shared event -- the caller owns retry policy, and a failed
            # request must never masquerade as a user stop.
            cancel.set()
            raise


def is_loopback_url(url: str) -> bool:
    """Return True when a provider URL targets this machine.

    Loopback endpoints (local test fixtures, llama.cpp, Ollama, and similar)
    never need a remote credential and must never be routed through an HTTP
    proxy: proxy environment alone must not be able to break or reroute
    local traffic.
    """
    try:
        host = urlsplit(url).hostname or ""
    except ValueError:
        return False
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class CancellableChatClient:
    """Retain the injectable chat.completions.create seam, with owned async I/O."""
    def __init__(self, base_url: str, api_key: str, cancel: threading.Event,
                 timeout: float, interval: float = 0.05, trust_env: bool = True) -> None:
        from types import SimpleNamespace
        self.base_url, self.api_key = base_url, api_key
        self.cancel, self.timeout, self.interval = cancel, timeout, interval
        self.trust_env = trust_env
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.embeddings = SimpleNamespace(create=lambda **kwargs: self._request("embeddings", "create", **kwargs))
        self.models = SimpleNamespace(list=lambda **kwargs: self._request("models", "list", **kwargs))

    def create(self, **kwargs: Any) -> Any:
        return self._request("chat.completions", "create", **kwargs)

    def stream_chat(self, on_chunk: Callable[[Any], None], **kwargs: Any) -> None:
        """Consume one SSE chat stream inside the owned event loop.

        Each decoded chunk is delivered to ``on_chunk`` synchronously; the
        loop (and the connection) closes only after the stream is exhausted,
        fails, or is cancelled. Cancellation raises :class:`TurnCancelled`.
        """
        async def consume():
            async with self._make_openai_client() as client:
                stream = await client.chat.completions.create(stream=True, **kwargs)
                async for chunk in stream:
                    if self.cancel.is_set():
                        raise TurnCancelled("Turn cancelled during streaming")
                    on_chunk(chunk)
        return run_cancellable_async(consume, self.cancel, self.interval)

    def _make_openai_client(self) -> Any:
        """Build the SDK client honoring this endpoint's proxy policy.

        Loopback endpoints ignore proxy environment entirely (``trust_env``
        False): a malformed ``no_proxy`` entry must never break local
        requests, and local traffic must never leave the machine.
        """
        from openai import AsyncOpenAI
        extra: dict[str, Any] = {}
        if not self.trust_env:
            # httpx2 is openai's renamed httpx fork and ships as its hard
            # dependency; plain httpx is the declared fallback.  Prefer the
            # installed one -- never hard-require a single package name.
            try:
                import httpx2 as http
            except ImportError:
                import httpx as http
            extra["http_client"] = http.AsyncClient(trust_env=False, timeout=self.timeout)
        return AsyncOpenAI(base_url=self.base_url, api_key=self.api_key,
                           max_retries=0, timeout=self.timeout, **extra)

    def _request(self, resource: str, method: str, **kwargs: Any) -> Any:
        async def request():
            async with self._make_openai_client() as client:
                endpoint = client
                for name in resource.split("."):
                    endpoint = getattr(endpoint, name)
                return await getattr(endpoint, method)(**kwargs)
        return run_cancellable_async(request, self.cancel, self.interval)


def cancellable_http_post(url: str, payload: dict[str, Any], cancel: threading.Event,
                          timeout: float, interval: float = 0.05, trust_env: bool = True) -> Any:
    async def request() -> Any:
        # See _make_openai_client: prefer httpx2 (openai's hard dep), fall
        # back to plain httpx; never hard-require a single package name.
        try:
            import httpx2 as http
        except ImportError:
            import httpx as http
        async with http.AsyncClient(timeout=timeout, trust_env=trust_env) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    return run_cancellable_async(request, cancel, interval)


@dataclass(frozen=True)
class ProcessResult:
    status: str
    returncode: int | None
    output: str
    raw_output: bytes

    def render(self) -> str:
        return f"Command status: {self.status}; exit code: {self.returncode}\n{self.output}"


class _WindowsJob:
    """Kill-on-close job owns regular descendants, including after parent exit."""
    def __init__(self, process: subprocess.Popen) -> None:
        import ctypes
        from ctypes import wintypes
        class Limits(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                        ("flags", wintypes.DWORD), ("min_working", ctypes.c_size_t),
                        ("max_working", ctypes.c_size_t), ("active", wintypes.DWORD),
                        ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                        ("scheduling", wintypes.DWORD)]
        class Counters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in (
                "read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]
        class Extended(ctypes.Structure):
            _fields_ = [("limits", Limits), ("io", Counters), ("process_memory", ctypes.c_size_t),
                        ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t),
                        ("peak_job", ctypes.c_size_t)]
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel.CreateJobObjectW.restype = wintypes.HANDLE
        kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        kernel.SetInformationJobObject.restype = wintypes.BOOL
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel.TerminateJobObject.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        self.kernel, self.handle = kernel, kernel.CreateJobObjectW(None, None)
        self.wait_handles = []
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        owned = None
        try:
            limits = Extended()
            limits.limits.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
                raise ctypes.WinError(ctypes.get_last_error())
            owned = kernel.OpenProcess(0x0100 | 0x0001, False, process.pid)
            if not owned or not kernel.AssignProcessToJobObject(self.handle, owned):
                raise ctypes.WinError(ctypes.get_last_error())
            self._resume_owned_thread(process.pid)
        except Exception:
            self.close()
            raise
        finally:
            if owned:
                kernel.CloseHandle(owned)

    def _resume_owned_thread(self, pid: int) -> None:
        """Popen closes the primary thread handle; reopen only our suspended thread."""
        import ctypes
        from ctypes import wintypes
        class ThreadEntry(ctypes.Structure):
            _fields_ = [("size", wintypes.DWORD), ("usage", wintypes.DWORD),
                        ("thread_id", wintypes.DWORD), ("owner_pid", wintypes.DWORD),
                        ("base_priority", wintypes.LONG), ("delta_priority", wintypes.LONG),
                        ("flags", wintypes.DWORD)]
        kernel = self.kernel
        kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        for name in ("Thread32First", "Thread32Next"):
            method = getattr(kernel, name)
            method.argtypes = [wintypes.HANDLE, ctypes.POINTER(ThreadEntry)]
            method.restype = wintypes.BOOL
        kernel.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenThread.restype = wintypes.HANDLE
        kernel.ResumeThread.argtypes = [wintypes.HANDLE]
        kernel.ResumeThread.restype = wintypes.DWORD
        snapshot = kernel.CreateToolhelp32Snapshot(0x00000004, 0)
        if snapshot == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            entry = ThreadEntry()
            entry.size = ctypes.sizeof(entry)
            found = kernel.Thread32First(snapshot, ctypes.byref(entry))
            while found:
                if entry.owner_pid == pid:
                    thread = kernel.OpenThread(0x0002, False, entry.thread_id)
                    if not thread:
                        raise ctypes.WinError(ctypes.get_last_error())
                    try:
                        if kernel.ResumeThread(thread) == 0xFFFFFFFF:
                            raise ctypes.WinError(ctypes.get_last_error())
                        return
                    finally:
                        kernel.CloseHandle(thread)
                entry.size = ctypes.sizeof(entry)
                found = kernel.Thread32Next(snapshot, ctypes.byref(entry))
            raise RuntimeError("Owned suspended process thread was not found")
        finally:
            kernel.CloseHandle(snapshot)

    def terminate(self) -> None:
        import ctypes
        if self.handle:
            self._retain_process_handles()
            if not self.kernel.TerminateJobObject(self.handle, 1):
                raise ctypes.WinError(ctypes.get_last_error())

    def _retain_process_handles(self) -> None:
        """Use job membership and handles, not PID ancestry or later PID lookups."""
        import ctypes
        from ctypes import wintypes
        kernel = self.kernel
        query = kernel.QueryInformationJobObject
        query.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                          wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        query.restype = wintypes.BOOL
        capacity, deadline = 64, time.monotonic() + 5
        while True:
            class ProcessIds(ctypes.Structure):
                _fields_ = [("assigned", wintypes.DWORD), ("count", wintypes.DWORD),
                            ("ids", ctypes.c_size_t * capacity)]
            info = ProcessIds()
            if query(self.handle, 3, ctypes.byref(info), ctypes.sizeof(info), None):
                break
            error = ctypes.get_last_error()
            if error != 234:
                raise ctypes.WinError(error)
            if time.monotonic() >= deadline:
                raise RuntimeError("Owned job process inventory exceeded cleanup deadline")
            capacity = max(capacity * 2, info.assigned)
        logging.getLogger(__name__).debug("Owned Windows job inventory: assigned=%s ids=%s",
                                         info.assigned, list(info.ids[:info.count]))
        kernel.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
        kernel.IsProcessInJob.restype = wintypes.BOOL
        for pid in info.ids[:info.count]:
            handle = kernel.OpenProcess(0x00100000 | 0x1000, False, pid)
            if not handle:
                error = ctypes.get_last_error()
                if error == 87:  # Process exited between inventory and handle acquisition.
                    continue
                raise ctypes.WinError(error)
            member = wintypes.BOOL()
            try:
                if not kernel.IsProcessInJob(handle, self.handle, ctypes.byref(member)):
                    raise ctypes.WinError(ctypes.get_last_error())
                if member.value:
                    logging.getLogger(__name__).debug("Retained owned Windows process %s", pid)
                    self.wait_handles.append(handle)
                    handle = None
            finally:
                if handle:
                    kernel.CloseHandle(handle)

    def wait_empty(self, timeout: float) -> None:
        """Job termination starts asynchronously; await all owned process exits."""
        import ctypes
        from ctypes import wintypes
        class Accounting(ctypes.Structure):
            _fields_ = [(name, ctypes.c_int64) for name in
                        ("user_time", "kernel_time", "period_user_time", "period_kernel_time")]
            _fields_ += [(name, wintypes.DWORD) for name in
                         ("page_faults", "total_processes", "active_processes", "terminated_processes")]
        query = self.kernel.QueryInformationJobObject
        query.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                          wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        query.restype = wintypes.BOOL
        deadline = time.monotonic() + timeout
        self.kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel.WaitForSingleObject.restype = wintypes.DWORD
        try:
            for handle in self.wait_handles:
                remaining = max(0, int((deadline - time.monotonic()) * 1000))
                result = self.kernel.WaitForSingleObject(handle, remaining)
                if result == 258:
                    raise RuntimeError("Owned Windows process did not signal termination before cleanup deadline")
                if result != 0:
                    raise ctypes.WinError(ctypes.get_last_error())
        finally:
            for handle in self.wait_handles:
                self.kernel.CloseHandle(handle)
            self.wait_handles.clear()
        while True:
            info = Accounting()
            if not query(self.handle, 1, ctypes.byref(info), ctypes.sizeof(info), None):
                raise ctypes.WinError(ctypes.get_last_error())
            if info.active_processes == 0:
                return
            if time.monotonic() >= deadline:
                raise RuntimeError("Owned Windows job did not finish termination before cleanup deadline")
            time.sleep(0.01)

    def close(self) -> None:
        for handle in self.wait_handles:
            self.kernel.CloseHandle(handle)
        self.wait_handles.clear()
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def _group_has_live_processes(group_id: int) -> bool:
    """Conservative EPERM check: a zombie-only group has already terminated."""
    try:
        result = subprocess.run(["ps", "-A", "-o", "pid=,pgid=,stat="],
                                capture_output=True, text=True, timeout=3)
        if result.returncode:
            return True
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            pid, group, state = line.split()
            if int(group) == group_id and not state.startswith("Z"):
                return True
        return False
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return True


def _signal_posix_group(group_id: int, sig: int) -> bool:
    try:
        os.killpg(group_id, sig)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        if not _group_has_live_processes(group_id):
            return False
        raise


def _stop_posix_group(process: subprocess.Popen, grace: float) -> None:
    if not _signal_posix_group(process.pid, signal.SIGTERM):
        return
    try:
        process.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        pass
    # The parent may have exited while a child ignores SIGTERM.
    _signal_posix_group(process.pid, signal.SIGKILL)


def run_process(command: str | list[str], workspace: Path, *, shell: bool = False,
                cancel: threading.Event | None = None, timeout: float = 300,
                grace: float = 1, env: dict[str, str] | None = None,
                progress: Callable[[str], None] | None = None,
                encoding: str = "utf-8") -> ProcessResult:
    """Capture complete output and reap only this process's owned group/job."""
    import math
    if not math.isfinite(timeout) or timeout <= 0 or not math.isfinite(grace) or grace <= 0:
        raise ValueError("Process timeout/grace must be finite positive numbers")
    codecs.lookup(encoding)
    cancel = cancel if cancel is not None else threading.Event()
    if cancel.is_set():
        return ProcessResult("cancelled", None, "", b"")
    # CREATE_SUSPENDED prevents children escaping before job assignment on Windows.
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | 0x00000004} if os.name == "nt" else {"start_new_session": True}
    process = subprocess.Popen(command, shell=shell, cwd=workspace, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **options)
    job = None
    chunks, reader_errors = [], []
    decoder = codecs.getincrementaldecoder(encoding)(errors="replace")
    def emit(chunk: str) -> None:
        if progress and chunk:
            try:
                progress(chunk)
            except Exception:
                # Adapter failure cannot abandon a live command or lose its capture.
                pass
    def read() -> None:
        try:
            while True:
                chunk = process.stdout.read1(65536)
                if not chunk:
                    break
                chunks.append(chunk)
                emit(decoder.decode(chunk))
            emit(decoder.decode(b"", final=True))
        except Exception as exc:
            reader_errors.append(exc)
    reader = threading.Thread(target=read, name="mythic-process-output", daemon=True)
    status = "completed"
    try:
        if os.name == "nt":
            job = _WindowsJob(process)
        reader.start()
        deadline = time.monotonic() + timeout
        while process.poll() is None:
            if cancel.is_set() or time.monotonic() >= deadline:
                status = "cancelled" if cancel.is_set() else "timed_out"
                if job:
                    job.terminate()
                else:
                    _stop_posix_group(process, grace)
                break
            time.sleep(0.02)
        process.wait(timeout=grace + 5)
        if status == "completed" and process.returncode:
            status = "failed"
    except BaseException:
        if job:
            job.terminate()
        elif os.name == "nt":
            # Assignment failed while suspended: no user code/children ran yet.
            process.kill()
        else:
            _stop_posix_group(process, grace)
        process.wait(timeout=grace + 5)
        raise
    finally:
        try:
            if job:
                try:
                    job.terminate()
                    job.wait_empty(grace + 5)
                finally:
                    job.close()
            elif os.name != "nt":
                _stop_posix_group(process, grace)
        finally:
            if reader.ident is not None:
                reader.join(timeout=grace + 5)
            if not reader.is_alive():
                process.stdout.close()
    if reader.is_alive():
        raise RuntimeError("Detached process still holds command output; owned process was stopped")
    if reader_errors:
        raise RuntimeError("Could not capture complete command output") from reader_errors[0]
    raw = b"".join(chunks)
    return ProcessResult(status, process.returncode, raw.decode(encoding, errors="replace"), raw)
