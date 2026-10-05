"""Owned, cancellable I/O for synchronous harness adapters."""

import asyncio
import codecs
import os
import signal
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .runtime import TurnCancelled


def run_cancellable_async(factory: Callable[[], Any], cancel: threading.Event,
                          interval: float = 0.05) -> Any:
    """Cancel and drain the owned coroutine before closing its event loop."""
    async def operation():
        if cancel.is_set():
            raise TurnCancelled("Operation cancelled before execution")
        task = asyncio.create_task(factory())
        async def watch():
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

    def drive():
        return asyncio.run(operation())
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
        except BaseException:
            cancel.set()
            raise


class CancellableChatClient:
    """Retain the injectable chat.completions.create seam, with owned async I/O."""
    def __init__(self, base_url: str, api_key: str, cancel: threading.Event,
                 timeout: float, interval: float = 0.05):
        from types import SimpleNamespace
        self.base_url, self.api_key = base_url, api_key
        self.cancel, self.timeout, self.interval = cancel, timeout, interval
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.embeddings = SimpleNamespace(create=lambda **kwargs: self._request("embeddings", "create", **kwargs))
        self.models = SimpleNamespace(list=lambda **kwargs: self._request("models", "list", **kwargs))

    def create(self, **kwargs: Any) -> Any:
        return self._request("chat.completions", "create", **kwargs)

    def _request(self, resource: str, method: str, **kwargs: Any) -> Any:
        async def request():
            from openai import AsyncOpenAI
            async with AsyncOpenAI(base_url=self.base_url, api_key=self.api_key,
                                   max_retries=0, timeout=self.timeout) as client:
                endpoint = client
                for name in resource.split("."):
                    endpoint = getattr(endpoint, name)
                return await getattr(endpoint, method)(**kwargs)
        return run_cancellable_async(request, self.cancel, self.interval)


def cancellable_http_post(url: str, payload: dict[str, Any], cancel: threading.Event,
                          timeout: float, interval: float = 0.05):
    async def request():
        try:
            import httpx2 as http
        except ImportError:
            import httpx as http
        async with http.AsyncClient(timeout=timeout) as client:
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
    def __init__(self, process: subprocess.Popen):
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
        if self.handle and not self.kernel.TerminateJobObject(self.handle, 1):
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self) -> None:
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def _stop_posix_group(process: subprocess.Popen, grace: float) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        pass
    # The parent may have exited while a child ignores SIGTERM.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


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
    def emit(chunk):
        if progress and chunk:
            try:
                progress(chunk)
            except Exception:
                # Adapter failure cannot abandon a live command or lose its capture.
                pass
    def read():
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
        if job:
            job.close()
        elif os.name != "nt":
            _stop_posix_group(process, grace)
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
