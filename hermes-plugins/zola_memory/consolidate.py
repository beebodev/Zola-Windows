"""Episode consolidator — pending turns → episodes (P6-D04)."""

from __future__ import annotations

import json
import re
import sqlite3
import threading
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

try:
    from . import forget
    from . import log as memlog
    from . import pending as pending_mod
    from . import store
    from . import time_context
except ImportError:  # P6-EPISODES: flat unittest discover top — P6-D04
    import forget
    import log as memlog
    import pending as pending_mod
    import store
    import time_context

# P6-EPISODES: named constants — P6-D04
CONSOLIDATE_QUIET_MINUTES = 10
CONSOLIDATE_LLM_TIMEOUT_S = 30
CONSOLIDATE_LEASE_TTL_S = 60  # 2× LLM timeout
CONSOLIDATE_MAX_ATTEMPTS = 5

SIGNIFICANCE_VALUES = frozenset(
    {"decision", "plan", "event", "preference_change", "problem", "other"}
)
ENTITY_KINDS = frozenset(
    {"person", "project", "vehicle", "place", "org", "other"}
)
WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

SUMMARIZER_INSTRUCTIONS = """You consolidate Brian's recent conversation turns into zero or more memory episodes for Zola.

Rules:
- Small talk, greetings, arithmetic, and passing chatter produce NO episode.
- One stretch of conversation may produce several episodes when they are distinct.
- Never record the content of a forget request or what was erased.
- Never create, invent, or rewrite lasting notebook facts. You may only reference existing fact IDs from the provided list.
- Do not create an episode merely because Zola restated or recalled something from memory context. Only something new that happened or was decided in the source turns justifies an episode.
- Open items and future plans belong in open_items on the episode they belong to — not as their own episodes.
- A plan, next step, or follow-up about the same thing as an event or decision in this stretch belongs in that episode's open_items, not in its own episode. A plan is its own episode only when nothing else in the stretch is about the same thing.
- Example: Brian says he took the car in for brakes, then that they'll do the tires next week → ONE episode (the shop visit), with the tire work as an open_item — not a second episode.
- Multiple fact_refs about the same thing belong on one episode; do not split an episode per fact_ref.
- Entity names and aliases must appear exactly as written in the source turns or in the provided active facts (no expanding abbreviations or inventing canonical names).
- event_time: only when Brian used a time phrase in a user turn. Set event_time_basis to "stated" and set event_time_evidence to his exact phrase. Never infer times from when the message was sent. A future plan is not an event_time (use basis "unknown" and nulls). Prefer referencing existing fact_refs when an episode concerns a stored fact.
- source_turn_range must use pending turn ids from the input list.
- If nothing qualifies, return {"episodes": []}."""

# P8-CONNECT: episode attribution when Workspace-tainted / unavailable — P8-D09
WORKSPACE_ATTRIBUTION_LINE = (
    'If any source turn is Workspace-tainted, attribute external content as something Zola read '
    '(for example: "Zola read a calendar event that said…"), never as Brian\'s own statement.'
)


def _zola_workspace_plugin_enabled() -> bool:
    """True when zola_workspace is allow-listed and not disabled. Fail → False."""
    try:
        from hermes_cli.plugins_discovery import (
            _get_disabled_plugins,
            _get_enabled_plugins,
        )

        disabled = _get_disabled_plugins() or set()
        if "zola_workspace" in disabled:
            return False
        enabled = _get_enabled_plugins()
        if enabled is None:
            return False
        return "zola_workspace" in enabled
    except Exception:
        return False


def _needs_workspace_attribution(rows: Sequence[sqlite3.Row]) -> bool:
    """Append attribution when workspace disabled, tainted, or import/read fails."""
    # P8-CONNECT: fail toward caution — P8-D09
    try:
        if not _zola_workspace_plugin_enabled():
            return True
    except Exception:
        return True
    try:
        from hermes_plugins.zola_workspace.taint import is_tainted
    except Exception:
        return True
    session_ids = set()
    try:
        for row in rows:
            try:
                sid = row["session_id"]
            except Exception:
                sid = ""
            if sid:
                session_ids.add(str(sid))
    except Exception:
        return True
    if not session_ids:
        return False
    for sid in session_ids:
        try:
            if is_tainted(sid):
                return True
        except Exception:
            return True
    return False


def summarizer_instructions_for(rows: Sequence[sqlite3.Row]) -> str:
    """SUMMARIZER_INSTRUCTIONS, plus Workspace attribution when required."""
    base = SUMMARIZER_INSTRUCTIONS
    if _needs_workspace_attribution(rows):
        return base + "\n- " + WORKSPACE_ATTRIBUTION_LINE
    return base


EPISODE_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["episodes"],
    "properties": {
        "episodes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "summary",
                    "significance",
                    "entities",
                    "fact_refs",
                    "source_turn_range",
                    "event_time_basis",
                    "open_items",
                ],
                "properties": {
                    "summary": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 800,
                    },
                    "significance": {
                        "type": "string",
                        "enum": sorted(SIGNIFICANCE_VALUES),
                    },
                    "entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["name", "kind"],
                            "properties": {
                                "id": {"type": ["string", "null"]},
                                "name": {
                                    "type": "string",
                                    "minLength": 1,
                                    "maxLength": 120,
                                },
                                "kind": {
                                    "type": "string",
                                    "enum": sorted(ENTITY_KINDS),
                                },
                                "alias": {"type": ["string", "null"]},
                            },
                        },
                    },
                    "fact_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "source_turn_range": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["start_pending_id", "end_pending_id"],
                        "properties": {
                            "start_pending_id": {"type": "string"},
                            "end_pending_id": {"type": "string"},
                        },
                    },
                    "event_time": {"type": ["string", "null"]},
                    "event_time_basis": {
                        "type": "string",
                        "enum": ["stated", "unknown"],
                    },
                    "event_time_evidence": {"type": ["string", "null"]},
                    "open_items": {
                        "type": "array",
                        "items": {"type": "string", "maxLength": 240},
                    },
                },
            },
        }
    },
}

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

_lock = threading.RLock()
_running = False
_coalesce: Optional[str] = None
_attempt_counts: Dict[str, int] = {}  # keyed by sorted pending-id fingerprint
_last_pending_write_at: Optional[float] = None
_timer_started = False
_timer_stop = threading.Event()
_llm_override: Any = None
_quiet_minutes_override: Optional[float] = None
_background_enabled = True
_instance_id = str(uuid.uuid4())


def reset_for_tests() -> None:
    global _running, _coalesce, _attempt_counts, _last_pending_write_at
    global _timer_started, _llm_override, _quiet_minutes_override, _instance_id
    global _timer_stop, _background_enabled
    with _lock:
        _running = False
        _coalesce = None
        _attempt_counts = {}
        _last_pending_write_at = None
        _timer_stop.set()
        _timer_started = False
        _llm_override = None
        _quiet_minutes_override = None
        _background_enabled = False
        _instance_id = str(uuid.uuid4())
        _timer_stop = threading.Event()


def set_background_enabled_for_tests(enabled: bool) -> None:
    global _background_enabled
    _background_enabled = bool(enabled)


def set_llm_for_tests(llm: Any) -> None:
    global _llm_override
    _llm_override = llm


def set_quiet_minutes_for_tests(minutes: Optional[float]) -> None:
    global _quiet_minutes_override
    _quiet_minutes_override = minutes


def note_pending_write() -> None:
    global _last_pending_write_at
    with _lock:
        _last_pending_write_at = time.monotonic()


def _quiet_minutes() -> float:
    if _quiet_minutes_override is not None:
        return float(_quiet_minutes_override)
    return float(CONSOLIDATE_QUIET_MINUTES)


def _get_llm() -> Any:
    if _llm_override is not None:
        return _llm_override
    try:
        from . import _get_plugin_llm as getter  # type: ignore
    except ImportError:
        try:
            import llm_access

            def getter() -> Any:
                ctx = llm_access.get_collector()
                if ctx is None:
                    return None
                try:
                    return ctx._plugin_context().llm
                except Exception:
                    return None

        except Exception:
            return None
    try:
        return getter()
    except Exception:
        return None


def start_quiet_timer(provider: Any) -> None:
    """Start the background quiet-gap watcher once per process."""
    global _timer_started
    if not _background_enabled:
        return
    with _lock:
        if _timer_started:
            return
        _timer_started = True
        _timer_stop.clear()

    def _loop() -> None:
        while not _timer_stop.is_set():
            try:
                _timer_stop.wait(5.0)
                if _timer_stop.is_set():
                    break
                conn = getattr(provider, "_conn", None)
                if conn is None:
                    continue
                with store.locked(conn):
                    n = pending_mod.count_pending(conn)
                if n <= 0:
                    continue
                with _lock:
                    last = _last_pending_write_at
                if last is None:
                    request_consolidate(provider, "quiet")
                    continue
                if (time.monotonic() - last) >= _quiet_minutes() * 60.0:
                    request_consolidate(provider, "quiet")
            except Exception:
                pass

    try:
        from agent.memory_provider import spawn_context_thread

        t = spawn_context_thread(target=_loop, name="zola-consolidate-timer")
    except Exception:
        t = threading.Thread(target=_loop, name="zola-consolidate-timer", daemon=True)
    t.daemon = True
    t.start()


def stop_quiet_timer_for_tests() -> None:
    global _timer_started
    _timer_stop.set()
    with _lock:
        _timer_started = False


def request_consolidate(provider: Any, trigger: str) -> None:
    """Non-blocking: coalesce a consolidator wake (never runs LLM inline)."""
    global _coalesce, _running
    if not _background_enabled:
        return
    with _lock:
        _coalesce = trigger
        if _running:
            return
        _running = True

    def _runner() -> None:
        global _running, _coalesce
        try:
            while True:
                with _lock:
                    trig = _coalesce or trigger
                    _coalesce = None
                try:
                    run_consolidation(provider, trig)
                except Exception:
                    memlog.write_event(
                        memlog.LOG_EVENT_CONSOLIDATE,
                        trigger=trig,
                        turns=0,
                        episodes=0,
                        ok=False,
                        attempt=0,
                        elapsed_ms=0,
                    )
                with _lock:
                    if _coalesce is None:
                        _running = False
                        return
        finally:
            with _lock:
                _running = False

    try:
        from agent.memory_provider import spawn_context_thread

        t = spawn_context_thread(target=_runner, name="zola-consolidate")
    except Exception:
        t = threading.Thread(target=_runner, name="zola-consolidate", daemon=True)
    t.daemon = True
    t.start()


def run_consolidation(provider: Any, trigger: str) -> bool:
    """Run one consolidation attempt (blocking). Returns True on commit."""
    conn = getattr(provider, "_conn", None)
    if conn is None:
        return False
    if not getattr(provider, "llm_available", False) and _llm_override is None:
        memlog.write_event(
            memlog.LOG_EVENT_CONSOLIDATE,
            trigger=trigger,
            turns=0,
            episodes=0,
            ok=False,
            attempt=0,
            elapsed_ms=0,
        )
        return False

    if not _acquire_lease(conn):
        return False
    t0 = time.perf_counter()
    try:
        # P6-EPISODES: retry deferred G-ERASE WAL TRUNCATE — P6-D04
        try:
            with store.locked(conn):
                store.try_pending_sanitize(conn, trigger="consolidate")
        except Exception:
            pass
        with store.locked(conn):
            token = forget.begin_consolidation(conn)
            rows = pending_mod.list_pending_ordered(conn)
        if not rows:
            return False
        pending_ids = [r["id"] for r in rows]
        key = ",".join(sorted(pending_ids))
        attempt = _attempt_counts.get(key, 0) + 1
        if attempt > CONSOLIDATE_MAX_ATTEMPTS:
            memlog.write_event(
                memlog.LOG_EVENT_CONSOLIDATE_GIVEUP,
                attempts=attempt - 1,
                pending_count=len(pending_ids),
            )
            # One more try only at initialize — allow reset when trigger is initialize
            if trigger != "initialize":
                return False
            _attempt_counts[key] = 0
            attempt = 1

        llm = _get_llm()
        if llm is None:
            memlog.write_event(
                memlog.LOG_EVENT_CONSOLIDATE,
                trigger=trigger,
                turns=len(rows),
                episodes=0,
                ok=False,
                attempt=0,
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
            )
            return False

        input_text = _build_model_input(conn, rows)
        try:
            # P8-CONNECT: attribution line when Workspace-tainted / unavailable — P8-D09
            instructions = summarizer_instructions_for(rows)
            result = llm.complete_structured(
                instructions=instructions,
                input=[{"type": "text", "text": input_text}],
                json_schema=EPISODE_JSON_SCHEMA,
                timeout=CONSOLIDATE_LLM_TIMEOUT_S,
            )
        except Exception:
            _attempt_counts[key] = attempt
            memlog.write_event(
                memlog.LOG_EVENT_CONSOLIDATE,
                trigger=trigger,
                turns=len(rows),
                episodes=0,
                ok=False,
                attempt=attempt,
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
            )
            return False

        parsed = _extract_parsed(result)
        ok_val, episodes = validate_episodes(parsed, rows, conn)
        if not ok_val:
            _attempt_counts[key] = attempt
            if attempt >= CONSOLIDATE_MAX_ATTEMPTS:
                memlog.write_event(
                    memlog.LOG_EVENT_CONSOLIDATE_GIVEUP,
                    attempts=attempt,
                    pending_count=len(pending_ids),
                )
            memlog.write_event(
                memlog.LOG_EVENT_CONSOLIDATE,
                trigger=trigger,
                turns=len(rows),
                episodes=0,
                ok=False,
                attempt=attempt,
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
            )
            return False

        _renew_lease(conn)
        committed = _commit(conn, token, rows, episodes, pending_ids)
        memlog.write_event(
            memlog.LOG_EVENT_CONSOLIDATE,
            trigger=trigger,
            turns=len(rows),
            episodes=len(episodes) if committed else 0,
            ok=committed,
            attempt=attempt,
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )
        if committed:
            _attempt_counts.pop(key, None)
        else:
            _attempt_counts[key] = attempt
        return committed
    finally:
        _release_lease(conn)


def _extract_parsed(result: Any) -> Any:
    if result is None:
        return None
    if isinstance(result, dict):
        return result
    parsed = getattr(result, "parsed", None)
    if parsed is not None:
        return parsed
    text = getattr(result, "text", None) or getattr(result, "content", None)
    if isinstance(text, str) and text.strip():
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    return None


def _build_model_input(conn: sqlite3.Connection, rows: Sequence[sqlite3.Row]) -> str:
    parts: List[str] = ["PENDING_TURNS:"]
    for r in rows:
        parts.append(
            f"- id={r['id']} user_time={r['user_time'] or 'null'}\n"
            f"  user: {r['user_text'] or ''}\n"
            f"  assistant: {r['assistant_text'] or ''}"
        )
    parts.append("ENTITIES:")
    for e in conn.execute("SELECT id, name, kind FROM entities ORDER BY name"):
        aliases = [
            a["alias"]
            for a in conn.execute(
                "SELECT alias FROM entity_aliases WHERE entity_id = ?",
                (e["id"],),
            )
        ]
        parts.append(
            f"- id={e['id']} name={e['name']} kind={e['kind']} "
            f"aliases={aliases}"
        )
    parts.append("ACTIVE_FACTS:")
    for f in conn.execute(
        "SELECT id, target, text FROM facts WHERE state = ? ORDER BY id",
        (store.STATE_ACTIVE,),
    ):
        parts.append(f"- id={f['id']} target={f['target']} text={f['text']}")
    return "\n".join(parts)


def validate_episodes(
    parsed: Any,
    rows: Sequence[sqlite3.Row],
    conn: sqlite3.Connection,
) -> Tuple[bool, List[Dict[str, Any]]]:
    if not isinstance(parsed, dict):
        return False, []
    if "episodes" not in parsed:
        return False, []
    # Reject fact-creating fields at top level
    for bad in ("facts", "new_facts", "fact_creates"):
        if bad in parsed:
            return False, []
    eps = parsed.get("episodes")
    if not isinstance(eps, list):
        return False, []
    if len(eps) == 0:
        return True, []

    by_id = {r["id"]: r for r in rows}
    order = [r["id"] for r in rows]
    order_pos = {pid: i for i, pid in enumerate(order)}
    active_facts = {
        r["id"]: r["text"]
        for r in conn.execute(
            "SELECT id, text FROM facts WHERE state = ?", (store.STATE_ACTIVE,)
        )
    }
    entity_names: Set[str] = set()
    for e in conn.execute("SELECT id, name FROM entities"):
        entity_names.add((e["name"] or "").casefold())
        for a in conn.execute(
            "SELECT alias FROM entity_aliases WHERE entity_id = ?", (e["id"],)
        ):
            entity_names.add((a["alias"] or "").casefold())
    entity_ids = {
        e["id"] for e in conn.execute("SELECT id FROM entities")
    }

    source_blob_parts: List[str] = []
    user_blobs: Dict[str, str] = {}
    for r in rows:
        ut = r["user_text"] or ""
        at = r["assistant_text"] or ""
        source_blob_parts.append(ut)
        source_blob_parts.append(at)
        user_blobs[r["id"]] = ut
    source_blob = "\n".join(source_blob_parts)

    out: List[Dict[str, Any]] = []
    for ep in eps:
        if not isinstance(ep, dict):
            return False, []
        for bad in ("facts", "new_facts", "fact_text"):
            if bad in ep:
                return False, []
        summary = ep.get("summary")
        if not isinstance(summary, str) or not (1 <= len(summary) <= 800):
            return False, []
        sig = ep.get("significance")
        if sig not in SIGNIFICANCE_VALUES:
            return False, []
        entities = ep.get("entities")
        if not isinstance(entities, list):
            return False, []
        for ent in entities:
            if not isinstance(ent, dict):
                return False, []
            name = ent.get("name")
            kind = ent.get("kind")
            if not isinstance(name, str) or not name.strip():
                return False, []
            if kind not in ENTITY_KINDS:
                return False, []
            alias = ent.get("alias")
            if alias is not None and not isinstance(alias, str):
                return False, []
            eid = ent.get("id")
            if eid is not None and eid not in entity_ids:
                return False, []
            if not _entity_grounded(
                name, alias, source_blob, active_facts, entity_names
            ):
                return False, []
        fact_refs = ep.get("fact_refs")
        if not isinstance(fact_refs, list):
            return False, []
        for fid in fact_refs:
            if fid not in active_facts:
                return False, []
        rng = ep.get("source_turn_range")
        if not isinstance(rng, dict):
            return False, []
        start_id = rng.get("start_pending_id")
        end_id = rng.get("end_pending_id")
        if start_id not in by_id or end_id not in by_id:
            return False, []
        if order_pos[start_id] > order_pos[end_id]:
            return False, []
        basis = ep.get("event_time_basis")
        if basis == "system":
            return False, []
        if basis not in ("stated", "unknown"):
            return False, []
        evidence = ep.get("event_time_evidence")
        event_time = ep.get("event_time")
        open_items = ep.get("open_items")
        if not isinstance(open_items, list):
            return False, []
        for oi in open_items:
            if not isinstance(oi, str) or len(oi) > 240:
                return False, []

        # Resolve stated time against the start turn's user_time (range)
        resolved_time: Optional[str] = None
        resolved_basis = "unknown"
        resolved_evidence: Optional[str] = None
        if basis == "stated":
            if not isinstance(evidence, str) or not evidence.strip():
                return False, []
            # evidence must appear in a user turn within range
            range_ids = order[
                order_pos[start_id] : order_pos[end_id] + 1
            ]
            found_in: Optional[str] = None
            ev_cf = evidence.casefold()
            for rid in range_ids:
                if ev_cf in (user_blobs.get(rid) or "").casefold():
                    found_in = rid
                    break
            if found_in is None:
                return False, []
            turn_user_time = by_id[found_in]["user_time"]
            if not turn_user_time:
                # P6-EPISODES: keep episode; log unresolved (counts only) — P6-D04
                memlog.write_event(
                    memlog.LOG_EVENT_CONSOLIDATE_TIME_UNRESOLVED,
                    reason="unparseable_user_time",
                    count=1,
                )
                resolved_basis = "unknown"
                resolved_time = None
                resolved_evidence = None
            else:
                resolved, fail_reason = resolve_stated_time_with_reason(
                    evidence, turn_user_time
                )
                if resolved is None:
                    memlog.write_event(
                        memlog.LOG_EVENT_CONSOLIDATE_TIME_UNRESOLVED,
                        reason=fail_reason or "other",
                        count=1,
                    )
                    resolved_basis = "unknown"
                    resolved_time = None
                    resolved_evidence = None
                else:
                    resolved_basis = "stated"
                    resolved_time = resolved
                    resolved_evidence = evidence
        else:
            if event_time is not None or evidence is not None:
                # allow nulls only
                if event_time is not None or (
                    evidence is not None and str(evidence).strip()
                ):
                    return False, []

        out.append(
            {
                "summary": summary,
                "significance": sig,
                "entities": entities,
                "fact_refs": list(fact_refs),
                "source_turn_range": {
                    "start_pending_id": start_id,
                    "end_pending_id": end_id,
                },
                "event_time": resolved_time,
                "event_time_basis": resolved_basis,
                "event_time_evidence": resolved_evidence,
                "open_items": list(open_items),
            }
        )
    return True, out


def _entity_grounded(
    name: str,
    alias: Optional[str],
    source_blob: str,
    active_facts: Dict[str, str],
    entity_names: Set[str],
) -> bool:
    try:
        from . import retrieve as retrieve_mod
    except ImportError:
        import retrieve as retrieve_mod

    def ok(surface: str) -> bool:
        s = surface.strip()
        if not s:
            return False
        # R1: word-boundary / phrase match in turns and fact texts
        if retrieve_mod.surface_matches_text(s, source_blob):
            return True
        for text in active_facts.values():
            if retrieve_mod.surface_matches_text(s, text or ""):
                return True
        if s.casefold() in entity_names:
            return True
        return False

    if not ok(name):
        return False
    if alias is not None and str(alias).strip() and not ok(str(alias)):
        return False
    return True


def resolve_stated_time(evidence: str, user_time_iso: str) -> Optional[str]:
    """Resolve approved phrase table against the turn's user_time. Date-only unless clock stated."""
    resolved, _reason = resolve_stated_time_with_reason(evidence, user_time_iso)
    return resolved


def resolve_stated_time_with_reason(
    evidence: str, user_time_iso: str
) -> Tuple[Optional[str], Optional[str]]:
    """Like ``resolve_stated_time``, plus a failure reason code when unresolved.

    Reason codes (F2): ``unparseable_user_time`` | ``phrase_not_in_table`` |
    ``future`` | ``other``.
    """
    if not (user_time_iso or "").strip():
        return None, "unparseable_user_time"
    turn_dt = _parse_iso(user_time_iso)
    if turn_dt is None:
        return None, "unparseable_user_time"
    turn_local = time_context.localize_marker(turn_dt)
    turn_date = turn_local.date()
    ev = (evidence or "").strip().casefold()
    if not ev:
        return None, "phrase_not_in_table"

    clock = _extract_clock(ev)

    def pack(d: date) -> Tuple[Optional[str], Optional[str]]:
        if d > turn_date:
            return None, "future"
        if clock is not None:
            hh, mm = clock
            dt = datetime(d.year, d.month, d.day, hh, mm, tzinfo=turn_local.tzinfo)
            return time_context.marker_iso(dt), None
        return d.isoformat(), None

    if ev == "today" or ev in (
        "this morning",
        "this afternoon",
        "this evening",
        "tonight",
    ):
        return pack(turn_date)
    if ev == "last night":
        return pack(turn_date - timedelta(days=1))
    if ev == "yesterday":
        return pack(turn_date - timedelta(days=1))
    if ev == "the day before yesterday":
        return pack(turn_date - timedelta(days=2))
    # P6-FIX-2: last weekend → Sat–Sun interval (Sunday = most recent Sunday
    # strictly before the turn's local date). Never a single day.
    if ev == "last weekend":
        # Mon→1 … Sat→6, Sun→7 so "this Sunday" is never selected.
        delta_to_prev_sunday = turn_date.weekday() + 1
        sunday = turn_date - timedelta(days=delta_to_prev_sunday)
        saturday = sunday - timedelta(days=1)
        if sunday > turn_date:
            return None, "future"
        return f"{saturday.isoformat()}/{sunday.isoformat()}", None
    m = re.fullmatch(r"(\d+)\s+days?\s+ago", ev)
    if m:
        return pack(turn_date - timedelta(days=int(m.group(1))))
    m = re.fullmatch(r"last\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", ev)
    if m:
        target = WEEKDAYS[m.group(1)]
        delta = (turn_date.weekday() - target) % 7
        if delta == 0:
            delta = 7
        return pack(turn_date - timedelta(days=delta))
    m = re.fullmatch(r"on\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", ev)
    if m:
        target = WEEKDAYS[m.group(1)]
        delta = (turn_date.weekday() - target) % 7
        if delta == 0 or delta > 6:
            return None, "other"
        return pack(turn_date - timedelta(days=delta))
    # explicit month+day optional year
    m = re.fullmatch(
        r"(?:on\s+)?(january|february|march|april|may|june|july|august|"
        r"september|october|november|december|jan|feb|mar|apr|jun|jul|aug|"
        r"sep|sept|oct|nov|dec)\s+(\d{1,2})(?:\s*,?\s*(\d{4}))?",
        ev,
    )
    if m:
        month = _MONTHS[m.group(1)]
        day = int(m.group(2))
        year = int(m.group(3)) if m.group(3) else turn_date.year
        try:
            d = date(year, month, day)
        except ValueError:
            return None, "other"
        if m.group(3) is None and d > turn_date:
            try:
                d = date(year - 1, month, day)
            except ValueError:
                return None, "other"
        return pack(d)
    return None, "phrase_not_in_table"


def _extract_clock(ev: str) -> Optional[Tuple[int, int]]:
    m = re.search(r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b", ev)
    if not m:
        m = re.search(r"\b(\d{1,2})\s*(am|pm)\b", ev)
        if not m:
            return None
        hh = int(m.group(1))
        mm = 0
        ap = m.group(2)
    else:
        hh = int(m.group(1))
        mm = int(m.group(2))
        ap = m.group(3)
    if ap:
        if hh == 12:
            hh = 0
        if ap == "pm":
            hh += 12
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        return None
    return hh, mm


def _parse_iso(value: str) -> Optional[datetime]:
    text = (value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _commit(
    conn: sqlite3.Connection,
    token: Dict[str, Any],
    rows: Sequence[sqlite3.Row],
    episodes: List[Dict[str, Any]],
    pending_ids: List[str],
) -> bool:
    by_id = {r["id"]: r for r in rows}
    with store.locked(conn):
        try:
            conn.execute("BEGIN IMMEDIATE")
            if not forget.can_commit(conn, token):
                conn.execute("ROLLBACK")
                memlog.write_event(
                    memlog.LOG_EVENT_CONSOLIDATE_DISCARD,
                    reason="generation_or_ids",
                )
                return False
            now = time_context.marker_iso(time_context.capture_now())
            for ep in episodes:
                eid = str(uuid.uuid4())
                start = by_id[ep["source_turn_range"]["start_pending_id"]]
                end = by_id[ep["source_turn_range"]["end_pending_id"]]
                source_user_time = start["user_time"]
                conn.execute(
                    "INSERT INTO episodes ("
                    "  id, summary, significance, event_time, event_time_basis,"
                    "  event_time_evidence, open_items_json, source_session_id,"
                    "  source_turn_start, source_turn_end, recorded_at, source_user_time"
                    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        eid,
                        ep["summary"],
                        ep["significance"],
                        ep["event_time"],
                        ep["event_time_basis"],
                        ep["event_time_evidence"],
                        json.dumps(ep["open_items"], separators=(",", ":")),
                        start["session_id"],
                        int(start["turn_index"]),
                        int(end["turn_index"]),
                        now,
                        source_user_time,
                    ),
                )
                conn.execute(
                    "INSERT INTO episodes_fts (episode_id, summary) VALUES (?, ?)",
                    (eid, ep["summary"]),
                )
                for ent in ep["entities"]:
                    ent_id = _upsert_entity(
                        conn, ent.get("id"), ent["name"], ent["kind"], ent.get("alias")
                    )
                    conn.execute(
                        "INSERT OR IGNORE INTO episode_entities (episode_id, entity_id) "
                        "VALUES (?, ?)",
                        (eid, ent_id),
                    )
                for fid in ep["fact_refs"]:
                    conn.execute(
                        "INSERT OR IGNORE INTO episode_fact_refs (episode_id, fact_id) "
                        "VALUES (?, ?)",
                        (eid, fid),
                    )
            for pid in pending_ids:
                conn.execute("DELETE FROM pending_turns WHERE id = ?", (pid,))
            conn.execute("COMMIT")
            # P6-EPISODES: G-ERASE sanitize after every consolidate commit (episodes or zero)
            # so deleted pending frames leave the WAL — Phase 7-WAL
            try:
                store.sanitize_after_erase(conn)
            except Exception:
                pass
            return True
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            return False


def _upsert_entity(
    conn: sqlite3.Connection,
    existing_id: Optional[str],
    name: str,
    kind: str,
    alias: Optional[str],
) -> str:
    if existing_id:
        return str(existing_id)
    norm = name.strip().casefold()
    row = conn.execute(
        "SELECT id FROM entities WHERE lower(name) = ?", (norm,)
    ).fetchone()
    if row is None:
        row = conn.execute(
            "SELECT entity_id AS id FROM entity_aliases WHERE lower(alias) = ?",
            (norm,),
        ).fetchone()
    if row is not None:
        ent_id = row["id"]
    else:
        ent_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO entities (id, name, kind, created_at) VALUES (?, ?, ?, ?)",
            (
                ent_id,
                name.strip(),
                kind,
                time_context.marker_iso(time_context.capture_now()),
            ),
        )
        conn.execute(
            "INSERT INTO entities_fts (entity_id, name) VALUES (?, ?)",
            (ent_id, name.strip()),
        )
    if alias and alias.strip() and alias.strip().casefold() != norm:
        conn.execute(
            "INSERT OR IGNORE INTO entity_aliases (entity_id, alias) VALUES (?, ?)",
            (ent_id, alias.strip()),
        )
        # Also index alias surface for retrieval
        conn.execute(
            "INSERT INTO entities_fts (entity_id, name) VALUES (?, ?)",
            (ent_id, alias.strip()),
        )
    return ent_id


# --- lease ------------------------------------------------------------------------


def _acquire_lease(conn: sqlite3.Connection) -> bool:
    now = time_context.capture_now()
    expires = now.timestamp() + CONSOLIDATE_LEASE_TTL_S
    expires_iso = time_context.marker_iso(
        datetime.fromtimestamp(expires, tz=timezone.utc).astimezone(now.tzinfo)
    )
    with store.locked(conn):
        try:
            conn.execute("BEGIN IMMEDIATE")
            owner = store.meta_get(conn, store.META_CONSOLIDATE_LEASE_OWNER)
            exp = store.meta_get(conn, store.META_CONSOLIDATE_LEASE_EXPIRES_AT)
            exp_dt = _parse_iso(exp) if exp else None
            if owner and exp_dt is not None and exp_dt > now and owner != _instance_id:
                conn.execute("ROLLBACK")
                memlog.write_event(
                    memlog.LOG_EVENT_CONSOLIDATE_LEASE,
                    action="busy",
                    ok=False,
                )
                return False
            store.meta_set(conn, store.META_CONSOLIDATE_LEASE_OWNER, _instance_id)
            store.meta_set(conn, store.META_CONSOLIDATE_LEASE_EXPIRES_AT, expires_iso)
            conn.execute("COMMIT")
            memlog.write_event(
                memlog.LOG_EVENT_CONSOLIDATE_LEASE,
                action="acquired",
                ok=True,
            )
            return True
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            return False


def _renew_lease(conn: sqlite3.Connection) -> None:
    now = time_context.capture_now()
    expires = now.timestamp() + CONSOLIDATE_LEASE_TTL_S
    expires_iso = time_context.marker_iso(
        datetime.fromtimestamp(expires, tz=timezone.utc).astimezone(now.tzinfo)
    )
    with store.locked(conn):
        try:
            conn.execute("BEGIN IMMEDIATE")
            owner = store.meta_get(conn, store.META_CONSOLIDATE_LEASE_OWNER)
            if owner != _instance_id:
                conn.execute("ROLLBACK")
                return
            store.meta_set(conn, store.META_CONSOLIDATE_LEASE_EXPIRES_AT, expires_iso)
            conn.execute("COMMIT")
            memlog.write_event(
                memlog.LOG_EVENT_CONSOLIDATE_LEASE,
                action="renewed",
                ok=True,
            )
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass


def _release_lease(conn: sqlite3.Connection) -> None:
    with store.locked(conn):
        try:
            conn.execute("BEGIN IMMEDIATE")
            owner = store.meta_get(conn, store.META_CONSOLIDATE_LEASE_OWNER)
            if owner == _instance_id:
                store.meta_set(conn, store.META_CONSOLIDATE_LEASE_OWNER, "")
                store.meta_set(conn, store.META_CONSOLIDATE_LEASE_EXPIRES_AT, "")
            conn.execute("COMMIT")
            memlog.write_event(
                memlog.LOG_EVENT_CONSOLIDATE_LEASE,
                action="released",
                ok=True,
            )
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
