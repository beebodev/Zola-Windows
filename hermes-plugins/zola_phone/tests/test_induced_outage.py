"""The C10 harness records an induced kill the dead process cannot log."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PLUGINS = Path(__file__).resolve().parents[2]
if str(PLUGINS) not in sys.path:
    sys.path.insert(0, str(PLUGINS))

from zola_phone.outage import induced_stop_line


class InducedStopTest(unittest.TestCase):
    def test_induced_kill_names_pc_shutdown(self) -> None:
        line = induced_stop_line()
        self.assertIn("reason=pc-shutdown", line)
        self.assertIn("who=pc", line)
        self.assertIn("induced=true", line)


if __name__ == "__main__":
    unittest.main()
