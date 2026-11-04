"""P10-READ: contact index — paging, canonical numbers, ambiguity, TTL, failure."""

from __future__ import annotations

import ast
import json
import logging
import sys
import unittest
from pathlib import Path
from unittest import mock

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import address_hash
import contact_index
import contacts
import google_http
import phone_ids

ADA = "people/c1"
BOB = "people/c2"
CY = "people/c3"
DEE = "people/c4"


def _person(resource, name, phones=(), emails=()):
    out = {"resourceName": resource}
    if name:
        out["names"] = [{"displayName": name}]
    if phones:
        out["phoneNumbers"] = [dict(p) if isinstance(p, dict) else {"value": p} for p in phones]
    if emails:
        out["emailAddresses"] = [{"value": e} for e in emails]
    return out


class _Clock:
    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t


class _Fake:
    """A scripted People API: pages of connections, or a failure."""

    def __init__(self, pages) -> None:
        self.pages = pages
        self.calls = []
        self.fail = False

    def __call__(self, method, url, **kwargs):
        self.calls.append((method, url, dict(kwargs.get("params") or {}), kwargs.get("headers")))
        if self.fail:
            return google_http.GoogleHttpResponse(500, "{}")
        token = (kwargs.get("params") or {}).get("pageToken")
        idx = int(token) if token else 0
        body = {"connections": self.pages[idx]}
        if idx + 1 < len(self.pages):
            body["nextPageToken"] = str(idx + 1)
        return google_http.GoogleHttpResponse(200, json.dumps(body))


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        contact_index.reset_for_tests()
        self.clock = _Clock()
        contact_index._now = self.clock
        patcher = mock.patch.object(
            contact_index, "_headers", return_value={"Authorization": "Bearer t"}
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        sleeper = mock.patch.object(google_http.time, "sleep")
        sleeper.start()
        self.addCleanup(sleeper.stop)
        self.addCleanup(google_http.reset_transport_for_tests)
        self.addCleanup(contact_index.reset_for_tests)

    def serve(self, pages) -> _Fake:
        fake = _Fake(pages)
        google_http.set_transport_for_tests(fake)
        return fake


class LoadTests(_Base):
    def test_pages_and_request_shape(self) -> None:
        fake = self.serve(
            [
                [_person(ADA, "Ada Lovelace", ["+15551230001"], ["Ada@Example.com"])],
                [_person(BOB, "Bob Byte", ["+15551230002"])],
            ]
        )
        found = contact_index.resolve_person_by_name("ada lovelace")
        self.assertEqual(found.display_name, "Ada Lovelace")
        self.assertEqual(contact_index.resolve_person_by_name("BOB  BYTE").display_name, "Bob Byte")
        self.assertEqual(len(fake.calls), 2)
        method, url, params, _ = fake.calls[0]
        self.assertEqual(method, "GET")
        self.assertTrue(url.endswith("/people/me/connections"))
        self.assertNotIn("searchContacts", url)
        self.assertEqual(params["pageSize"], contact_index.PAGE_SIZE)
        self.assertEqual(params["personFields"], contact_index.PERSON_FIELDS)
        self.assertEqual(fake.calls[1][2]["pageToken"], "1")
        self.assertNotIn("pageToken", params)
        self.assertEqual(google_http.ROUTE_CONTACTS_CONNECTIONS, "people.people.connections.list")

    def test_handle_is_stable_opaque_and_hides_resource_name(self) -> None:
        self.serve([[_person(ADA, "Ada", ["+15551230001"])]])
        first = contact_index.resolve_person_by_name("ada")
        contact_index.reset_for_tests()
        contact_index._now = self.clock
        again = contact_index.resolve_person_by_name("ada")
        self.assertEqual(first.handle, again.handle)
        self.assertNotIn(ADA, first.handle)
        self.assertNotIn(ADA, repr(first))
        self.assertNotIn("Ada", repr(first))
        self.assertNotIn("+1555", repr(first))
        self.assertEqual(first.handle, contact_index._handle_for(ADA))

    def test_person_without_resource_name_is_skipped(self) -> None:
        self.serve([[{"names": [{"displayName": "Ghost"}]}, _person(ADA, "Ada")]])
        self.assertIsNone(contact_index.resolve_person_by_name("ghost"))
        self.assertIsNotNone(contact_index.resolve_person_by_name("ada"))

    def test_hashes_for_numbers_and_emails(self) -> None:
        self.serve([[_person(ADA, "Ada", ["+15551230001"], [" Ada@Example.com "])]])
        ada = contact_index.resolve_person_by_name("ada")
        phone_hash = phone_ids.hash("+15551230001")
        email_hash = address_hash.address_hash("ada@example.com")
        self.assertIn(phone_hash, ada.number_hashes)
        self.assertIn(email_hash, ada.email_hashes)
        self.assertEqual(contact_index.resolve_person_by_phone_hash(phone_hash).handle, ada.handle)
        self.assertEqual(contact_index.resolve_person_by_email_hash(email_hash).handle, ada.handle)
        self.assertIsNone(contact_index.resolve_person_by_phone_hash("0" * 64))
        self.assertIsNone(contact_index.resolve_person_by_email_hash(""))
        self.assertEqual(contact_index.canonical_numbers_for(ada), ("+15551230001",))
        self.assertEqual(contact_index.canonical_numbers_for(ada.handle), ("+15551230001",))
        self.assertEqual(contact_index.canonical_numbers_for("nope"), ())
        self.assertEqual(contact_index.canonical_numbers_for(None), ())


class PhoneTests(_Base):
    def test_canonical_form_preferred_and_fallback_counted(self) -> None:
        self.serve(
            [
                [
                    _person(
                        ADA,
                        "Ada",
                        [{"value": "(555) 000-9999", "canonicalForm": "+15551230001"}],
                    ),
                    _person(BOB, "Bob", ["(555) 123-0002"]),
                    _person(CY, "Cy", [{"value": "555 123 0003", "canonicalForm": "garbage"}]),
                    _person(DEE, "Dee", ["32665", "AMZN", "x"]),
                ]
            ]
        )
        self.assertEqual(contact_index.canonical_numbers_for(contact_index.resolve_person_by_name("ada")), ("+15551230001",))
        self.assertEqual(contact_index.canonical_numbers_for(contact_index.resolve_person_by_name("bob")), ("+15551230002",))
        self.assertEqual(contact_index.canonical_numbers_for(contact_index.resolve_person_by_name("cy")), ("+15551230003",))
        # shortcodes and alnum senders are not matchable, so Dee has no number
        self.assertEqual(contact_index.canonical_numbers_for(contact_index.resolve_person_by_name("dee")), ())
        # Bob and Cy had no usable canonicalForm
        self.assertEqual(contact_index.phone_fallback_count(), 2)

    def test_all_canonical_forms_need_no_fallback(self) -> None:
        self.serve([[_person(ADA, "Ada", [{"value": "x", "canonicalForm": "+15551230001"}])]])
        contact_index.get_index()
        contact_index.wait_refresh_for_tests()
        self.assertEqual(contact_index.phone_fallback_count(), 0)

    def test_duplicate_number_on_one_person_is_listed_once(self) -> None:
        self.serve([[_person(ADA, "Ada", ["+15551230001", "(555) 123-0001"])]])
        ada = contact_index.resolve_person_by_name("ada")
        self.assertEqual(ada.numbers, ("+15551230001",))

    def test_shared_number_resolves_to_neither(self) -> None:
        self.serve(
            [
                [
                    _person(ADA, "Ada", ["+15551230001", "+15551239999"]),
                    _person(BOB, "Bob", ["+15551230002", "+15551239999"]),
                ]
            ]
        )
        ada = contact_index.resolve_person_by_name("ada")
        self.assertIsNotNone(ada)
        shared = phone_ids.hash("+15551239999")
        self.assertIsNone(contact_index.resolve_person_by_phone_hash(shared))
        own = phone_ids.hash("+15551230001")
        self.assertEqual(contact_index.resolve_person_by_phone_hash(own).display_name, "Ada")
        self.assertEqual(contact_index.canonical_numbers_for(ada), ("+15551230001",))

    def test_shared_email_resolves_to_neither(self) -> None:
        self.serve([[_person(ADA, "Ada", emails=["x@e.com"]), _person(BOB, "Bob", emails=["X@e.com"])]])
        contact_index.resolve_person_by_name("ada")
        self.assertIsNone(contact_index.resolve_person_by_email_hash(address_hash.address_hash("x@e.com")))

    def test_same_name_twice_is_ambiguous(self) -> None:
        self.serve([[_person(ADA, "Sam"), _person(BOB, "sam")]])
        self.assertIsNone(contact_index.resolve_person_by_name("SAM"))


class SpeechMatchTests(_Base):
    """F4: case/spacing/punctuation, first/last alone, small misspellings; never fuzzy a number."""

    def test_spacing_punctuation_and_tokens(self) -> None:
        self.serve([[_person(ADA, "Beebo Dev", ["+15551230001"])]])
        for query in ("Bebo Dev", "BeboDev", "beebo-dev", "beebo", "Dev", "BEBO DEV"):
            hits = contact_index.match_people_by_name(query)
            self.assertEqual(len(hits), 1, query)
            self.assertEqual(hits[0].display_name, "Beebo Dev", query)

    def test_fuzzy_never_picks_between_two(self) -> None:
        self.serve(
            [
                [
                    _person(ADA, "Marcus", ["+15551230001"]),
                    _person(BOB, "Marcas", ["+15551230002"]),
                ]
            ]
        )
        # "Marcos" is one edit from each; must not auto-choose.
        self.assertEqual(
            [p.display_name for p in contact_index.match_people_by_name("Marcos")],
            ["Marcus", "Marcas"],
        )
        self.assertIsNone(contact_index.resolve_person_by_name("Marcos"))

    def test_short_tokens_are_exact_only(self) -> None:
        self.serve([[_person(ADA, "Bob Ray", ["+15551230001"])]])
        self.assertEqual(contact_index.match_people_by_name("Bob"), contact_index.match_people_by_name("bob"))
        self.assertEqual(len(contact_index.match_people_by_name("Bob")), 1)
        # "Rob" is one edit from "Bob" but both length 3 → no fuzzy.
        self.assertEqual(contact_index.match_people_by_name("Rob"), ())

    def test_digit_only_strings_are_never_fuzzy(self) -> None:
        self.serve([[_person(ADA, "5551230001", ["+15551230001"])]])
        self.assertEqual(len(contact_index.match_people_by_name("5551230001")), 1)  # exact
        self.assertEqual(contact_index.match_people_by_name("5551230002"), ())  # one digit off: no fuzzy


class RefreshTests(_Base):
    def test_ttl_reloads_after_thirty_minutes_only(self) -> None:
        fake = self.serve([[_person(ADA, "Ada")]])
        contact_index.get_index()
        contact_index.wait_refresh_for_tests()
        self.assertEqual(len(fake.calls), 1)
        self.clock.t += contact_index.TTL_SECONDS - 1
        contact_index.refresh_if_stale()
        contact_index.wait_refresh_for_tests()
        self.assertEqual(len(fake.calls), 1)
        self.clock.t += 2
        fake.pages = [[_person(ADA, "Ada"), _person(BOB, "Bob")]]
        contact_index.refresh_if_stale()
        contact_index.wait_refresh_for_tests()
        self.assertEqual(len(fake.calls), 2)
        self.assertIsNotNone(contact_index.resolve_person_by_name("bob"))
        self.assertEqual(contact_index.TTL_SECONDS, 1800)

    def test_name_miss_refreshes_once_then_is_rate_limited(self) -> None:
        fake = self.serve([[_person(ADA, "Ada")]])
        self.assertIsNone(contact_index.resolve_person_by_name("bob"))
        contact_index.wait_refresh_for_tests()
        self.assertEqual(len(fake.calls), 1)  # first load; no second call inside the interval
        self.clock.t += contact_index.REFRESH_MIN_INTERVAL_SECONDS
        fake.pages = [[_person(ADA, "Ada"), _person(BOB, "Bob")]]
        # cool-down elapsed: on-miss refreshes even though the index is still inside TTL
        found = contact_index.resolve_person_by_name("bob")
        contact_index.wait_refresh_for_tests()
        self.assertIsNotNone(found)
        self.assertEqual(found.display_name, "Bob")
        self.assertEqual(len(fake.calls), 2)
        self.assertIsNone(contact_index.resolve_person_by_name("nobody"))
        contact_index.wait_refresh_for_tests()
        self.assertEqual(len(fake.calls), 2)

    def test_hit_does_not_refresh(self) -> None:
        fake = self.serve([[_person(ADA, "Ada")]])
        contact_index.resolve_person_by_name("ada")
        contact_index.wait_refresh_for_tests()
        count = len(fake.calls)
        for _ in range(3):
            contact_index.resolve_person_by_name("ada")
        self.assertEqual(len(fake.calls), count)

    def test_empty_query_makes_no_call(self) -> None:
        fake = self.serve([[]])
        self.assertIsNone(contact_index.resolve_person_by_name("   "))
        self.assertEqual(fake.calls, [])

    def test_failure_marks_unavailable_and_everyone_is_unknown(self) -> None:
        fake = self.serve([[_person(ADA, "Ada", ["+15551230001"])]])
        self.assertIsNotNone(contact_index.resolve_person_by_name("ada"))
        contact_index.wait_refresh_for_tests()
        self.assertFalse(contact_index.contacts_unavailable())
        fake.fail = True
        self.clock.t += contact_index.TTL_SECONDS + 1
        contact_index.refresh_if_stale()
        contact_index.wait_refresh_for_tests()
        self.assertIsNone(contact_index.resolve_person_by_name("ada"))
        self.assertTrue(contact_index.contacts_unavailable())
        self.assertIsNone(contact_index.get_index())
        self.assertIsNone(contact_index.resolve_person_by_phone_hash(phone_ids.hash("+15551230001")))

    def test_failed_load_retries_only_after_cooldown_and_recovers(self) -> None:
        fake = self.serve([[_person(ADA, "Ada")]])
        fake.fail = True
        self.assertIsNone(contact_index.resolve_person_by_name("ada"))
        contact_index.wait_refresh_for_tests()
        self.assertTrue(contact_index.contacts_unavailable())
        count = len(fake.calls)
        self.assertIsNone(contact_index.resolve_person_by_name("ada"))
        self.assertEqual(len(fake.calls), count)
        fake.fail = False
        self.clock.t += contact_index.REFRESH_MIN_INTERVAL_SECONDS
        self.assertIsNotNone(contact_index.resolve_person_by_name("ada"))
        contact_index.wait_refresh_for_tests()
        self.assertFalse(contact_index.contacts_unavailable())

    def test_auth_failure_is_unavailable(self) -> None:
        fake = self.serve([[_person(ADA, "Ada")]])
        with mock.patch.object(contact_index, "_headers", side_effect=RuntimeError("not_connected")):
            self.assertIsNone(contact_index.resolve_person_by_name("ada"))
            contact_index.wait_refresh_for_tests()
        self.assertTrue(contact_index.contacts_unavailable())
        self.assertEqual(fake.calls, [])

    def test_truncated_paging_is_a_failure(self) -> None:
        pages = [[_person(f"people/p{i}", f"P{i}")] for i in range(contact_index.MAX_PAGES + 1)]
        self.serve(pages)
        contact_index.get_index()
        contact_index.wait_refresh_for_tests()
        self.assertIsNone(contact_index.get_index())
        self.assertTrue(contact_index.contacts_unavailable())

    def test_f8_stale_refresh_returns_without_waiting_on_slow_people_api(self) -> None:
        """F8: turn path must not wait for Google; aged index stays until the bg finish."""
        import threading
        import time

        fake = self.serve([[_person(ADA, "Ada", ["+15551230001"])]])
        self.assertIsNotNone(contact_index.resolve_person_by_name("ada"))
        contact_index.wait_refresh_for_tests()
        digest = phone_ids.hash("+15551230001")
        self.clock.t += contact_index.TTL_SECONDS + 1
        gate = threading.Event()

        def slow(method, url, **kwargs):
            gate.wait(30)
            return fake(method, url, **kwargs)

        google_http.set_transport_for_tests(slow)
        started = time.monotonic()
        self.assertTrue(contact_index.refresh_if_stale())
        self.assertLess(time.monotonic() - started, 2.0)
        # aged index still names Ada while the slow refresh runs
        self.assertEqual(
            contact_index.resolve_person_by_phone_hash(digest).display_name, "Ada"
        )
        gate.set()
        contact_index.wait_refresh_for_tests()

    def test_f8_bounded_on_miss_gives_up_inside_the_bound(self) -> None:
        """F8: phone_read_texts on-miss waits at most TURN_REFRESH_BOUND_SECONDS."""
        import threading
        import time

        fake = self.serve([[_person(ADA, "Ada")]])
        gate = threading.Event()

        def slow(method, url, **kwargs):
            gate.wait(30)
            return fake(method, url, **kwargs)

        google_http.set_transport_for_tests(slow)
        started = time.monotonic()
        ok = contact_index.refresh_bounded(0.4)
        elapsed = time.monotonic() - started
        self.assertFalse(ok)
        self.assertLess(elapsed, 1.5)
        self.assertGreaterEqual(elapsed, 0.35)
        gate.set()
        contact_index.wait_refresh_for_tests()


class HygieneTests(_Base):
    def test_nothing_sensitive_is_logged(self) -> None:
        self.serve([[_person(ADA, "Ada Lovelace", ["+15551230001"], ["ada@example.com"])]])
        logging.disable(logging.NOTSET)
        logger = logging.getLogger("zola_workspace.contact_index")
        logger.setLevel(logging.DEBUG)
        with self.assertLogs(logger, level=logging.DEBUG) as captured:
            contact_index.resolve_person_by_name("ada lovelace")
            contact_index.resolve_person_by_name("nobody at all")
            logger.info("anchor")
        text = "\n".join(captured.output)
        for secret in ("Ada", "Lovelace", "15551230001", "ada@example.com", ADA, "nobody"):
            self.assertNotIn(secret, text)

    def test_module_has_no_disk_or_store_use(self) -> None:
        tree = ast.parse((PLUGIN_ROOT / "contact_index.py").read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            if isinstance(node, ast.ImportFrom):
                imported.update(a.name.split(".")[0] for a in node.names)
                imported.add((node.module or "").split(".")[0])
        for banned in ("sqlite3", "proactive_store", "pathlib", "os", "shutil", "tempfile", "taint", "recorded_results"):
            self.assertNotIn(banned, imported)
        source = (PLUGIN_ROOT / "contact_index.py").read_text(encoding="utf-8")
        self.assertNotIn("searchContacts", source)
        self.assertNotIn("otherContacts", source)
        self.assertNotIn("open(", source)


class ShapePersonTests(unittest.TestCase):
    def test_shape_person_prefers_canonical_form(self) -> None:
        shaped = contacts.shape_person(
            {
                "names": [{"displayName": "Ada"}],
                "emailAddresses": [{"value": "ada@example.com"}],
                "phoneNumbers": [
                    {"value": "(555) 123-0001", "canonicalForm": "+15551230001"},
                    {"value": "555 123 0002"},
                    {"canonicalForm": "+15551230003"},
                    {"value": ""},
                ],
            }
        )
        self.assertEqual(shaped["phones"], ["+15551230001", "555 123 0002", "+15551230003"])
        self.assertEqual(shaped["display_name"], "Ada")
        self.assertEqual(shaped["emails"], ["ada@example.com"])


if __name__ == "__main__":
    unittest.main()
