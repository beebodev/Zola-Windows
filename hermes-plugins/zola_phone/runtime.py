"""Held phone connection, ingest, and the local pipe (P10-D12)."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import sys
import threading
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from . import wire

LOG_MAX_BYTES = 1_000_000
LOG_BACKUPS = 3
EXIT_ALREADY_RUNNING = 2
PIPE_HELD = "pipe_held"
FORBIDDEN_MODULES = (
    "auth",
    "google_http",
    "gmail",
    "gcal",
    "drive",
    "contacts",
    "send_gate",
    "ranker",
    "read_common",
    "loops",
    "taint",
    "turn_context",
    "recorded_results",
)

_log = logging.getLogger("zola_phone")


def workspace_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "zola_workspace"


def load_store():
    # P10-INTAKE: flat imports avoid zola_workspace/__init__.py — P10-D12
    folder = str(workspace_dir())
    if folder not in sys.path:
        sys.path.insert(0, folder)
    import address_hash
    import loop_match
    import phone_ids
    import proactive_store

    return address_hash, loop_match, phone_ids, proactive_store


def forbidden_loaded() -> list:
    found = [name for name in FORBIDDEN_MODULES if name in sys.modules]
    for name in sys.modules:
        if name.startswith("hermes_cli") or name.startswith("tui_gateway"):
            found.append(name)
    return found


def configure_logging(home: Path) -> None:
    path = home / "logs" / "zola_phone.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    _log.setLevel(logging.INFO)
    for handler in list(_log.handlers):
        handler.close()
    _log.handlers.clear()
    handler = RotatingFileHandler(path, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUPS, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    _log.addHandler(handler)


def _note(event: str, **fields: Any) -> None:
    parts = [event]
    for key in sorted(fields):
        if fields[key] is not None:
            parts.append(f"{key}={fields[key]}")
    _log.info("%s", " ".join(parts))


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Engine:
    def __init__(self, home: Path, secret: str, *, fault: Optional[Callable[[str], None]] = None) -> None:
        self.home = Path(home)
        self.secret = secret
        self.fault = fault
        self.protocol = wire.load_protocol()
        self.address_hash, self.loop_match, self.phone_ids, self.store = load_store()
        self.db_path = self.store.default_db_path(self.home)
        self.conn = self.store.connect(self.db_path, retry=False)
        self.key_dir = self.home / "phone"
        self.key_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._private = ""
        self._public = ""
        self.peer: Dict[str, Any] = {}
        self._load_keys()
        self.code = ""
        self.code_expires = 0
        self.code_attempts = 0
        self.code_dead = False
        self._pair_pending: Optional[Dict[str, Any]] = None
        self.current = ""
        self.socket_open = False
        self.closed_at_ms = int(self.peer.get("closed_at_ms") or 0)
        self.awaiting_pong = False
        self.misses = 0
        self.last_ping_answered = True
        self.tailnet = True
        self.pending_events: Dict[str, threading.Event] = {}
        self.pending_results: Dict[str, Dict[str, Any]] = {}
        self.last_reason = ""
        self.clock: Callable[[], int] = lambda: int(time.time() * 1000)
        self.sender: Optional[Callable[[bytes], None]] = None
        self._sender_conn = ""
        self.closer: Optional[Callable[[str], None]] = None
        self.last_frame_ms = 0
        self.next_ping_ms = 0
        self.pong_deadline_ms = 0
        self.read_timeout_ping = False
        self.last_closed_conn = ""
        self.verified_calls = 0
        self._recover()

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass

    def _load_keys(self) -> None:
        from . import keys

        loaded = keys.load_or_create(self.key_dir)
        self._private = loaded["private_pem"]
        self._public = loaded["public_pem"]
        self.peer = loaded["peer"]

    def _save_peer(self) -> None:
        from . import keys

        keys.save_peer(self.key_dir, self.peer)

    def _recover(self) -> None:
        # P10-INTAKE: unevaluated rows are evaluated once on startup — P10-D12
        listed = self.store.list_unevaluated_phone_items(self.conn)
        if not listed.get("ok"):
            return
        for item in listed.get("items") or []:
            self._evaluate_item(item)

    def link_state(self, now_ms: Optional[int] = None) -> str:
        now_ms = self.clock() if now_ms is None else int(now_ms)
        if not self.tailnet:
            return "no_tailnet"
        if not self.peer.get("device_id"):
            return "not_paired"
        if self.socket_open:
            if self.last_ping_answered:
                return "connected"
            return "not_responding"
        closed = int(self.closed_at_ms or 0)
        grace = int(self.protocol["reconnecting_grace_ms"])
        if closed and now_ms - closed < grace:
            return "reconnecting"
        if closed:
            return "offline"
        return "reconnecting"

    def status(self) -> Dict[str, Any]:
        device = str(self.peer.get("device_id") or "")
        return {
            "ok": True,
            "link_state": self.link_state(),
            "socket_open": self.socket_open,
            "last_ping_answered": self.last_ping_answered,
            "paired": bool(device),
            "device_hash": _hash(device) if device else "",
            "last_disconnect": str(self.peer.get("last_disconnect") or ""),
        }

    def _secret_ok(self, presented: str) -> bool:
        return bool(self.secret) and hmac.compare_digest(self.secret, str(presented or ""))

    def local_request(self, body: Dict[str, Any]) -> Dict[str, Any]:
        kind = str(body.get("type") or "")
        needs = self.protocol["local_requests"].get(kind, {}).get("secret", True)
        if kind not in self.protocol["local_requests"]:
            return {"ok": False, "reason": "malformed"}
        if needs and not self._secret_ok(str(body.get("secret") or "")):
            _note("zola_phone.reject", reason="unauthorized", req=kind)
            return {"ok": False, "reason": "unauthorized"}
        if kind == "status":
            with self._lock:
                return self.status()
        if kind == "pairing.start":
            return self._start_pairing()
        with self._lock:
            if not self.socket_open or self.sender is None:
                return {"ok": False, "status": "phone_unavailable", "reason": "no_connection"}
            if not self.peer.get("device_id"):
                return {"ok": False, "status": "phone_unavailable", "reason": "not_paired"}
            sender = self.sender
        return self._relay(kind, body, sender)

    def _start_pairing(self) -> Dict[str, Any]:
        digits = int(self.protocol["pairing"]["code_digits"])
        span = 10 ** digits
        with self._lock:
            self.code = f"{secrets.randbelow(span):0{digits}d}"
            self.code_expires = self.clock() + int(self.protocol["timing_ms"]["pairing_code_ttl"])
            self.code_attempts = 0
            self.code_dead = False
            code = self.code
        _note("zola_phone.pairing", result="started")
        return {"ok": True, "code": code}

    def _relay(self, kind: str, body: Dict[str, Any], sender: Callable[[bytes], None]) -> Dict[str, Any]:
        request_id = str(body.get("request_id") or secrets.token_hex(8))
        type_name = {
            "read_history": "history.read.request",
            "read_notifications": "notifications.read.request",
            "read_code": "code.read.request",
            "diagnostic_read": "diagnostic_read",
        }[kind]
        with self._lock:
            payload = self._pc_payload(type_name, request_id=request_id)
            for key in ("selector", "max_messages", "max_characters", "max_items", "provider_id", "kind"):
                if key in body:
                    payload[key] = body[key]
            deadline = int(self.protocol["timing_ms"]["read_timeout"])
            payload["deadline_ms"] = deadline
            frame = wire.encode_frame("signed", payload, wire.sign_payload(self._private, payload), self.protocol)
            event = threading.Event()
            self.pending_events[request_id] = event
        try:
            sender(frame)
        except Exception:
            with self._lock:
                self.pending_events.pop(request_id, None)
            return {"ok": False, "status": "phone_unavailable", "reason": "no_connection"}
        if not event.wait((deadline + 1000) / 1000):
            with self._lock:
                self.pending_events.pop(request_id, None)
                self.read_timeout_ping = True
            _note("zola_phone.read", req=kind, status="timeout")
            return {"ok": False, "status": "phone_unavailable", "reason": "timeout"}
        with self._lock:
            result = self.pending_results.pop(request_id, {"ok": False, "status": "phone_unavailable", "reason": "timeout"})
        _note("zola_phone.read", req=kind, status="ok" if result.get("ok") else "late")
        return result

    def _pc_payload(self, type_name: str, **extra: Any) -> Dict[str, Any]:
        with self._lock:
            seq = int(self.peer.get("pc_seq") or 0) + 1
            self.peer["pc_seq"] = seq
            self._save_peer()
            payload = {
                "type": type_name,
                "device_id": self.peer.get("device_id") or "",
                "seq": seq,
                "sent_at_ms": self.clock(),
                "contract_version": int(self.protocol["contract_version"]),
            }
            payload.update(extra)
            return payload

    def note_socket(self, open_: bool, *, reason: str = "", who: str = "pc") -> None:
        with self._lock:
            self.socket_open = open_
            if open_:
                self.closed_at_ms = 0
                self.peer["link_open"] = True
                self.last_ping_answered = True
                self.awaiting_pong = False
                self.misses = 0
                if not self.next_ping_ms:
                    self.next_ping_ms = self.clock() + int(self.protocol["timing_ms"]["ping_interval"])
            else:
                self.closed_at_ms = self.clock()
                self.peer["link_open"] = False
                self.peer["closed_at_ms"] = self.closed_at_ms
                self.peer["last_disconnect"] = reason
                self.last_closed_conn = self.current
                self.current = ""
                self.sender = None
                self._sender_conn = ""
                self.awaiting_pong = False
                _note("zola_phone.disconnect", reason=reason or "network-lost", who=who)
            self._save_peer()

    def note_pong(self) -> None:
        with self._lock:
            self.awaiting_pong = False
            self.misses = 0
            self.last_ping_answered = True
            self.next_ping_ms = self.clock() + int(self.protocol["timing_ms"]["ping_interval"])

    def note_pong_miss(self) -> bool:
        """True when the socket should close."""
        with self._lock:
            self.misses += 1
            self.awaiting_pong = False
            self.last_ping_answered = False
            limit = int(self.protocol["timing_ms"]["pong_misses_before_close"])
            if self.misses >= limit:
                self.note_socket(False, reason="pong-missed", who="pc")
                return True
            return False

    def keepalive_step(self) -> str:
        # P10-INTAKE: interval pings use the contract clock; one extra ping follows a timed-out read — P10-D07
        with self._lock:
            if not self.socket_open or not self.current:
                return "idle"
            now = self.clock()
            timing = self.protocol["timing_ms"]
            if self.awaiting_pong and now >= self.pong_deadline_ms:
                return "close" if self.note_pong_miss() else "miss"
            if self.awaiting_pong:
                return "wait"
            due_immediate = self.read_timeout_ping
            due_interval = bool(self.next_ping_ms) and now >= self.next_ping_ms
            if not due_immediate and not due_interval:
                return "wait"
            self.awaiting_pong = True
            self.pong_deadline_ms = now + int(timing["pong_wait"])
            if due_immediate:
                self.read_timeout_ping = False
            if due_interval:
                self.next_ping_ms = now + int(timing["ping_interval"])
            return "ping"

    def make_ping(self) -> bytes:
        payload = self._pc_payload("keepalive.ping")
        return wire.encode_frame("signed", payload, wire.sign_payload(self._private, payload), self.protocol)

    def adopt_sender(self, conn_id: str, sender: Callable[[bytes], None]) -> None:
        with self._lock:
            if self.current == conn_id:
                self.sender = sender
                self._sender_conn = conn_id

    def release_sender(self, conn_id: str) -> None:
        with self._lock:
            if self._sender_conn == conn_id:
                self.sender = None
                self._sender_conn = ""

    def receive(self, conn_id: str, raw: bytes) -> Optional[bytes]:
        calls = {"n": 0}

        def _count() -> None:
            calls["n"] += 1
            self.verified_calls += 1

        reason = wire.classify_raw(
            raw,
            protocol=self.protocol,
            paired_public=str(self.peer.get("public_pem") or ""),
            rejected_publics=list(self.peer.get("rejected") or []),
            paired_device_id=str(self.peer.get("device_id") or ""),
            last_seq=max(
                int(self.peer.get("phone_seq") or 0),
                int((self._pair_pending or {}).get("seq") or 0),
            ),
            now_ms=self.clock(),
            pairing_code="" if self.code_dead else self.code,
            on_verify=_count,
        )
        self.last_reason = reason
        if reason != "accept":
            _note("zola_phone.reject", reason=reason)
            if reason == "bad-signature" and len(raw) <= wire.frame_limit(self.protocol) and parsed_kind(raw) == "pairing":
                self.note_pairing_failure()
            return None
        parsed = json.loads(raw.decode("utf-8"))
        payload = parsed["payload"]
        if parsed.get("kind") == "pairing":
            with self._lock:
                return self._pairing(conn_id, payload)
        with self._lock:
            if self.current and conn_id != self.current:
                old = self.current
                self.current = conn_id
                self.sender = None
                self._sender_conn = ""
                self.socket_open = True
                closer = self.closer
                _note("zola_phone.disconnect", reason="superseded", who="pc")
            else:
                old = ""
                closer = None
                self.current = conn_id
                self.socket_open = True
                self.closed_at_ms = 0
            self.last_frame_ms = self.clock()
            if not self.next_ping_ms:
                self.next_ping_ms = self.clock() + int(self.protocol["timing_ms"]["ping_interval"])
            self.peer["phone_seq"] = int(payload["seq"])
            self._save_peer()
        if closer is not None and old:
            closer(old)
        return self._dispatch(payload)

    def _pairing(self, conn_id: str, payload: Dict[str, Any]) -> Optional[bytes]:
        now = self.clock()
        if self.code_dead or not self.code or now > self.code_expires:
            _note("zola_phone.reject", reason="pairing-expired")
            return None
        kind = str(payload.get("type") or "")
        device = str(payload.get("device_id") or "")
        if kind == "phone_open":
            public = str(payload.get("public_pem") or "")
            if not public or not device:
                return None
            self._pair_pending = {"device": device, "public": public, "seq": int(payload["seq"])}
            self.current = conn_id
            return self._pairing_frame("pc_bind", device_id=device, public_pem=self._public)
        if kind != "phone_bind" or not self._pair_pending:
            return None
        if device != self._pair_pending["device"] or str(payload.get("public_pem") or "") != self._pair_pending["public"]:
            self.note_pairing_failure()
            return None
        public = self._pair_pending["public"]
        previous = str(self.peer.get("public_pem") or "")
        same = device == self.peer.get("device_id")
        rejected = list(self.peer.get("rejected") or [])
        if previous and previous not in rejected:
            rejected.append(previous)
        self.peer = {
            "device_id": device,
            "public_pem": public,
            "rejected": rejected if same else ([] if not previous else [previous]),
            "phone_seq": int(payload["seq"]),
            "pc_seq": int(self.peer.get("pc_seq") or 0),
            "link_open": True,
        }
        self._pair_pending = None
        reply = self._pairing_frame("pc_ok", device_id=device)
        self.code_dead = True
        self.code = ""
        self.current = conn_id
        self.socket_open = True
        self.last_ping_answered = True
        self._save_peer()
        _note("zola_phone.pairing", result="paired", device=_hash(device))
        return reply

    def _pairing_frame(self, type_name: str, **extra: Any) -> bytes:
        payload = self._pc_payload(type_name, **extra)
        mac = wire.pairing_mac(self.code, payload)
        return wire.encode_frame("pairing", payload, mac, self.protocol)

    def note_pairing_failure(self) -> None:
        self.code_attempts += 1
        limit = int(self.protocol["timing_ms"]["pairing_wrong_attempts"])
        if self.code_attempts >= limit:
            self.code_dead = True
            self.code = ""
            _note("zola_phone.pairing", result="invalidated")

    def _ack_frame(self, type_name: str, device: str, **extra: Any) -> bytes:
        payload = self._pc_payload(type_name, **extra)
        payload["device_id"] = device
        return wire.encode_frame("signed", payload, wire.sign_payload(self._private, payload), self.protocol)

    def _dispatch(self, payload: Dict[str, Any]) -> Optional[bytes]:
        type_name = str(payload.get("type") or "")
        if type_name in ("keepalive.pong",):
            self.note_pong()
            return None
        if type_name.endswith(".result") or type_name == "diagnostic_read.result":
            request_id = str(payload.get("request_id") or "")
            with self._lock:
                event = self.pending_events.pop(request_id, None)
                if event is None:
                    _note("zola_phone.read", req=type_name, status="late-result")
                    return None
                body = {"ok": True, "request_id": request_id, "status": payload.get("status") or "ok"}
                if type_name != "code.read.result":
                    body["items"] = payload.get("items")
                else:
                    body["value"] = payload.get("value")
                self.pending_results[request_id] = body
            event.set()
            return None
        if type_name not in ("messages.event", "notifications.event"):
            return None
        return self._ingest(payload)

    def _ingest(self, payload: Dict[str, Any]) -> Optional[bytes]:
        # P10-INTAKE: a missing contract field is a refusal, not a default — P10-D12
        notif = payload.get("type") == "notifications.event"
        kind = "notif" if notif else str(payload.get("kind") or "")
        if notif:
            required = ("package", "notification_key", "newest_message_timestamp")
            if any(field not in payload for field in required):
                return self._ack_for(payload, kind, "rejected", "bad_field")
            when_key = "posted_at_ms"
        else:
            if kind not in ("sms", "mms") or "provider_id" not in payload:
                return self._ack_for(payload, kind, "rejected", "bad_field")
            when_key = "received_at_ms"
        if "completeness" not in payload or payload.get("completeness") not in ("complete", "exhausted"):
            return self._ack_for(payload, kind, "rejected", "bad_completeness")
        revision = payload.get("revision")
        if "revision" not in payload or isinstance(revision, bool) or not isinstance(revision, int):
            return self._ack_for(payload, kind, "rejected", "bad_revision")
        when_raw = payload.get(when_key)
        if when_key not in payload or isinstance(when_raw, bool) or not isinstance(when_raw, int):
            return self._ack_for(payload, kind, "rejected", "bad_time")
        from datetime import datetime, timezone

        when = datetime.fromtimestamp(int(when_raw) / 1000.0, timezone.utc)
        body = str(payload.get("body") or payload.get("text") or "")
        result = self.store.ingest_phone_item(
            self.conn,
            kind=kind,
            device_id=str(payload.get("device_id") or ""),
            provider_id=str(payload.get("provider_id") or ""),
            package=str(payload.get("package") or ""),
            notification_key=str(payload.get("notification_key") or ""),
            newest_message_timestamp=str(payload.get("newest_message_timestamp") or ""),
            revision=revision,
            completeness=str(payload.get("completeness") or ""),
            received_at=when,
            sender_raw=str(payload.get("sender_raw") or ""),
            sender_display_name=str(payload.get("sender_display_name") or ""),
            body=body,
            is_group=int(payload.get("is_group") or 0),
            participant_count=payload.get("participant_count"),
            rcs_flag=payload.get("rcs_flag"),
            attachment_has=payload.get("attachment_has"),
            attachment_count=payload.get("attachment_count"),
            attachment_kind=payload.get("attachment_kind"),
            mask_kind=payload.get("mask_kind"),
            truncated=payload.get("truncated"),
        )
        if self.fault is not None:
            self.fault("after_commit")
        word = str(result.get("result") or "")
        if word in ("stored", "updated", "duplicate"):
            self._maybe_evaluate(str(result.get("id") or ""))
        if self.fault is not None:
            self.fault("before_ack")
        ack = "duplicate" if word in ("ignored", "duplicate") else word
        reason = result.get("reason")
        _note(
            "zola_phone.accept",
            item=_hash(str(result.get("id") or payload.get("provider_id") or "")),
            kind=kind,
            result=ack,
        )
        return self._ack_for(payload, kind, ack, reason if ack == "rejected" else None)

    def _ack_for(self, payload: Dict[str, Any], kind: str, word: str, reason: Optional[str]) -> bytes:
        revision = payload.get("revision")
        extra: Dict[str, Any] = {
            "result": word,
            "revision": revision if isinstance(revision, int) and not isinstance(revision, bool) else 0,
        }
        if reason:
            extra["reason"] = reason
        if kind == "notif":
            extra["package"] = str(payload.get("package") or "")
            extra["notification_key"] = str(payload.get("notification_key") or "")
            extra["newest_message_timestamp"] = str(payload.get("newest_message_timestamp") or "")
            return self._ack_frame("notifications.ack", str(payload.get("device_id") or ""), **extra)
        extra["provider_id"] = str(payload.get("provider_id") or "")
        extra["kind"] = kind
        return self._ack_frame("messages.ack", str(payload.get("device_id") or ""), **extra)

    def _maybe_evaluate(self, item_id: str) -> None:
        if not item_id:
            return
        listed = self.store.list_unevaluated_phone_items(self.conn)
        for item in listed.get("items") or []:
            if item["id"] == item_id:
                self._evaluate_item(item)
                return

    def _evaluate_item(self, item: Dict[str, Any]) -> None:
        if self.fault is not None:
            self.fault("before_eval")
        found = self.store.list_open_loop_predicates(self.conn)
        view = {
            "source": item.get("source"),
            "message_id": item.get("message_id"),
            "sender_address_hash": item.get("sender_address_hash"),
            "detected_at": item.get("detected_at"),
        }
        for loop in found.get("loops") or []:
            if not self.loop_match.evaluate(loop.get("predicate") or {}, view):
                continue
            noted = self.store.note_loop_match_on_loop(self.conn, loop["id"])
            if not (noted.get("ok") or noted.get("already")):
                return
            marked = self.store.set_loop_matched(self.conn, item["id"])
            if not (marked.get("ok") or marked.get("already")):
                return
        saved = self.store.mark_watch_evaluated(self.conn, item["id"])
        if not saved.get("ok"):
            _note("zola_phone.reject", reason="watch")


def parsed_kind(raw: bytes) -> str:
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ""
    if isinstance(parsed, dict):
        return str(parsed.get("kind") or "")
    return ""


async def _wait(future: asyncio.Future, timeout: float) -> Dict[str, Any]:
    return await asyncio.wait_for(future, timeout)
