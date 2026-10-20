"""Tailscale listener and the local named pipe (P10-D12)."""

from __future__ import annotations

import asyncio
import ipaddress
import json
import subprocess
import threading
import time
from typing import Callable, Optional

import win32file
import win32pipe
import pywintypes

from . import keys
from .runtime import Engine, _note

CGNAT = ipaddress.ip_network("100.64.0.0/10")
PIPE_INSTANCES = 255

# P10-INTAKE: remote rejection is a pipe-mode bit on current Windows — P10-D12
PIPE_ACCESS_DUPLEX = 0x00000003
FILE_FLAG_FIRST_PIPE_INSTANCE = 0x00080000
PIPE_REJECT_REMOTE_CLIENTS = 0x00000008
ERROR_PIPE_EXISTS = (5, 183, 231)


def tailscale_ipv4() -> str:
    try:
        done = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    for line in (done.stdout or "").splitlines():
        text = line.strip()
        if text:
            return text
    return ""


def allowed_bind(host: str, port: int, listen_port: int) -> bool:
    # P10-INTAKE: only an IPv4 address inside the Tailscale CGNAT range — P10-D12
    if int(port) != int(listen_port) or int(port) == 8765:
        return False
    try:
        ip = ipaddress.ip_address(str(host))
    except ValueError:
        return False
    return ip.version == 4 and ip in CGNAT


def bind_action(previous: str, host: str, port: int, listen_port: int) -> str:
    if not allowed_bind(host, port, listen_port):
        return "refuse"
    if previous and previous == host:
        return "keep"
    return "rebind"


def create_pipe(name: str, *, first: bool = False):
    # P10-INTAKE: the first instance stays open for the life of the process — P10-D12
    open_mode = PIPE_ACCESS_DUPLEX
    if first:
        open_mode |= FILE_FLAG_FIRST_PIPE_INSTANCE
    try:
        return win32pipe.CreateNamedPipe(
            name,
            open_mode,
            PIPE_REJECT_REMOTE_CLIENTS,
            PIPE_INSTANCES,
            65536,
            65536,
            0,
            keys.pipe_security(),
        )
    except pywintypes.error as exc:
        if first and exc.winerror in ERROR_PIPE_EXISTS:
            _note("zola_phone.reject", reason="pipe_held")
        raise


def read_pipe_line(handle) -> bytes:
    buf = b""
    while b"\n" not in buf:
        piece = win32file.ReadFile(handle, 65536)[1]
        if not piece:
            break
        buf += piece
        if len(buf) > 2_000_000:
            break
    return buf.split(b"\n", 1)[0]


def _serve_client(engine: Engine, handle) -> None:
    try:
        raw = read_pipe_line(handle)
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            body = {}
        reply = json.dumps(engine.local_request(body), ensure_ascii=False).encode("utf-8") + b"\n"
        win32file.WriteFile(handle, reply)
    finally:
        try:
            win32pipe.DisconnectNamedPipe(handle)
        except pywintypes.error:
            pass
        win32file.CloseHandle(handle)


def serve_pipe(engine: Engine, stop: threading.Event, handle=None) -> None:
    name = engine.protocol["pipe_name"]
    if handle is None:
        handle = create_pipe(name, first=True)
    while not stop.is_set():
        try:
            win32pipe.ConnectNamedPipe(handle, None)
        except pywintypes.error as exc:
            if exc.winerror == 535:
                pass
            elif stop.is_set():
                break
            else:
                time.sleep(0.05)
                continue
        threading.Thread(target=_serve_client, args=(engine, handle), daemon=True).start()
        handle = create_pipe(name, first=False)
    win32file.CloseHandle(handle)


def pipe_request(name: str, body: dict) -> dict:
    handle = win32file.CreateFile(
        name,
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0,
        None,
        win32file.OPEN_EXISTING,
        0,
        None,
    )
    try:
        win32file.WriteFile(handle, (json.dumps(body, ensure_ascii=False) + "\n").encode("utf-8"))
        data = read_pipe_line(handle)
    finally:
        win32file.CloseHandle(handle)
    return json.loads(data.decode("utf-8"))


class FrameWriter:
    """One task drains the queue, so frames cannot interleave."""

    def __init__(self, send: Callable, loop: asyncio.AbstractEventLoop) -> None:
        self._send = send
        self._loop = loop
        self._queue: asyncio.Queue = asyncio.Queue()
        self._task = loop.create_task(self._drain())

    async def _drain(self) -> None:
        while True:
            frame = await self._queue.get()
            if frame is None:
                return
            await self._send(frame)

    def submit(self, frame: bytes) -> None:
        self._loop.call_soon_threadsafe(self._queue.put_nowait, frame)

    def close(self) -> None:
        self.submit(None)


def adopt_after_frame(engine: Engine, conn_id: str, submit: Callable[[bytes], None], reply: Optional[bytes]) -> bool:
    # P10-INTAKE: outbound traffic waits until this connection is the authenticated one — P10-D12
    engine.adopt_sender(conn_id, submit)
    if engine.current == conn_id and reply is not None:
        submit(reply)
        return True
    return engine.last_reason == "accept" or engine.current == conn_id


async def keepalive_loop(engine: Engine) -> None:
    while True:
        step = engine.keepalive_step()
        with engine._lock:
            sender = engine.sender
            closed = engine.last_closed_conn
            closer = engine.closer
        if step == "ping" and sender is not None:
            sender(engine.make_ping())
        elif step == "close" and closer is not None and closed:
            closer(closed)
        await asyncio.sleep(0.05)


async def handle_connection(engine: Engine, ws) -> None:
    conn_id = str(id(ws))
    loop = asyncio.get_running_loop()
    engine.loop = loop
    writer = FrameWriter(ws.send, loop)
    sockets = getattr(engine, "_sockets", None)
    if sockets is not None:
        sockets[conn_id] = ws
    try:
        async for message in ws:
            raw = message.encode("utf-8") if isinstance(message, str) else message
            reply = engine.receive(conn_id, raw)
            keep = adopt_after_frame(engine, conn_id, writer.submit, reply)
            if not keep:
                break
    finally:
        writer.close()
        engine.release_sender(conn_id)
        if sockets is not None:
            sockets.pop(conn_id, None)
        if engine.current == conn_id:
            engine.note_socket(False, reason="peer-closed", who="phone")


async def listen_forever(engine: Engine, resolve: Callable[[], str], port: int, stop: threading.Event):
    import websockets

    engine._sockets = {}

    def closer(conn_id: str) -> None:
        ws = engine._sockets.pop(conn_id, None)
        if ws is not None and engine.loop is not None:
            engine.loop.call_soon_threadsafe(lambda: ws.close())

    engine.closer = closer
    engine.loop = asyncio.get_running_loop()
    asyncio.create_task(keepalive_loop(engine))
    backoff = int(engine.protocol["timing_ms"]["connect_backoff"][0]) / 1000
    limit = engine.protocol["size_limits"]["frame_bytes"]
    current = ""
    server = None
    while not stop.is_set():
        host = resolve() or ""
        action = bind_action(current, host, port, port)
        if action == "refuse":
            engine.tailnet = False
            if server is not None:
                server.close()
                await server.wait_closed()
                server = None
                current = ""
                if engine.socket_open:
                    engine.note_socket(False, reason="network-lost", who="pc")
        elif action == "rebind":
            if server is not None:
                server.close()
                await server.wait_closed()
                if engine.socket_open:
                    engine.note_socket(False, reason="network-lost", who="pc")
            current = host
            engine.tailnet = True

            async def _handler(ws, _engine=engine):
                await handle_connection(_engine, ws)

            server = await websockets.serve(_handler, host, port, max_size=limit + 1)
        else:
            engine.tailnet = True
        await asyncio.sleep(backoff)
