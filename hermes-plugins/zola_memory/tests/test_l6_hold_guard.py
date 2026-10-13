"""L6 harness: a pre-existing forget-hold row is left untouched."""

from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path

_MEMORY = Path(__file__).resolve().parents[1]
if str(_MEMORY) not in sys.path:
    sys.path.insert(0, str(_MEMORY))

import l6_hold_guard


class L6HoldGuardTests(unittest.TestCase):
    def test_skip_does_not_write_a_foreign_row(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        original = '{"session_id":"already","started_at":"2026-10-13T21:31:08Z"}'
        conn.execute(
            "INSERT INTO meta (key, value) VALUES ('forget_hold', ?)",
            (original,),
        )
        conn.commit()
        row = conn.execute(
            "SELECT value FROM meta WHERE key = 'forget_hold'"
        ).fetchone()
        decision = l6_hold_guard.harness_hold_decision(row[0] if row else None)
        self.assertEqual(decision, "skip")
        if decision == "proceed":
            conn.execute("DELETE FROM meta WHERE key = 'forget_hold'")
            conn.commit()
        after = conn.execute(
            "SELECT value FROM meta WHERE key = 'forget_hold'"
        ).fetchone()
        self.assertEqual(after[0], original)
        conn.close()

    def test_proceed_only_when_the_row_is_absent(self) -> None:
        self.assertEqual(l6_hold_guard.harness_hold_decision(None), "proceed")
        self.assertEqual(l6_hold_guard.harness_hold_decision(""), "proceed")
        self.assertEqual(l6_hold_guard.harness_hold_decision("x"), "skip")
