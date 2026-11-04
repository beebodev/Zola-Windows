"""P10-READ: zola-phone code arm / redeem / disarm (mechanism B). The value is a synthetic sentinel."""

from __future__ import annotations

import json
import queue
import sys
import threading
import unittest
from pathlib import Path

PLUGINS = Path(__file__).resolve().parents[2]
if str(PLUGINS) not in sys.path:
    sys.path.insert(0, str(PLUGINS))

try:
    from . import test_p10_intake as intake  # a module, so its TestCase is not collected twice
except ImportError:  # flat discovery
    import test_p10_intake as intake  # type: ignore

DEVICE, NOW, SECRET = intake.DEVICE, intake.NOW, intake.SECRET

SENTINEL = "ZP10-READ-CODE-SENTINEL-4471"
SESSION = "gw-session-1"
TURN = "turn-1"
ITEM = "item-1"
ARM = {"session_id": SESSION, "turn_id": TURN, "item_id": ITEM, "provider_id": "sms-1", "kind": "sms"}


class CodeArmTests(unittest.TestCase):
    def setUp(self) -> None:
        # P10-READ: reuse the intake harness (real engine, real pairing, signed phone frames)
        self.h = intake.IntakeTests("test_bind_allows_only_the_tailnet_address")
        self.h.setUp()
        self.addCleanup(self.h.tearDown)
        self.engine = self.h.engine
        self.clock = {"now": NOW}
        self.engine.clock = lambda: self.clock["now"]
        self.h._pair()
        self.engine.socket_open = True
        self.engine.current = "c1"
        self.frames: "queue.Queue[dict]" = queue.Queue()
        self.engine.sender = lambda frame: self.frames.put(json.loads(frame.decode("utf-8"))["payload"])
        self.phone_seq = int(self.engine.peer["phone_seq"])
        self.engine.protocol["timing_ms"]["read_timeout"] = 5000

    def _local(self, name: str, **fields):
        return self.engine.local_request(dict({"type": name, "secret": SECRET}, **fields))

    def _arm(self, **overrides):
        return self._local("code.arm", **dict(ARM, **overrides))

    def _answer(self, status: str = "ok", value: str = SENTINEL, reason: str = "", delay_hook=None) -> None:
        """The phone: answer the next code.read.request with a signed result."""
        request = self.frames.get(timeout=5)
        self.assertEqual(request["type"], "code.read.request")
        if delay_hook:
            delay_hook()
        self.phone_seq += 1
        body = {
            "type": "code.read.result",
            "device_id": DEVICE,
            "seq": self.phone_seq,
            "sent_at_ms": NOW,
            "contract_version": int(self.engine.protocol["contract_version"]),
            "request_id": request["request_id"],
            "status": status,
        }
        if status == "ok":
            body.update(value=value, value_kind="code")
        if reason:
            body["reason"] = reason
        self.engine.receive("c1", self.h._signed(body))

    def _redeem(self, handle: str, answer=True, **fields):
        fields.setdefault("session_id", SESSION)
        box = {}
        worker = threading.Thread(target=lambda: box.update(r=self._local("code.redeem", handle=handle, **fields)), daemon=True)
        worker.start()
        if answer:
            self._answer()
        worker.join(timeout=8)
        self.assertFalse(worker.is_alive())
        return box["r"]

    def _log(self) -> str:
        path = self.h.home / "logs" / "zola_phone.log"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    # ── contract: v4 is unchanged and v4 frames are still accepted ────────────────────────────

    def test_contract_stays_v4_and_new_requests_are_pc_local_secret(self) -> None:
        protocol = self.engine.protocol
        self.assertEqual(protocol["contract_version"], 4)
        self.assertEqual(protocol["supported_versions"], [4])
        for name in ("code.arm", "code.redeem", "code.disarm"):
            self.assertTrue(protocol["local_requests"][name]["secret"], name)
        raw = json.loads((PLUGINS / "zola_workspace" / "contracts" / "phone_protocol.json").read_text(encoding="utf-8"))
        self.assertEqual((raw["contract_version"], raw["supported_versions"]), (4, [4]))

    def test_a_v4_phone_frame_is_still_accepted(self) -> None:
        self.h._event()
        self.assertEqual(self.engine.last_reason, "accept")

    # ── arm ───────────────────────────────────────────────────────────────────────────────────

    def test_arm_needs_the_launch_secret(self) -> None:
        refused = self.engine.local_request(dict({"type": "code.arm"}, **ARM))
        self.assertEqual(refused["reason"], "unauthorized")
        wrong = self.engine.local_request(dict({"type": "code.arm", "secret": "nope"}, **ARM))
        self.assertEqual(wrong["reason"], "unauthorized")

    def test_arm_returns_an_opaque_handle_and_the_ttl(self) -> None:
        armed = self._arm()
        self.assertTrue(armed["ok"])
        self.assertEqual(armed["ttl_ms"], 60_000)
        self.assertNotIn(SENTINEL, json.dumps(armed))
        self.assertGreaterEqual(len(armed["handle"]), 24)

    def test_arm_refuses_missing_binding_and_bad_kind(self) -> None:
        for name in ARM:
            fields = dict(ARM)
            fields.pop(name)
            self.assertEqual(self._local("code.arm", **fields)["reason"], "bad_request", name)
        self.assertEqual(self._arm(kind="notif")["reason"], "bad_request")

    def test_arm_needs_a_paired_live_phone(self) -> None:
        self.engine.socket_open = False
        self.assertEqual(self._arm()["reason"], "no_connection")

    # ── redeem ────────────────────────────────────────────────────────────────────────────────

    def test_redeem_returns_the_value_to_the_caller_only_and_logs_nothing(self) -> None:
        handle = self._arm()["handle"]
        result = self._redeem(handle)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["value"], SENTINEL)
        self.assertEqual(result["value_kind"], "code")
        log = self._log()
        self.assertNotIn(SENTINEL, log)
        self.assertNotIn(handle, log)
        self.assertNotIn(SECRET, log)

    def test_redeem_is_single_use(self) -> None:
        handle = self._arm()["handle"]
        self.assertTrue(self._redeem(handle)["ok"])
        replay = self._redeem(handle, answer=False)
        self.assertEqual(replay["reason"], "replay")
        self.assertNotIn("value", replay)
        self.assertTrue(self.frames.empty(), "a replay must not reach the phone")

    def test_redeem_refuses_wrong_session_turn_item_without_asking_the_phone(self) -> None:
        handle = self._arm()["handle"]
        self.assertEqual(self._redeem(handle, answer=False, session_id="other")["reason"], "wrong_session")
        self.assertEqual(self._redeem(handle, answer=False, turn_id="turn-2")["reason"], "wrong_turn")
        self.assertEqual(self._redeem(handle, answer=False, item_id="item-2")["reason"], "wrong_item")
        self.assertTrue(self.frames.empty())
        # a wrong-binding try does not spend the handle
        self.assertTrue(self._redeem(handle, turn_id=TURN, item_id=ITEM)["ok"])

    def test_redeem_unknown_handle(self) -> None:
        self.assertEqual(self._redeem("not-a-handle", answer=False)["reason"], "unknown_handle")

    def test_redeem_refuses_after_the_60_second_ttl(self) -> None:
        handle = self._arm()["handle"]
        self.clock["now"] += 59_000
        self.assertTrue(self._local("code.arm", **dict(ARM, session_id="s2"))["ok"])
        self.clock["now"] += 1_001
        self.assertEqual(self._redeem(handle, answer=False)["reason"], "expired")
        self.assertTrue(self.frames.empty())

    def test_the_phone_refusal_passes_through_without_a_value(self) -> None:
        handle = self._arm()["handle"]
        box = {}
        worker = threading.Thread(target=lambda: box.update(r=self._local("code.redeem", handle=handle, session_id=SESSION)), daemon=True)
        worker.start()
        self._answer(status="refused", reason="not_identifiable")
        worker.join(timeout=8)
        self.assertFalse(box["r"]["ok"])
        self.assertEqual(box["r"]["reason"], "not_identifiable")
        self.assertNotIn("value", box["r"])
        self.assertEqual(self._redeem(handle, answer=False)["reason"], "replay")

    # ── disarm ────────────────────────────────────────────────────────────────────────────────

    def test_disarm_before_redeem_spends_the_handle(self) -> None:
        handle = self._arm()["handle"]
        self.assertEqual(self._local("code.disarm", handle=handle)["disarmed"], 1)
        self.assertEqual(self._redeem(handle, answer=False)["reason"], "unknown_handle")
        self.assertTrue(self.frames.empty())

    def test_disarm_during_redeem_discards_the_value(self) -> None:
        handle = self._arm()["handle"]
        box = {}
        worker = threading.Thread(target=lambda: box.update(r=self._local("code.redeem", handle=handle, session_id=SESSION)), daemon=True)
        worker.start()
        self._answer(delay_hook=lambda: self._local("code.disarm", handle=handle))
        worker.join(timeout=8)
        self.assertFalse(box["r"]["ok"])
        self.assertEqual(box["r"]["reason"], "cancelled")
        self.assertNotIn(SENTINEL, json.dumps(box["r"]))
        self.assertNotIn(SENTINEL, self._log())

    def test_disarm_all_and_by_session(self) -> None:
        first = self._arm()["handle"]
        second = self._local("code.arm", **dict(ARM, session_id="s2"))["handle"]
        self.assertEqual(self._local("code.disarm", session_id="s2")["disarmed"], 1)
        self.assertEqual(self._redeem(second, answer=False, session_id="s2")["reason"], "unknown_handle")
        self.assertEqual(self._local("code.disarm", all=True)["disarmed"], 1)
        self.assertEqual(self._redeem(first, answer=False)["reason"], "unknown_handle")
        self.assertEqual(self._local("code.disarm")["reason"], "bad_request")

    def test_a_new_arm_for_a_session_replaces_the_old_one(self) -> None:
        first = self._arm()["handle"]
        second = self._arm(turn_id="turn-2")["handle"]
        self.assertEqual(self._redeem(first, answer=False)["reason"], "unknown_handle")
        self.assertTrue(self._redeem(second, turn_id="turn-2")["ok"])

    def test_arms_are_memory_only(self) -> None:
        self._arm()
        text = json.dumps([p.name for p in self.h.home.rglob("*") if p.is_file()])
        self.assertNotIn("arm", text.casefold().replace("pair", ""))


if __name__ == "__main__":
    unittest.main()
