"""Process entry (P10-D12)."""

from __future__ import annotations

import asyncio
import ctypes
import os
import threading
import time
from ctypes import wintypes
from pathlib import Path

from .runtime import EXIT_ALREADY_RUNNING, Engine, configure_logging, forbidden_loaded
from .serve import create_pipe, listen_forever, serve_pipe, tailscale_ipv4

_MUTEX = "Local\\ZolaPhone"
_WAIT_TIMEOUT = 0x00000102
_SECRET_ENV = "ZOLA_PHONE_LAUNCH_SECRET"


def _acquire() -> bool:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel.CreateMutexW(None, False, _MUTEX)
    if not handle:
        return False
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    waited = kernel.WaitForSingleObject(handle, 0)
    if waited == _WAIT_TIMEOUT:
        kernel.CloseHandle(handle)
        return False
    return True


def _watch_parent() -> None:
    raw = os.environ.get("ZOLA_PHONE_PARENT_PID") or ""
    if not raw.isdigit():
        return
    pid = int(raw)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    while True:
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            os._exit(0)
        kernel.CloseHandle(handle)
        time.sleep(2)


def take_secret() -> str:
    # P10-INTAKE: the value stays in memory; a later tool subprocess must not inherit it — P10-D12
    return os.environ.pop(_SECRET_ENV, "")


def main() -> int:
    if not _acquire():
        return EXIT_ALREADY_RUNNING
    home = os.environ.get("HERMES_HOME") or ""
    if not home:
        return 1
    secret = take_secret()
    home_path = Path(home)
    configure_logging(home_path)
    engine = Engine(home_path, secret)
    try:
        handle = create_pipe(engine.protocol["pipe_name"], first=True)
    except Exception:
        return EXIT_ALREADY_RUNNING
    from .runtime import _note

    found = forbidden_loaded()
    _note("zola_phone.start", forbidden=",".join(found) if found else "-")
    stop = threading.Event()
    threading.Thread(target=_watch_parent, daemon=True).start()
    threading.Thread(target=serve_pipe, args=(engine, stop, handle), daemon=True).start()
    port = int(os.environ.get("ZOLA_PHONE_LISTEN_PORT") or engine.protocol["listen_port"])
    asyncio.run(listen_forever(engine, tailscale_ipv4, port, stop))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
