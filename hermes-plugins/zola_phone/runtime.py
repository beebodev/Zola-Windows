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
from dataclasses import dataclass
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

# P10-READ: handle life is 60 s; the tool waits 45 s and the client gives up sooner than that
CODE_HANDLE_TTL_MS = 60_000
CODE_ARM_LIMIT = 8


@dataclass
class _Arm:
    """One armed code read. Memory only. It holds ids, never a value."""

    session_id: str
    turn_id: str
    item_id: str
    provider_id: str
    kind: str
    expires_ms: int
    state: str = "armed"  # armed | redeeming | used | disarmed


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
        self.listener_permission = 1
        self.listener_bound = 1
        self.allowlist_count = 0
        self.allowlist_packages: list[str] = []
        self.notice_depth = 0
        self.notice_drops = 0
        self.notice_age_drops = 0
        self.notice_filtered = 0
        self.notice_removed = 0
        self.notice_rejected = 0
        self.notice_gaps = 0
        # P10-READ: armed code reads live in memory only and die with this process — mechanism B
        self._arms: Dict[str, "_Arm"] = {}
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
        self.pc_id = str(loaded["pc_id"])

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
            "listener_permission": self.listener_permission,
            "listener_bound": self.listener_bound,
            "allowlist_count": self.allowlist_count,
            "allowlist_packages": list(self.allowlist_packages),
            "notification_queue_depth": self.notice_depth,
            "notification_queue_drops": self.notice_drops,
            "notification_age_drops": self.notice_age_drops,
            "notification_filtered": self.notice_filtered,
            "allowlist_removed": self.notice_removed,
            "notification_rejected": self.notice_rejected,
            "listener_gap_count": self.notice_gaps,
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
        # P10-READ: the code handle lifecycle never touches the store and never logs a value
        if kind == "code.arm":
            return self._code_arm(body)
        if kind == "code.redeem":
            return self._code_redeem(body)
        if kind == "code.disarm":
            return self._code_disarm(body)
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

    # ── P10-READ: code arm / redeem / disarm (mechanism B) ───────────────────────────────────────
    #
    # The serve-side tool arms one read and gets an opaque handle. Only the Windows client, which
    # holds the launch secret, redeems it, and only the client ever sees the value. Nothing here is
    # stored, and no log line carries the handle's text or the value.

    def _prune_arms(self, now_ms: int) -> None:
        for handle in [h for h, arm in self._arms.items() if now_ms >= arm.expires_ms and arm.state != "redeeming"]:
            self._arms.pop(handle, None)

    def _code_arm(self, body: Dict[str, Any]) -> Dict[str, Any]:
        fields: Dict[str, str] = {}
        for name in ("session_id", "turn_id", "item_id", "provider_id", "kind"):
            value = body.get(name)
            if not isinstance(value, str) or not value:
                _note("zola_phone.code", step="arm", result="refused", reason="bad_request")
                return {"ok": False, "reason": "bad_request"}
            fields[name] = value
        if fields["kind"] not in ("sms", "mms"):
            _note("zola_phone.code", step="arm", result="refused", reason="bad_request")
            return {"ok": False, "reason": "bad_request"}
        with self._lock:
            if not self.peer.get("device_id"):
                return {"ok": False, "status": "phone_unavailable", "reason": "not_paired"}
            if not self.socket_open or self.sender is None:
                return {"ok": False, "status": "phone_unavailable", "reason": "no_connection"}
            now = self.clock()
            self._prune_arms(now)
            # one live arm per session: a new ask replaces the old one
            for handle in [h for h, arm in self._arms.items() if arm.session_id == fields["session_id"]]:
                self._drop_arm_locked(handle)
            while len(self._arms) >= CODE_ARM_LIMIT:
                oldest = min(self._arms, key=lambda h: self._arms[h].expires_ms)
                self._drop_arm_locked(oldest)
            handle = secrets.token_urlsafe(24)
            self._arms[handle] = _Arm(
                session_id=fields["session_id"],
                turn_id=fields["turn_id"],
                item_id=fields["item_id"],
                provider_id=fields["provider_id"],
                kind=fields["kind"],
                expires_ms=now + CODE_HANDLE_TTL_MS,
            )
        _note("zola_phone.code", step="arm", result="ok")
        return {"ok": True, "handle": handle, "ttl_ms": CODE_HANDLE_TTL_MS}

    def _drop_arm_locked(self, handle: str) -> None:
        arm = self._arms.get(handle)
        if arm is None:
            return
        if arm.state == "redeeming":
            # a relay is in flight; its value is discarded when it lands
            arm.state = "disarmed"
        else:
            self._arms.pop(handle, None)

    def _code_redeem(self, body: Dict[str, Any]) -> Dict[str, Any]:
        handle = body.get("handle")
        session_id = body.get("session_id")
        if not isinstance(handle, str) or not handle or not isinstance(session_id, str) or not session_id:
            _note("zola_phone.code", step="redeem", result="refused", reason="bad_request")
            return {"ok": False, "reason": "bad_request"}
        with self._lock:
            now = self.clock()
            arm = self._arms.get(handle)
            if arm is None:
                refusal = "unknown_handle"
            elif arm.state == "disarmed":
                refusal = "cancelled"
            elif arm.state != "armed":
                refusal = "replay"
            elif now >= arm.expires_ms:
                self._arms.pop(handle, None)
                refusal = "expired"
            elif session_id != arm.session_id:
                refusal = "wrong_session"
            elif "turn_id" in body and body.get("turn_id") != arm.turn_id:
                refusal = "wrong_turn"
            elif "item_id" in body and body.get("item_id") != arm.item_id:
                refusal = "wrong_item"
            else:
                refusal = ""
            if refusal:
                _note("zola_phone.code", step="redeem", result="refused", reason=refusal)
                return {"ok": False, "reason": refusal}
            assert arm is not None
            # single use: the handle is spent now, whatever the phone answers
            arm.state = "redeeming"
            sender = self.sender
            if not self.socket_open or sender is None:
                arm.state = "used"
                return {"ok": False, "status": "phone_unavailable", "reason": "no_connection"}
            provider_id, kind = arm.provider_id, arm.kind
        result = self._relay("read_code", {"provider_id": provider_id, "kind": kind}, sender)
        with self._lock:
            if arm.state == "disarmed":
                self._arms.pop(handle, None)
                _note("zola_phone.code", step="redeem", result="discarded", reason="disarmed")
                return {"ok": False, "reason": "cancelled"}
            arm.state = "used"
        value = result.get("value")
        if not result.get("ok") or result.get("status") != "ok" or not isinstance(value, str) or not value:
            reason = str(result.get("reason") or "not_identifiable")
            _note("zola_phone.code", step="redeem", result="refused", reason=reason)
            return {"ok": False, "status": str(result.get("status") or "refused"), "reason": reason}
        _note("zola_phone.code", step="redeem", result="ok")
        return {"ok": True, "value": value, "value_kind": str(result.get("value_kind") or "")}

    def _code_disarm(self, body: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            if body.get("all") is True:
                targets = list(self._arms)
            elif isinstance(body.get("handle"), str) and body.get("handle"):
                targets = [str(body["handle"])] if str(body["handle"]) in self._arms else []
            elif isinstance(body.get("session_id"), str) and body.get("session_id"):
                targets = [h for h, arm in self._arms.items() if arm.session_id == body["session_id"]]
            else:
                _note("zola_phone.code", step="disarm", result="refused", reason="bad_request")
                return {"ok": False, "reason": "bad_request"}
            for handle in targets:
                self._drop_arm_locked(handle)
        _note("zola_phone.code", step="disarm", result="ok", count=len(targets))
        return {"ok": True, "disarmed": len(targets)}

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
            # P10-NOTIFY: package filters notifications.read.request — N12
            for key in ("selector", "max_messages", "max_characters", "max_items", "provider_id", "kind", "package"):
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
                self._note_pairing_material(raw)
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
            _note(
                "zola_phone.pairing",
                step=str(payload.get("type") or "unknown"),
                result="dropped",
                reason="pairing-expired",
            )
            return None
        kind = str(payload.get("type") or "")
        device = str(payload.get("device_id") or "")
        if kind == "phone_open":
            public = str(payload.get("public_pem") or "")
            if not public or not device:
                _note("zola_phone.pairing", step="phone_open", result="dropped", reason="missing")
                return None
            self._pair_pending = {"device": device, "public": public, "seq": int(payload["seq"])}
            self.current = conn_id
            frame = self._pairing_frame("pc_bind", device_id=device, public_pem=self._public, pc_id=self.pc_id)
            _note("zola_phone.pairing", step="pc_bind", result="sent")
            return frame
        if kind != "phone_bind":
            _note("zola_phone.pairing", step=kind or "unknown", result="dropped", reason="unexpected")
            return None
        if not self._pair_pending:
            _note("zola_phone.pairing", step="phone_bind", result="dropped", reason="no-pending")
            return None
        if device != self._pair_pending["device"] or str(payload.get("public_pem") or "") != self._pair_pending["public"]:
            self.note_pairing_failure()
            _note("zola_phone.pairing", step="phone_bind", result="dropped", reason="mismatch")
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
        _note("zola_phone.pairing", step="pc_ok", result="sent")
        _note("zola_phone.pairing", result="paired", device=_hash(device))
        return reply

    def _pairing_frame(self, type_name: str, **extra: Any) -> bytes:
        payload = self._pc_payload(type_name, **extra)
        mac = wire.pairing_mac(self.code, payload)
        return wire.encode_frame("pairing", payload, mac, self.protocol)

    def _note_pairing_material(self, raw: bytes) -> None:
        try:
            parsed = json.loads(raw.decode("utf-8"))
            payload = parsed.get("payload") if isinstance(parsed, dict) else None
            if not isinstance(payload, dict):
                return
            material = wire.canonical(payload)
            pem = str(payload.get("public_pem") or "")
            _note(
                "zola_phone.pairing",
                result="material",
                bytes=len(material),
                sha=hashlib.sha256(material).hexdigest()[:16],
                code_len=len(self.code),
                newlines=pem.count("\n"),
                cr=pem.count("\r"),
            )
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
            _note("zola_phone.pairing", result="material-unread")

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
        if type_name == "hello":
            caps = payload.get("capabilities")
            _note(
                "zola_phone.hello",
                capabilities=len(caps) if isinstance(caps, list) else 0,
                pending_incomplete=payload.get("pending_incomplete"),
                notification_queue_depth=payload.get("notification_queue_depth"),
                listener_permission=payload.get("listener_permission"),
                listener_bound=payload.get("listener_bound"),
                allowlist_count=payload.get("allowlist_count"),
                notification_queue_drops=payload.get("notification_queue_drops"),
                listener_gap_count=payload.get("listener_gap_count"),
            )
            return None
        if type_name == "device.health":
            self._remember_notice(payload)
            _note(
                "zola_phone.health",
                pending_incomplete=payload.get("pending_incomplete"),
                exhausted=payload.get("exhausted"),
                unacked=payload.get("unacked"),
                rejected=payload.get("rejected"),
                restored=payload.get("restored"),
                suspected_restored=payload.get("suspected_restored"),
                deleted=payload.get("deleted"),
                provider_reset=payload.get("provider_reset"),
                listener_permission=self.listener_permission,
                listener_bound=self.listener_bound,
                allowlist_count=self.allowlist_count,
                notification_queue_depth=self.notice_depth,
                notification_queue_drops=self.notice_drops,
                notification_age_drops=self.notice_age_drops,
                notification_filtered=self.notice_filtered,
                allowlist_removed=self.notice_removed,
                notification_rejected=self.notice_rejected,
                listener_gap_count=self.notice_gaps,
            )
            return None
        if type_name == "messages.deleted":
            return self._deleted(payload)
        if type_name.endswith(".result") or type_name == "diagnostic_read.result":
            request_id = str(payload.get("request_id") or "")
            with self._lock:
                event = self.pending_events.pop(request_id, None)
                if event is None:
                    _note("zola_phone.read", req=type_name, status="late-result")
                    return None
                body = {"ok": True, "request_id": request_id, "status": payload.get("status") or "ok"}
                # P10-COMPANION: diagnostic counts stay on the local result — C2
                if type_name == "diagnostic_read.result":
                    for key in (
                        "pending_incomplete",
                        "exhausted",
                        "unacked",
                        "restored",
                        "suspected_restored",
                        "deleted",
                        "provider_reset",
                        "rows_since_baseline",
                        "rejected",
                        "cursor_lag",
                    ):
                        if key in payload:
                            body[key] = payload[key]
                elif type_name == "notifications.read.result":
                    items, capped = cap_notifications(payload.get("items"), self.protocol)
                    body["capped"] = capped
                    body["items"] = items
                elif type_name != "code.read.result":
                    items = payload.get("items")
                    if type_name == "history.read.result":
                        items, capped = cap_history(items, self.protocol)
                        body["capped"] = capped
                        if capped:
                            _note("zola_phone.history", kept=len(items) if isinstance(items, list) else 0, capped=1)
                    body["items"] = items
                else:
                    body["value"] = payload.get("value")
                    # P10-COMPANION: value_kind and reason reach the caller; the value is not logged — C4
                    for key in ("value_kind", "reason"):
                        if key in payload:
                            body[key] = payload.get(key)
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
            delay_ms=self.clock() - int(when_raw),
        )
        return self._ack_for(payload, kind, ack, reason if ack == "rejected" else None)

    def _remember_notice(self, payload: Dict[str, Any]) -> None:
        def num(name: str, default: int = 0) -> int:
            value = payload.get(name, default)
            if isinstance(value, bool) or not isinstance(value, int):
                return default
            return int(value)

        packages = payload.get("allowlist_packages")
        self.listener_permission = num("listener_permission", 1)
        self.listener_bound = num("listener_bound", 1)
        if isinstance(packages, list):
            self.allowlist_packages = [str(item) for item in packages if isinstance(item, str)]
            self.allowlist_count = len(self.allowlist_packages)
        else:
            self.allowlist_packages = []
            self.allowlist_count = num("allowlist_count")
        self.notice_depth = num("notification_queue_depth")
        self.notice_drops = num("notification_queue_drops")
        self.notice_age_drops = num("notification_age_drops")
        self.notice_filtered = num("notification_filtered")
        self.notice_removed = num("allowlist_removed")
        self.notice_rejected = num("notification_rejected")
        self.notice_gaps = num("listener_gap_count")

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

    def _deleted(self, payload: Dict[str, Any]) -> Optional[bytes]:
        # P10-COMPANION: a deleted notice is logged and acknowledged; the store keeps nothing — P10-D03
        kind = str(payload.get("kind") or "")
        revision = payload.get("revision")
        if kind not in ("sms", "mms") or "provider_id" not in payload:
            return self._ack_for(payload, kind or "sms", "rejected", "bad_field")
        if payload.get("outcome") != "deleted":
            return self._ack_for(payload, kind, "rejected", "bad_field")
        if "revision" not in payload or isinstance(revision, bool) or not isinstance(revision, int):
            return self._ack_for(payload, kind, "rejected", "bad_revision")
        identity = _hash("|".join((
            str(payload.get("device_id") or ""),
            kind,
            str(payload.get("provider_id") or ""),
            str(revision),
        )))
        with self._lock:
            seen = list(self.peer.get("deleted_seen") or [])
            repeat = identity in seen
            if not repeat:
                seen.append(identity)
                limit = int(self.protocol.get("deleted_seen_limit") or 2000)
                if len(seen) > limit:
                    seen = seen[-limit:]
                self.peer["deleted_seen"] = seen
                self._save_peer()
        word = "duplicate" if repeat else "suppressed"
        _note("zola_phone.deleted", item=identity, revision=revision, result=word)
        return self._ack_for(payload, kind, word, None)

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


def cap_notifications(items: Any, protocol: Dict[str, Any]) -> Any:
    # P10-NOTIFY: a read result is capped before it is returned and its text is not logged
    if not isinstance(items, list):
        return items, False
    limits = protocol["size_limits"]
    max_items = int(limits["notification_read_items"])
    max_chars = int(limits["notification_read_chars"])
    per_item = int(limits["notification_text_chars"])
    kept = []
    used = 0
    capped = False
    for item in items:
        if len(kept) >= max_items:
            capped = True
            break
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "")
        if len(text) > per_item:
            item = dict(item)
            item["text"] = text[:per_item]
            item["truncated"] = 1
            text = item["text"]
        if used and used + len(text) > max_chars:
            capped = True
            break
        kept.append(item)
        used += len(text)
    return kept, capped


def cap_history(items: Any, protocol: Dict[str, Any]) -> Any:
    # P10-COMPANION: a trimmed history says so; a silent cut would look complete — Phase 5
    if not isinstance(items, list):
        return items, False
    limits = protocol["size_limits"]
    max_items = int(limits["history_messages"])
    max_chars = int(limits["history_chars"])
    kept = []
    used = 0
    capped = False
    for item in items:
        if len(kept) >= max_items:
            capped = True
            break
        if not isinstance(item, dict):
            continue
        text = str(item.get("body") or item.get("text") or "")
        if used and used + len(text) > max_chars:
            capped = True
            break
        if len(text) > max_chars:
            trimmed = dict(item)
            trimmed["body"] = text[:max_chars]
            trimmed["truncated"] = True
            text = trimmed["body"]
            item = trimmed
        kept.append(item)
        used += len(text)
    return kept, capped


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
