"""Synthetic phone for intake checks. Unittest does not collect this file.

Keys are generated under --home. This process never reads the live PC key.

Commands after pairing, one per line:
  text PROVIDER BODY
  notification PACKAGE KEY TIMESTAMP
  ping answer|silent
  read on-time|late|never
  bad unsigned|bad-signature|unknown-key|wrong-device|replay|stale|version|malformed|half-open
  second
  late-revision PROVIDER
  duplicate PROVIDER
  out-of-order PROVIDER
  exhausted PROVIDER
  oversize PROVIDER
  separator
  quit
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from zola_phone import wire

COMMANDS = (
    "text",
    "notification",
    "ping",
    "read",
    "bad",
    "second",
    "late-revision",
    "duplicate",
    "out-of-order",
    "exhausted",
    "oversize",
    "separator",
    "quit",
)


class FakeSession:
    def __init__(self, home: Path, device: str) -> None:
        self.home = Path(home)
        self.device = device
        self.protocol = wire.load_protocol()
        self.private, self.public = self._load_or_create()
        self.seq = 0
        self.answer_ping = True
        self.read_mode = "on-time"
        self.code = ""

    def _load_or_create(self) -> tuple[str, str]:
        path = self.home / "fake_phone_key.pem"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            private = path.read_text(encoding="ascii")
            key = serialization.load_pem_private_key(private.encode("ascii"), password=None)
        else:
            key = ec.generate_private_key(ec.SECP256R1())
            private = key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ).decode("ascii")
            path.write_text(private, encoding="ascii")
        public = key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii")
        return private, public

    def envelope(self, type_name: str, **fields) -> dict:
        # P10-INTAKE: each frame is a fresh envelope — P10-D12
        self.seq += 1
        payload = {
            "type": type_name,
            "device_id": self.device,
            "seq": self.seq,
            "sent_at_ms": int(time.time() * 1000),
            "contract_version": int(self.protocol["contract_version"]),
        }
        payload.update(fields)
        return payload

    def signed(self, payload: dict, *, private: str | None = None, signature: str | None = None) -> bytes:
        key = self.private if private is None else private
        sig = wire.sign_payload(key, payload) if signature is None else signature
        return wire.encode_frame("signed", payload, sig, self.protocol)

    def text_event(self, provider: str, body: str, **extra) -> bytes:
        payload = self.envelope(
            "messages.event",
            provider_id=provider,
            kind="sms",
            revision=int(extra.pop("revision", 1)),
            completeness=str(extra.pop("completeness", "complete")),
            received_at_ms=int(time.time() * 1000),
            sender_raw="+15555550100",
            is_group=0,
            body=body,
            **extra,
        )
        return self.signed(payload)

    def notification_event(self, package: str, key: str, stamp: str) -> bytes:
        payload = self.envelope(
            "notifications.event",
            package=package,
            notification_key=key,
            newest_message_timestamp=stamp,
            revision=1,
            completeness="complete",
            posted_at_ms=int(time.time() * 1000),
            text="ZP10 notice",
            is_group=0,
        )
        return self.signed(payload)


def misbehave(session: FakeSession, how: str) -> bytes:
    payload = session.envelope(
        "messages.event",
        provider_id="sms-bad",
        kind="sms",
        revision=1,
        completeness="complete",
        received_at_ms=int(time.time() * 1000),
        sender_raw="+15555550100",
        is_group=0,
        body="ZP10",
    )
    if how == "unsigned":
        return session.signed(payload, signature="")
    if how == "bad-signature":
        return session.signed(payload, signature="AAAA")
    if how == "unknown-key":
        other = ec.generate_private_key(ec.SECP256R1())
        private = other.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode("ascii")
        return session.signed(payload, private=private)
    if how == "wrong-device":
        payload["device_id"] = "zp10-other-device"
        return session.signed(payload)
    if how == "replay":
        session.seq -= 1
        payload["seq"] = session.seq
        return session.signed(payload)
    if how == "stale":
        payload["sent_at_ms"] = int(time.time() * 1000) - 600_000
        return session.signed(payload)
    if how == "version":
        payload["contract_version"] = 99
        return session.signed(payload)
    if how == "malformed":
        return b"{"
    return session.signed(payload)


async def _run(args: argparse.Namespace) -> None:
    import websockets

    session = FakeSession(Path(args.home), args.device)
    async with websockets.connect(f"ws://{args.host}:{args.port}") as ws:
        opened = session.envelope("phone_open", public_pem=session.public)
        await ws.send(wire.encode_frame("pairing", opened, wire.pairing_mac(args.code, opened), session.protocol))
        bind = json.loads(await ws.recv())
        bound = session.envelope("phone_bind", public_pem=session.public)
        await ws.send(wire.encode_frame("pairing", bound, wire.pairing_mac(args.code, bound), session.protocol))
        await ws.recv()
        if bind["payload"]["type"] != "pc_bind" or not bind["payload"].get("pc_id"):
            raise SystemExit("expected pc_bind")
        if not wire.mac_matches(args.code, bind["payload"], bind["signature"]):
            raise SystemExit("bad pc_bind mac")

        async def listen() -> None:
            async for message in ws:
                raw = message.encode("utf-8") if isinstance(message, str) else message
                try:
                    payload = json.loads(raw.decode("utf-8"))["payload"]
                except (UnicodeDecodeError, json.JSONDecodeError, KeyError):
                    continue
                if payload.get("type") == "keepalive.ping" and session.answer_ping:
                    pong = session.envelope("keepalive.pong")
                    await ws.send(session.signed(pong))
                elif str(payload.get("type") or "").endswith(".request") or payload.get("type") == "diagnostic_read":
                    if session.read_mode == "never":
                        continue
                    if session.read_mode == "late":
                        await asyncio.sleep(int(session.protocol["timing_ms"]["read_timeout"]) / 1000 + 1)
                    result = session.envelope(
                        "history.read.result" if payload.get("type") == "history.read.request" else "code.read.result",
                        request_id=payload.get("request_id"),
                        status="ok",
                        value="ZP10-CODE",
                    )
                    await ws.send(session.signed(result))

        task = asyncio.create_task(listen())
        loop = asyncio.get_running_loop()
        while True:
            line = (await loop.run_in_executor(None, sys.stdin.readline)).strip()
            if not line:
                break
            parts = line.split()
            cmd = parts[0]
            if cmd == "quit":
                break
            if cmd == "text":
                await ws.send(session.text_event(parts[1], " ".join(parts[2:]) or "ZP10"))
            elif cmd == "notification":
                await ws.send(session.notification_event(parts[1], parts[2], parts[3]))
            elif cmd == "ping":
                session.answer_ping = parts[1] != "silent"
            elif cmd == "read":
                session.read_mode = parts[1]
            elif cmd == "bad":
                if parts[1] == "half-open":
                    task.cancel()
                    continue
                await ws.send(misbehave(session, parts[1]))
            elif cmd == "second":
                other = await websockets.connect(f"ws://{args.host}:{args.port}")
                await other.send(session.text_event("sms-second", "ZP10"))
            elif cmd == "late-revision":
                await ws.send(session.text_event(parts[1], "ZP10", revision=1))
                await ws.send(session.text_event(parts[1], "ZP10 later", revision=2))
            elif cmd == "duplicate":
                frame = session.text_event(parts[1], "ZP10")
                await ws.send(frame)
                await ws.send(session.text_event(parts[1], "ZP10"))
            elif cmd == "out-of-order":
                await ws.send(session.text_event(parts[1] + "-3", "ZP10"))
                await ws.send(session.text_event(parts[1] + "-1", "ZP10"))
            elif cmd == "exhausted":
                await ws.send(session.text_event(parts[1], "ZP10", completeness="exhausted"))
            elif cmd == "oversize":
                await ws.send(session.text_event(parts[1], "Z" * 16001))
            elif cmd == "separator":
                await ws.send(session.text_event("sms\u001f1", "ZP10"))
        task.cancel()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=47821)
    parser.add_argument("--code", required=True)
    parser.add_argument("--device", default="zp10-device-test")
    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
