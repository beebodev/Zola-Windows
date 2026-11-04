"""P10-READ: RCS sender extraction; normalize() vectors stay as they were."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import phone_ids

# Same vectors as the P10-STORE normalizer test; extract_rcs_sender must not move them.
NORMALIZER_CASES = (
    ("(555) 123-4567", "e164", "+15551234567"),
    ("555-123-4567", "e164", "+15551234567"),
    ("+1 555 123 4567", "e164", "+15551234567"),
    ("1-555-123-4567", "e164", "+15551234567"),
    ("5551234567", "e164", "+15551234567"),
    ("15551234567", "e164", "+15551234567"),
    ("+15551234567", "e164", "+15551234567"),
    ("+44 20 7946 0958", "e164", "+442079460958"),
    ("32665", "shortcode", "32665"),
    ("AMZN", "alnum", "amzn"),
    ("", "unparsed", ""),
    ("junk", "alnum", "junk"),
    ("abc!@#def", "unparsed", "abc!@#def"),
    ("hello-world-123456", "unparsed", "hello-world-123456"),
)
UNPARSED = ("unparsed", "")


class RcsSenderTests(unittest.TestCase):
    def test_tel_forms(self) -> None:
        for raw, canonical in (
            ("tel:+15551234567", "+15551234567"),
            ("TEL:+15551234567", "+15551234567"),
            ("  tel:+15551234567  ", "+15551234567"),
            ("tel:+1-555-123-4567", "+15551234567"),
            ("tel:+1(555)123-4567", "+15551234567"),
            ("tel:+44.20.7946.0958", "+442079460958"),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(phone_ids.extract_rcs_sender(raw), ("e164", canonical))

    def test_tel_that_is_not_unambiguous(self) -> None:
        for raw in (
            "tel:5551234567",
            "tel:15551234567",
            "tel:+1555",
            "tel:+1555123456789012",
            "tel:+15551234567;ext=22",
            "tel:+15551234567;phone-context=example.com",
            "tel:+1555abc4567",
            "tel:",
            "tel:+",
        ):
            with self.subTest(raw=raw):
                self.assertEqual(phone_ids.extract_rcs_sender(raw), UNPARSED)

    def test_sip_with_e164_user(self) -> None:
        for raw, canonical in (
            ("sip:+15551234567@carrier.example.com", "+15551234567"),
            ("sips:+15551234567@carrier.example.com", "+15551234567"),
            ("SIP:+15551234567@carrier.example.com;user=phone", "+15551234567"),
            ("sip:+442079460958@ims.example.net:5060", "+442079460958"),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(phone_ids.extract_rcs_sender(raw), ("e164", canonical))

    def test_business_agent_is_unparsed(self) -> None:
        for raw in (
            "sip:brand-agent-77@bots.example.com",
            "sip:agent_id@rbm.goog",
            "sip:5551234567@carrier.example.com",
            "sip:+15551234567",
            "sip:+15551234567@",
            "sip:+15551234567@host@other",
            "sip:+1555;ext=1@host.example",
            "sip:+15551234567@host.example?header=x",
        ):
            with self.subTest(raw=raw):
                self.assertEqual(phone_ids.extract_rcs_sender(raw), UNPARSED)

    def test_junk_is_unparsed_and_leaks_nothing(self) -> None:
        for raw in (
            "",
            None,
            "junk",
            "+15551234567",
            "5551234567",
            "mailto:+15551234567@example.com",
            "http://example.com/+15551234567",
            "tel",
            ":+15551234567",
            "\x00\x01",
        ):
            with self.subTest(raw=raw):
                kind, canonical = phone_ids.extract_rcs_sender(raw)
                self.assertEqual((kind, canonical), UNPARSED)
                self.assertFalse(phone_ids.matchable(kind))

    def test_extracted_number_hashes_like_a_plain_number(self) -> None:
        _, from_tel = phone_ids.extract_rcs_sender("tel:+15551234567")
        _, from_text = phone_ids.normalize("(555) 123-4567")
        self.assertEqual(phone_ids.hash(from_tel), phone_ids.hash(from_text))

    def test_normalize_vectors_unchanged(self) -> None:
        for raw, kind, canonical in NORMALIZER_CASES:
            with self.subTest(raw=raw):
                self.assertEqual(phone_ids.normalize(raw), (kind, canonical))
        # a tel: string through normalize() keeps its old behavior (not e164)
        self.assertEqual(phone_ids.normalize("tel:+15551234567")[0], "unparsed")

    def test_shared_vector_file_still_loads(self) -> None:
        path = PLUGIN_ROOT / "contracts" / "phone_vectors.json"
        self.assertTrue(json.loads(path.read_text(encoding="utf-8"))["cases"])


if __name__ == "__main__":
    unittest.main()
