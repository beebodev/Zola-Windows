"""zola-phone intake tests. Synthetic ids only (P10-D12)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

PLUGINS = Path(__file__).resolve().parents[2]
if str(PLUGINS) not in sys.path:
    sys.path.insert(0, str(PLUGINS))

from zola_phone import wire
from zola_phone.runtime import Engine, configure_logging, load_store
from zola_phone.serve import allowed_bind, bind_action, create_pipe, pipe_request, serve_pipe

SECRET = "launch-secret-test"
NOW = 1_700_000_000_000
DEVICE = "zp10-device-test"
PYTHON = Path(r"C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe")


def _phone_key():
    key = ec.generate_private_key(ec.SECP256R1())
    private = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("ascii")
    public = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return private, public


def _pipe(name: str, body: dict) -> dict:
    last: Exception | None = None
    for _ in range(20):
        try:
            return pipe_request(name, body)
        except Exception as exc:
            last = exc
            time.sleep(0.05)
    assert last is not None
    raise last


class IntakeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        configure_logging(self.home)
        self.engine = Engine(self.home, SECRET)
        self.engine.clock = lambda: NOW
        self.private, self.public = _phone_key()
        self.seq = 0
        _addr, _match, _ids, store = load_store()
        store.set_ticket_override_for_tests(True)

    def tearDown(self) -> None:
        _addr, _match, _ids, store = load_store()
        store.set_ticket_override_for_tests(None)
        self.engine.close()
        import logging

        for handler in list(logging.getLogger("zola_phone").handlers):
            handler.close()
        logging.getLogger("zola_phone").handlers.clear()
        self.tmp.cleanup()

    def _payload(self, type_name: str, **extra):
        self.seq += 1
        body = {
            "type": type_name,
            "device_id": DEVICE,
            "seq": self.seq,
            "sent_at_ms": NOW,
            "contract_version": 2,
        }
        body.update(extra)
        return body

    def _signed(self, payload, private=None):
        key = self.private if private is None else private
        return wire.encode_frame("signed", payload, wire.sign_payload(key, payload), self.engine.protocol)

    def _pair(self, conn="c1", device=DEVICE, public=None):
        started = self.engine.local_request({"type": "pairing.start", "secret": SECRET})
        self.assertTrue(started["ok"])
        code = started["code"]
        opened = self._payload("phone_open", public_pem=public or self.public, device_id=device)
        raw = wire.encode_frame("pairing", opened, wire.pairing_mac(code, opened), self.engine.protocol)
        bind = self.engine.receive(conn, raw)
        self.assertEqual(self.engine.last_reason, "accept")
        bind_payload = json.loads(bind.decode("utf-8"))["payload"]
        self.assertEqual(bind_payload["type"], "pc_bind")
        self.assertTrue(wire.mac_matches(code, bind_payload, json.loads(bind.decode("utf-8"))["signature"]))
        bound = self._payload("phone_bind", public_pem=public or self.public, device_id=device)
        reply = self.engine.receive(
            conn,
            wire.encode_frame("pairing", bound, wire.pairing_mac(code, bound), self.engine.protocol),
        )
        self.assertEqual(self.engine.last_reason, "accept")
        self.assertEqual(json.loads(reply.decode("utf-8"))["payload"]["type"], "pc_ok")
        return code, reply

    def _event(self, provider="sms-1", body="hello", revision=1):
        payload = self._payload(
            "messages.event",
            provider_id=provider,
            kind="sms",
            revision=revision,
            completeness="complete",
            received_at_ms=NOW,
            sender_raw="+15555550100",
            is_group=0,
            participant_count=1,
            rcs_flag="no",
            body=body,
        )
        return self.engine.receive("c1", self._signed(payload))

    def test_identity_and_size_before_verify(self) -> None:
        _addr, match, _ids, _store = load_store()
        import loops

        self.assertIs(loops.evaluate, match.evaluate)
        before = self.engine.verified_calls
        raw = b"x" * (self.engine.protocol["size_limits"]["frame_bytes"] + 1)
        self.engine.receive("c1", raw)
        self.assertEqual(self.engine.last_reason, "too-large")
        self.assertEqual(self.engine.verified_calls, before)
        both = wire.encode_frame(
            "signed",
            self._payload("messages.event", body="short", kind="sms"),
            "",
            self.engine.protocol,
        ) + raw
        self.engine.receive("c1", both)
        self.assertEqual(self.engine.last_reason, "too-large")
        self.assertEqual(self.engine.verified_calls, before)
        log = (self.home / "logs" / "zola_phone.log").read_text(encoding="utf-8")
        self.assertNotIn("unsigned", log)
        unsigned = wire.encode_frame(
            "signed",
            self._payload("messages.event", body="Z" * 16001, kind="sms"),
            "",
            self.engine.protocol,
        )
        self.engine.receive("c1", unsigned)
        self.assertEqual(self.engine.last_reason, "unsigned")
        self.assertEqual(self.engine.verified_calls, before)

    def test_version_rejected(self) -> None:
        self._pair()
        payload = self._payload("messages.event", contract_version=99, kind="sms", provider_id="sms-v", revision=1, completeness="complete", received_at_ms=NOW, sender_raw="+15555550100", is_group=0, body="x")
        self.engine.receive("c1", self._signed(payload))
        self.assertEqual(self.engine.last_reason, "version")

    def test_pair_ingest_ack_and_watch(self) -> None:
        code, reply = self._pair()
        self.assertIsNotNone(reply)
        log = (self.home / "logs" / "zola_phone.log").read_text(encoding="utf-8")
        self.assertNotIn(code, log)
        _addr, _match, _ids, store = load_store()
        store.insert_loop(
            self.engine.conn,
            intent="fixture",
            predicate={"op": "all", "args": []},
            session_id="sess-zp10",
            name_source="mail",
        )
        ack = self._event()
        parsed = json.loads(ack.decode("utf-8"))
        self.assertEqual(parsed["payload"]["result"], "stored")
        row = self.engine.conn.execute("SELECT watch_evaluated, loop_matched FROM items").fetchone()
        self.assertEqual(row["watch_evaluated"], 1)
        self.assertEqual(row["loop_matched"], 1)

    def test_resend_after_crash_and_restart_replay(self) -> None:
        self._pair()

        def boom(name):
            if name == "after_commit":
                raise RuntimeError("between commit and ack")

        self.engine.fault = boom
        with self.assertRaises(RuntimeError):
            self._event(provider="sms-crash")
        self.engine.fault = None
        again = self._event(provider="sms-crash")
        self.assertEqual(json.loads(again.decode("utf-8"))["payload"]["result"], "duplicate")
        phone_seq = int(self.engine.peer["phone_seq"])
        self.engine.close()
        restarted = Engine(self.home, SECRET)
        restarted.clock = lambda: NOW
        self.engine = restarted
        stale = self._payload("messages.event", seq=phone_seq, kind="sms", provider_id="sms-old", revision=1, completeness="complete", received_at_ms=NOW, sender_raw="+15555550100", is_group=0, body="old")
        self.engine.receive("c1", self._signed(stale))
        self.assertEqual(self.engine.last_reason, "replay")

    def test_watch_recovery_both_faults(self) -> None:
        self._pair()

        def before_eval(name):
            if name == "before_eval":
                raise RuntimeError("before eval")

        self.engine.fault = before_eval
        with self.assertRaises(RuntimeError):
            self._event(provider="sms-eval")
        self.engine.close()
        recovered = Engine(self.home, SECRET)
        row = recovered.conn.execute("SELECT watch_evaluated FROM items").fetchone()
        self.assertEqual(row["watch_evaluated"], 1)
        recovered.close()
        self.engine = Engine(self.home, SECRET)
        self.engine.clock = lambda: NOW
        self.private, self.public = self.private, self.public

        def before_ack(name):
            if name == "before_ack":
                raise RuntimeError("before ack")

        self._pair()
        self.engine.fault = before_ack
        with self.assertRaises(RuntimeError):
            self._event(provider="sms-ack")
        rows = self.engine.conn.execute("SELECT watch_evaluated FROM items").fetchall()
        self.assertTrue(rows)
        self.assertTrue(all(row["watch_evaluated"] == 1 for row in rows))

    def test_supersede_only_after_auth(self) -> None:
        self._pair()
        self._event(provider="sms-live")
        closed = []
        self.engine.closer = closed.append
        bad_key, bad_pub = _phone_key()
        payload = self._payload("messages.event", kind="sms", provider_id="sms-bad", revision=1, completeness="complete", received_at_ms=NOW, sender_raw="+15555550100", is_group=0, body="no")
        self.engine.receive("c2", self._signed(payload, bad_key))
        self.assertEqual(self.engine.last_reason, "bad-signature")
        self.assertEqual(self.engine.current, "c1")
        self.assertEqual(closed, [])
        good = self._payload("messages.event", kind="sms", provider_id="sms-next", revision=1, completeness="complete", received_at_ms=NOW, sender_raw="+15555550100", is_group=0, body="yes")
        self.engine.receive("c2", self._signed(good))
        self.assertEqual(self.engine.current, "c2")
        self.assertEqual(closed, ["c1"])
        self.assertEqual(bad_pub[:0], "")

    def test_old_key_unknown_after_repair(self) -> None:
        self._pair()
        old_private = self.private
        self.private, self.public = _phone_key()
        self._pair(device=DEVICE, public=self.public)
        payload = self._payload("messages.event", kind="sms", provider_id="sms-oldkey", revision=1, completeness="complete", received_at_ms=NOW, sender_raw="+15555550100", is_group=0, body="old")
        self.engine.receive("c1", self._signed(payload, old_private))
        self.assertEqual(self.engine.last_reason, "unknown-key")

    def test_health_states(self) -> None:
        self.assertEqual(self.engine.link_state(), "not_paired")
        self._pair()
        self.engine.note_socket(True)
        self.engine.last_ping_answered = True
        self.assertEqual(self.engine.link_state(), "connected")
        self.assertFalse(self.engine.note_pong_miss())
        self.assertEqual(self.engine.link_state(), "not_responding")
        self.assertTrue(self.engine.note_pong_miss())
        self.assertEqual(self.engine.link_state(), "reconnecting")
        self.engine.closed_at_ms = NOW - 480000
        self.assertEqual(self.engine.link_state(), "offline")
        self.engine.tailnet = False
        self.assertEqual(self.engine.link_state(), "no_tailnet")

    def test_secret_and_read_code_not_logged(self) -> None:
        status = self.engine.local_request({"type": "status"})
        self.assertTrue(status["ok"])
        denied = self.engine.local_request({"type": "read_history"})
        self.assertEqual(denied["reason"], "unauthorized")
        self._pair()
        self.engine.socket_open = True
        self.engine.protocol["timing_ms"]["read_timeout"] = 200
        sent = {}

        def late(frame):
            sent["frame"] = frame

        self.engine.sender = late
        result = self.engine.local_request({"type": "read_code", "secret": SECRET, "provider_id": "sms-1", "kind": "sms"})
        self.assertEqual(result["reason"], "timeout")
        value = "ZP10-CODE-SENTINEL"
        payload = self._payload("code.read.result", request_id=json.loads(sent["frame"].decode("utf-8"))["payload"]["request_id"], status="ok", value=value)
        self.engine.receive("c1", self._signed(payload))
        log = (self.home / "logs" / "zola_phone.log").read_text(encoding="utf-8")
        self.assertIn("late-result", log)
        self.assertNotIn(value, log)
        self.assertNotIn(SECRET, log)

    def test_bind_allows_only_the_tailnet_address(self) -> None:
        port = 47821
        self.assertTrue(allowed_bind("100.102.206.71", port, port))
        self.assertFalse(allowed_bind("0.0.0.0", port, port))
        self.assertFalse(allowed_bind("192.168.1.9", port, port))
        self.assertFalse(allowed_bind("100.102.206.71", 8765, 8765))

    def test_pipe_secret(self) -> None:
        name = r"\\.\pipe\ZolaPhoneTest" + str(os.getpid())
        self.engine.protocol["pipe_name"] = name
        stop = threading.Event()
        threading.Thread(target=serve_pipe, args=(self.engine, stop), daemon=True).start()
        status = _pipe(name, {"type": "status"})
        self.assertEqual(status["link_state"], "not_paired")
        denied = _pipe(name, {"type": "pairing.start"})
        self.assertEqual(denied["reason"], "unauthorized")
        with self.assertRaises(Exception):
            create_pipe(name, first=True)
        stop.set()

    def test_isolation_on_the_real_startup_path(self) -> None:
        env = os.environ.copy()
        env.pop("ZOLA_PHONE_ISOLATION_PROBE", None)
        env["HERMES_HOME"] = str(self.home)
        env["PYTHONPATH"] = str(PLUGINS)
        env["ZOLA_PHONE_LAUNCH_SECRET"] = "isolation-secret"
        env["ZOLA_PHONE_LISTEN_PORT"] = "0"
        proc = subprocess.Popen(
            [str(PYTHON), "-m", "zola_phone"],
            cwd=str(PLUGINS),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            log = self.home / "logs" / "zola_phone.log"
            deadline = time.time() + 20
            text = ""
            while time.time() < deadline:
                if log.exists():
                    text = log.read_text(encoding="utf-8")
                    if "zola_phone.start" in text:
                        break
                if proc.poll() is not None:
                    break
                time.sleep(0.1)
            self.assertIn("zola_phone.start", text)
            self.assertIn("forbidden=-", text)
            for name in ("gmail", "read_common", "loops", "taint", "turn_context", "recorded_results"):
                self.assertNotIn(name, text.split("forbidden=", 1)[-1])
            self.assertNotIn("isolation-secret", text)
        finally:
            proc.kill()
            proc.wait(timeout=10)

    def test_f7_lan_address_is_not_a_tailnet(self) -> None:
        port = 47821
        self.assertFalse(allowed_bind("192.168.1.9", port, port))
        self.assertFalse(allowed_bind("0.0.0.0", port, port))
        self.assertFalse(allowed_bind("", port, port))
        self.assertFalse(allowed_bind("not-an-ip", port, port))

    def test_f6_missing_revision_stores_nothing(self) -> None:
        self._pair()
        payload = self._payload(
            "messages.event",
            provider_id="sms-missing",
            kind="sms",
            completeness="complete",
            received_at_ms=NOW,
            sender_raw="+15555550100",
            is_group=0,
            body="x",
        )
        payload.pop("revision", None)
        ack = self.engine.receive("c1", self._signed(payload))
        parsed = json.loads(ack.decode("utf-8"))["payload"]
        self.assertEqual(parsed["reason"], "bad_revision")
        count = self.engine.conn.execute("SELECT COUNT(*) AS n FROM items").fetchone()["n"]
        self.assertEqual(count, 0)

    def test_f1_two_missed_pongs_close(self) -> None:
        self._pair()
        self.engine.socket_open = True
        self.engine.current = "c1"
        self.engine.last_frame_ms = NOW
        self.engine.next_ping_ms = NOW
        clock = {"now": NOW}
        self.engine.clock = lambda: clock["now"]
        self.assertEqual(self.engine.keepalive_step(), "ping")
        clock["now"] += 15000
        self.assertEqual(self.engine.keepalive_step(), "miss")
        self.assertEqual(self.engine.link_state(), "not_responding")
        self.assertTrue(self.engine.socket_open)
        self.engine.next_ping_ms = clock["now"]
        self.assertEqual(self.engine.keepalive_step(), "ping")
        clock["now"] += 15000
        self.assertEqual(self.engine.keepalive_step(), "close")
        self.assertFalse(self.engine.socket_open)
        log = (self.home / "logs" / "zola_phone.log").read_text(encoding="utf-8")
        self.assertIn("pong-missed", log)
        self.assertIn("who=pc", log)

    def test_f1_pong_restores_and_read_timeout_pings(self) -> None:
        self._pair()
        self.engine.socket_open = True
        self.engine.current = "c1"
        clock = {"now": NOW}
        self.engine.clock = lambda: clock["now"]
        self.engine.last_frame_ms = NOW
        self.engine.next_ping_ms = NOW
        self.assertEqual(self.engine.keepalive_step(), "ping")
        clock["now"] += 15000
        self.assertEqual(self.engine.keepalive_step(), "miss")
        pong = self._payload("keepalive.pong")
        self.engine.receive("c1", self._signed(pong))
        self.assertEqual(self.engine.link_state(), "connected")
        self.engine.next_ping_ms = clock["now"] + 240000
        self.engine.last_frame_ms = clock["now"]
        self.engine.awaiting_pong = False
        clock["now"] += 15000
        self.assertEqual(self.engine.keepalive_step(), "wait")
        clock["now"] += 240000 - 15000
        self.assertEqual(self.engine.keepalive_step(), "ping")

    def test_f12_idle_link_pings_every_four_minutes(self) -> None:
        self._pair()
        self.engine.socket_open = True
        self.engine.current = "c1"
        clock = {"now": NOW}
        self.engine.clock = lambda: clock["now"]
        self.engine.last_frame_ms = NOW
        self.engine.next_ping_ms = NOW + 240000
        self.engine.awaiting_pong = False
        pings = []
        end = NOW + 20 * 60 * 1000
        while clock["now"] <= end:
            if self.engine.keepalive_step() == "ping":
                pings.append(clock["now"])
                self.engine.receive(
                    "c1",
                    self._signed(self._payload("keepalive.pong", sent_at_ms=clock["now"])),
                )
            clock["now"] += 1000
        self.assertEqual(pings, [NOW + 240000 * i for i in range(1, 6)])

        clock["now"] = NOW
        self.engine.socket_open = True
        self.engine.current = "c1"
        self.engine.next_ping_ms = NOW + 240000
        self.engine.awaiting_pong = False
        self.engine.misses = 0
        self.engine.last_ping_answered = True
        self.engine.protocol["timing_ms"]["read_timeout"] = 30
        self.engine.sender = lambda _frame: None
        timed = self.engine.local_request({"type": "read_history", "secret": SECRET, "request_id": "f12-read"})
        self.assertEqual(timed["reason"], "timeout")
        self.assertEqual(self.engine.keepalive_step(), "ping")
        self.assertEqual(self.engine.keepalive_step(), "wait")
        clock["now"] += 15000
        self.assertEqual(self.engine.keepalive_step(), "miss")
        self.assertEqual(self.engine.link_state(), "not_responding")
        self.assertTrue(self.engine.socket_open)
        self.engine.next_ping_ms = clock["now"]
        self.assertEqual(self.engine.keepalive_step(), "ping")
        clock["now"] += 15000
        self.assertEqual(self.engine.keepalive_step(), "close")
        self.assertFalse(self.engine.socket_open)

    def test_f2_stranger_receives_nothing(self) -> None:
        from zola_phone.serve import adopt_after_frame

        self._pair()
        seen = []

        def record(frame: bytes) -> None:
            seen.append(frame)

        self.engine.socket_open = True
        self.engine.current = "c1"
        self.engine.sender = record
        self.engine._sender_conn = "c1"
        stranger = []
        self.engine.last_reason = "malformed"
        self.assertFalse(adopt_after_frame(self.engine, "c2", stranger.append, b"no"))
        self.assertEqual(stranger, [])
        self.assertIs(self.engine.sender, record)
        self.engine.protocol["timing_ms"]["read_timeout"] = 200
        result = self.engine.local_request({"type": "read_history", "secret": SECRET, "request_id": "r-f2"})
        self.assertEqual(result["reason"], "timeout")
        self.assertEqual(len(seen), 1)
        self.assertEqual(stranger, [])

    def test_f2_frames_do_not_interleave(self) -> None:
        import asyncio
        from zola_phone.serve import FrameWriter

        async def run() -> None:
            busy = {"n": 0, "bad": False}
            sent = []

            async def send(frame: bytes) -> None:
                if busy["n"]:
                    busy["bad"] = True
                busy["n"] += 1
                await asyncio.sleep(0.02)
                busy["n"] -= 1
                sent.append(frame)

            writer = FrameWriter(send, asyncio.get_running_loop())
            writer.submit(b"a")
            writer.submit(b"b")
            await asyncio.sleep(0.1)
            writer.close()
            await writer._task
            self.assertFalse(busy["bad"])
            self.assertEqual(sent, [b"a", b"b"])

        asyncio.run(run())

    def test_f3_concurrent_relays_use_distinct_seqs(self) -> None:
        import queue

        self._pair()
        self.engine.socket_open = True
        self.engine.current = "c1"
        self.engine.protocol["timing_ms"]["read_timeout"] = 5000
        seqs = []
        pending = queue.Queue()

        def sender(frame: bytes) -> None:
            payload = json.loads(frame.decode("utf-8"))["payload"]
            seqs.append(payload["seq"])
            pending.put(payload["request_id"])

        self.engine.sender = sender
        phone = {"n": int(self.engine.peer["phone_seq"])}

        def complete() -> None:
            while True:
                request_id = pending.get()
                if request_id is None:
                    return
                phone["n"] += 1
                payload = {
                    "type": "history.read.result",
                    "device_id": DEVICE,
                    "seq": phone["n"],
                    "sent_at_ms": NOW,
                    "contract_version": 2,
                    "request_id": request_id,
                    "status": "ok",
                    "items": [],
                }
                self.engine.receive("c1", self._signed(payload))

        threading.Thread(target=complete, daemon=True).start()
        results = []

        def relay(index: int) -> None:
            results.append(self.engine.local_request({"type": "read_history", "secret": SECRET, "request_id": f"r{index}"}))

        threads = [threading.Thread(target=relay, args=(index,)) for index in range(50)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=8)
        pending.put(None)
        self.assertEqual(len(results), 50)
        self.assertTrue(all(item.get("ok") for item in results))
        self.assertEqual(seqs, sorted(seqs))
        self.assertEqual(len(set(seqs)), 50)

    def test_f4_status_answers_while_a_read_waits(self) -> None:
        self._pair()
        self.engine.socket_open = True
        self.engine.current = "c1"
        self.engine.sender = lambda _frame: None
        self.engine.protocol["timing_ms"]["read_timeout"] = 3000
        name = r"\\.\pipe\ZolaPhoneStat" + str(os.getpid())
        self.engine.protocol["pipe_name"] = name
        stop = threading.Event()
        threading.Thread(target=serve_pipe, args=(self.engine, stop), daemon=True).start()
        threading.Thread(
            target=lambda: _pipe(name, {"type": "read_history", "secret": SECRET}),
            daemon=True,
        ).start()
        time.sleep(0.3)
        started = time.time()
        status = _pipe(name, {"type": "status"})
        self.assertLess(time.time() - started, 1)
        self.assertEqual(status["link_state"], "connected")
        stop.set()

    def test_f4_long_history_line_arrives_whole(self) -> None:
        import win32file
        import win32pipe

        name = r"\\.\pipe\ZolaPhoneLong" + str(os.getpid())
        body = "Z" * 64000

        def server() -> None:
            handle = create_pipe(name, first=True)
            win32pipe.ConnectNamedPipe(handle, None)
            from zola_phone.serve import read_pipe_line

            read_pipe_line(handle)
            win32file.WriteFile(handle, (json.dumps({"text": body}) + "\n").encode("utf-8"))
            win32file.CloseHandle(handle)

        threading.Thread(target=server, daemon=True).start()
        got = _pipe(name, {"type": "status"})
        self.assertEqual(got["text"], body)

    def test_f6_fields_and_notification_ack(self) -> None:
        self._pair()
        missing_time = self._payload(
            "messages.event",
            provider_id="sms-time",
            kind="sms",
            revision=1,
            completeness="complete",
            sender_raw="+15555550100",
            is_group=0,
            body="x",
        )
        missing_time.pop("received_at_ms", None)
        ack = json.loads(self.engine.receive("c1", self._signed(missing_time)).decode("utf-8"))["payload"]
        self.assertEqual(ack["reason"], "bad_time")
        bad_complete = self._payload(
            "messages.event",
            provider_id="sms-comp",
            kind="sms",
            revision=1,
            completeness="incomplete",
            received_at_ms=NOW,
            sender_raw="+15555550100",
            is_group=0,
            body="x",
        )
        ack = json.loads(self.engine.receive("c1", self._signed(bad_complete)).decode("utf-8"))["payload"]
        self.assertEqual(ack["reason"], "bad_completeness")
        attached = self._payload(
            "messages.event",
            provider_id="sms-file",
            kind="sms",
            revision=1,
            completeness="complete",
            received_at_ms=NOW,
            sender_raw="+15555550100",
            is_group=0,
            body="x",
            attachment_has=1,
            attachment_count=2,
            attachment_kind="image",
        )
        self.engine.receive("c1", self._signed(attached))
        row = self.engine.conn.execute(
            "SELECT attachment_has, attachment_count, attachment_kind FROM items"
        ).fetchone()
        self.assertEqual(tuple(row), (1, 2, "image"))
        note = self._payload(
            "notifications.event",
            package="com.zp10.app",
            notification_key="n1",
            newest_message_timestamp="1000",
            revision=1,
            completeness="complete",
            posted_at_ms=NOW,
            text="ZP10",
            is_group=0,
        )
        ack = json.loads(self.engine.receive("c1", self._signed(note)).decode("utf-8"))["payload"]
        self.assertEqual(ack["type"], "notifications.ack")
        self.assertEqual(ack["package"], "com.zp10.app")
        self.assertEqual(ack["notification_key"], "n1")
        self.assertEqual(ack["newest_message_timestamp"], "1000")

    def test_f7_address_change_rebinds(self) -> None:
        self.assertEqual(bind_action("", "100.64.0.1", 47821, 47821), "rebind")
        self.assertEqual(bind_action("100.64.0.1", "100.64.0.1", 47821, 47821), "keep")
        self.assertEqual(bind_action("100.64.0.1", "100.64.0.2", 47821, 47821), "rebind")
        self.assertEqual(bind_action("100.64.0.1", "10.0.0.8", 47821, 47821), "refuse")
        self.assertEqual(bind_action("100.64.0.1", "", 47821, 47821), "refuse")

    def test_f5_secret_is_removed_before_tools(self) -> None:
        import importlib.util

        path = PLUGINS / "zola_workspace" / "launch_secret.py"
        spec = importlib.util.spec_from_file_location("launch_secret_phase5", path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        os.environ[module.SECRET_ENV] = "sentinel-secret-value"
        self.addCleanup(lambda: os.environ.pop(module.SECRET_ENV, None))
        self.assertEqual(module.take(), "sentinel-secret-value")
        self.assertNotIn(module.SECRET_ENV, os.environ)
        done = subprocess.run(
            [str(PYTHON), "-c", "import os; print(os.environ.get('ZOLA_PHONE_LAUNCH_SECRET',''))"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(done.stdout.strip(), "")
        register = (PLUGINS / "zola_workspace" / "__init__.py").read_text(encoding="utf-8")
        self.assertLess(register.find("launch_secret.take()"), register.find("ctx.register_tool"))
        self.assertNotIn("sentinel-secret-value", (self.home / "logs" / "zola_phone.log").read_text(encoding="utf-8"))

    def test_f9_vectors_results_and_local_reasons(self) -> None:
        root = PLUGINS / "zola_workspace" / "contracts"
        protocol = wire.load_protocol()
        keys = json.loads((root / "phone_test_keys.json").read_text(encoding="utf-8"))
        vectors = json.loads((root / "phone_vectors.json").read_text(encoding="utf-8"))
        for case in vectors["cases"]:
            self.assertEqual(wire.decide_case(case, protocol, keys, vectors), case["expect"], case["name"])
        denied = self.engine.local_request({"type": "read_code"})
        self.assertEqual(denied["reason"], "unauthorized")
        self._pair()
        unavailable = self.engine.local_request({"type": "read_code", "secret": SECRET})
        self.assertEqual(unavailable["reason"], "no_connection")
        self.engine.socket_open = True
        self.engine.sender = lambda _frame: None
        self.engine.peer["device_id"] = ""
        not_paired = self.engine.local_request({"type": "diagnostic_read", "secret": SECRET})
        self.assertEqual(not_paired["reason"], "not_paired")
        self.engine.peer["device_id"] = DEVICE
        self.engine.protocol["timing_ms"]["read_timeout"] = 200
        timed = self.engine.local_request({"type": "read_notifications", "secret": SECRET, "request_id": "late-1"})
        self.assertEqual(timed["reason"], "timeout")
        payload = self._payload("code.read.result", request_id="late-1", status="ok", value="ZP10-CODE-SENTINEL")
        self.engine.receive("c1", self._signed(payload))
        log = (self.home / "logs" / "zola_phone.log").read_text(encoding="utf-8")
        self.assertIn("late-result", log)
        self.assertNotIn("ZP10-CODE-SENTINEL", log)

    def test_f9_ack_words_and_source_scan(self) -> None:
        self._pair()
        _addr, _match, _ids, store = load_store()
        first = self._event(provider="sms-word", revision=1)
        self.assertEqual(json.loads(first.decode("utf-8"))["payload"]["result"], "stored")
        again = self._event(provider="sms-word", revision=1)
        self.assertEqual(json.loads(again.decode("utf-8"))["payload"]["result"], "duplicate")
        higher = self._event(provider="sms-word", revision=2)
        self.assertEqual(json.loads(higher.decode("utf-8"))["payload"]["result"], "updated")
        lower = self._event(provider="sms-word", revision=1)
        self.assertEqual(json.loads(lower.decode("utf-8"))["payload"]["result"], "duplicate")
        identity = store._phone_identity(
            kind="sms",
            device_id=DEVICE,
            provider_id="sms-tomb",
            package="",
            notification_key="",
            newest_message_timestamp="",
        )
        store.record_phone_tombstone(self.engine.conn, identity)
        buried = self._event(provider="sms-tomb", revision=1)
        self.assertEqual(json.loads(buried.decode("utf-8"))["payload"]["result"], "suppressed")
        hits = []
        for path in PLUGINS.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".cs"}:
                continue
            if "tests" in path.parts or path.name == "phone_test_keys.json":
                continue
            if "phone_test_keys.json" in path.read_text(encoding="utf-8", errors="ignore"):
                hits.append(str(path))
        self.assertEqual(hits, [])
        done = subprocess.run(
            [str(PYTHON), "-m", "zola_phone.tools.fake_phone", "--help"],
            cwd=str(PLUGINS),
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        for word in ("text", "notification", "ping", "read", "bad", "second", "half-open", "oversize", "separator"):
            self.assertIn(word, done.stdout)

    def test_f9_five_wrong_codes_invalidate_and_an_expired_code_is_refused(self) -> None:
        started = self.engine.local_request({"type": "pairing.start", "secret": SECRET})
        code = started["code"]
        opened = self._payload("phone_open", public_pem=self.public, device_id=DEVICE)
        for _ in range(5):
            wrong = wire.encode_frame(
                "pairing", opened, wire.pairing_mac("00000000", opened), self.engine.protocol
            )
            self.assertIsNone(self.engine.receive("c1", wrong))
            self.assertEqual(self.engine.last_reason, "bad-signature")
        self.assertTrue(self.engine.code_dead)
        log = (self.home / "logs" / "zola_phone.log").read_text(encoding="utf-8")
        self.assertIn("invalidated", log)
        still = wire.encode_frame("pairing", opened, wire.pairing_mac(code, opened), self.engine.protocol)
        self.assertIsNone(self.engine.receive("c1", still))
        self.assertFalse(self.engine.peer.get("device_id"))

        self.engine.clock = lambda: NOW
        again = self.engine.local_request({"type": "pairing.start", "secret": SECRET})
        self.assertTrue(again["ok"])
        self.engine.code_expires = NOW - 1
        fresh = self._payload("phone_open", public_pem=self.public, device_id=DEVICE)
        expired = wire.encode_frame(
            "pairing", fresh, wire.pairing_mac(again["code"], fresh), self.engine.protocol
        )
        self.assertIsNone(self.engine.receive("c1", expired))
        log = (self.home / "logs" / "zola_phone.log").read_text(encoding="utf-8")
        self.assertIn("pairing-expired", log)
        self.assertFalse(self.engine.peer.get("device_id"))

    def test_f4_second_process_refuses_the_pipe_and_mutex(self) -> None:
        env = os.environ.copy()
        env["HERMES_HOME"] = str(self.home)
        env["PYTHONPATH"] = str(PLUGINS)
        env["ZOLA_PHONE_LAUNCH_SECRET"] = "second-secret"
        env["ZOLA_PHONE_LISTEN_PORT"] = "0"
        first = subprocess.Popen(
            [str(PYTHON), "-m", "zola_phone"],
            cwd=str(PLUGINS),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            log = self.home / "logs" / "zola_phone.log"
            deadline = time.time() + 20
            while time.time() < deadline and first.poll() is None:
                if log.exists() and "zola_phone.start" in log.read_text(encoding="utf-8"):
                    break
                time.sleep(0.1)
            self.assertIsNone(first.poll())
            second = subprocess.run(
                [str(PYTHON), "-m", "zola_phone"],
                cwd=str(PLUGINS),
                env=env,
                capture_output=True,
                text=True,
                timeout=20,
            )
            self.assertEqual(second.returncode, 2, second.stderr)
            with self.assertRaises(Exception):
                create_pipe(r"\\.\pipe\ZolaPhone", first=True)
        finally:
            first.kill()
            first.wait(timeout=10)
            time.sleep(0.4)


if __name__ == "__main__":
    unittest.main()
