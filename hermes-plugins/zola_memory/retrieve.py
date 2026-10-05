"""Episode retrieval for prefetch (P6-D04)."""

from __future__ import annotations

import json
import re
import sqlite3
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

try:
    from . import forget
    from . import log as memlog
    from . import store
    from . import time_context
except ImportError:  # P6-EPISODES: flat unittest discover top — P6-D04
    import forget
    import log as memlog
    import store
    import time_context

# P6-EPISODES: retrieval floor — Phase 4b calibration (see progress doc) — P6-D04
# Per-candidate gate (X3) drops single-common-word overlaps (tonight/car/work/weekend).
# Qualifying related hits score ≥ 1.0 via entity-name boost; must-not-surface score 0.
EPISODE_MIN_SCORE = 0.15
MAX_EPISODES_PER_TURN = 3
# P6-FIX-2: say-when cue — first line of the prefetch block (exact) — P6-D05
EPISODES_BLOCK_HEADER = (
    '[Episodes — past conversations. If you use one, mention roughly when it was '
    '(e.g. "yesterday", "last week").]'
)

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+", re.UNICODE)
_NUMBER_RE = re.compile(r"\d+")


def set_episode_min_score_for_tests(value: float) -> None:
    global EPISODE_MIN_SCORE
    EPISODE_MIN_SCORE = float(value)


def distinctive_terms(query: str) -> List[str]:
    """Query terms filtered by Track 4 stopwords (len≥3)."""
    out: List[str] = []
    seen: Set[str] = set()
    for tok in _TOKEN_RE.findall(query or ""):
        low = tok.casefold()
        if len(low) < 3 or low in forget._STOPWORDS:
            continue
        if low in seen:
            continue
        seen.add(low)
        out.append(low)
    return out


def extract_numbers(text: str) -> Set[str]:
    return set(_NUMBER_RE.findall(text or ""))


def surface_matches_text(surface: str, text: str) -> bool:
    """Casefold word-boundary / multi-word phrase match (R1)."""
    parts = _TOKEN_RE.findall((surface or "").casefold())
    if not parts:
        return False
    pattern = r"\b" + r"\s+".join(re.escape(p) for p in parts) + r"\b"
    return re.search(pattern, (text or "").casefold(), re.UNICODE) is not None


def candidate_passes_gate(
    *,
    entity_hit: bool,
    query_terms: Sequence[str],
    query_numbers: Set[str],
    episode_text: str,
) -> bool:
    """X3 per-candidate: entity hit, shared number, or ≥ 2 shared distinctive terms."""
    if entity_hit:
        return True
    shared_numbers = query_numbers & extract_numbers(episode_text)
    if shared_numbers:
        return True
    ep_terms = set(distinctive_terms(episode_text))
    shared = sum(1 for t in query_terms if t in ep_terms)
    return shared >= 2


def format_short_date(when: datetime) -> str:
    local = time_context.localize_marker(when)
    dow = time_context.DOW_NAMES[local.weekday()]
    month = time_context.MONTH_NAMES[local.month - 1]
    return f"{dow} {month} {local.day}"


def format_calendar_relative(now: datetime, when: datetime) -> str:
    """Date-only relative wording: today / yesterday / day-week buckets — never hours."""
    now_local = time_context.localize_marker(now)
    last_local = time_context.localize_marker(when)
    cal_days = (now_local.date() - last_local.date()).days
    if cal_days == 0:
        return "today"
    if cal_days == 1:
        return "yesterday"
    if 2 <= cal_days < 14:
        return f"{cal_days} days ago"
    if cal_days >= 14:
        weeks = cal_days // 7
        if weeks == 1:
            return "a week ago"
        return f"{weeks} weeks ago"
    return "date unknown"


def format_episode_line(
    *,
    source_user_time: Optional[str],
    event_time: Optional[str],
    summary: str,
    open_items: Sequence[str],
    now: Optional[datetime] = None,
) -> str:
    now = now or time_context.capture_now()
    talked = _format_when_side(source_user_time, now)
    happened = _format_happened(event_time, now)
    line = f"- talked about {talked} · happened: {happened} · {summary}"
    items = [x for x in open_items if x]
    if items:
        line += " · still open: " + "; ".join(items)
    return line


def _format_when_side(iso: Optional[str], now: datetime) -> str:
    dt = _parse_iso(iso) if iso else None
    if dt is None:
        return "date unknown"
    return f"{format_short_date(dt)} ({format_calendar_relative(now, dt)})"


def _format_happened(event_time: Optional[str], now: datetime) -> str:
    if not event_time:
        return "date unknown"
    text = event_time.strip()
    # P6-FIX-2: Sat–Sun ISO interval from "last weekend"
    m = re.fullmatch(
        r"(\d{4}-\d{2}-\d{2})/(\d{4}-\d{2}-\d{2})",
        text,
    )
    if m:
        try:
            y1, mo1, d1 = (int(x) for x in m.group(1).split("-"))
            y2, mo2, d2 = (int(x) for x in m.group(2).split("-"))
            sat = date(y1, mo1, d1)
            sun = date(y2, mo2, d2)
        except ValueError:
            return "date unknown"
        return format_weekend_happened(sat, sun, now)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        y, mth, d = (int(x) for x in text.split("-"))
        dt = datetime(y, mth, d, 12, 0, tzinfo=now.tzinfo or timezone.utc)
        return f"{format_short_date(dt)} ({format_calendar_relative(now, dt)})"
    dt = _parse_iso(text)
    if dt is None:
        return "date unknown"
    return f"{format_short_date(dt)} ({format_calendar_relative(now, dt)})"


def format_weekend_happened(sat: date, sun: date, now: datetime) -> str:
    """Display Sat–Sun interval: 'the weekend of Oct 3–4 (last weekend)'."""
    if sat.month == sun.month and sat.year == sun.year:
        span = f"{time_context.MONTH_NAMES[sat.month - 1]} {sat.day}–{sun.day}"
    else:
        span = (
            f"{time_context.MONTH_NAMES[sat.month - 1]} {sat.day}–"
            f"{time_context.MONTH_NAMES[sun.month - 1]} {sun.day}"
        )
    now_local = time_context.localize_marker(now).date()
    most_recent_sunday = now_local - timedelta(days=(now_local.weekday() + 1))
    if sun == most_recent_sunday:
        rel = "last weekend"
    else:
        sun_dt = datetime(
            sun.year, sun.month, sun.day, 12, 0, tzinfo=now.tzinfo or timezone.utc
        )
        rel = format_calendar_relative(now, sun_dt)
    return f"the weekend of {span} ({rel})"


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value or not str(value).strip():
        return None
    text = str(value).strip()
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            y, m, d = (int(x) for x in text.split("-"))
            return datetime(y, m, d, 12, 0, tzinfo=timezone.utc)
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _entity_name_hits(conn: sqlite3.Connection, query: str) -> Set[str]:
    """Episode ids linked to entities whose name/alias matches query on word boundaries."""
    hits: Set[str] = set()
    for e in conn.execute("SELECT id, name FROM entities"):
        surfaces = [e["name"] or ""]
        for a in conn.execute(
            "SELECT alias FROM entity_aliases WHERE entity_id = ?", (e["id"],)
        ):
            surfaces.append(a["alias"] or "")
        if not any(surface_matches_text(s, query) for s in surfaces if s.strip()):
            continue
        for r in conn.execute(
            "SELECT episode_id FROM episode_entities WHERE entity_id = ?",
            (e["id"],),
        ):
            hits.add(r["episode_id"])
    return hits


def _episode_blob(conn: sqlite3.Connection, episode_id: str) -> str:
    row = conn.execute(
        "SELECT summary FROM episodes WHERE id = ?", (episode_id,)
    ).fetchone()
    parts = [row["summary"] or ""] if row else []
    for r in conn.execute(
        "SELECT e.name AS name FROM episode_entities ee "
        "JOIN entities e ON e.id = ee.entity_id WHERE ee.episode_id = ?",
        (episode_id,),
    ):
        parts.append(r["name"] or "")
    for r in conn.execute(
        "SELECT a.alias AS alias FROM episode_entities ee "
        "JOIN entity_aliases a ON a.entity_id = ee.entity_id "
        "WHERE ee.episode_id = ?",
        (episode_id,),
    ):
        parts.append(r["alias"] or "")
    return "\n".join(parts)


def retrieve_episodes(
    conn: sqlite3.Connection,
    query: str,
    *,
    platform: str = "",
    parent_session_id: str = "",
) -> str:
    t0 = time.perf_counter()
    if not forget.is_brian_conversation(platform, parent_session_id):
        memlog.write_event(
            memlog.LOG_EVENT_RETRIEVE,
            candidates=0,
            returned=0,
            top_score=0,
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )
        return ""

    terms = distinctive_terms(query)
    query_numbers = extract_numbers(query)
    entity_eps = _entity_name_hits(conn, query)

    # Pool: FTS hits + entity-linked episodes (gate is per-candidate, not query-level)
    candidates: Dict[str, float] = {}
    if terms:
        match = " OR ".join(f'"{t}"' for t in terms)
        try:
            for r in conn.execute(
                "SELECT episode_id, bm25(episodes_fts) AS score "
                "FROM episodes_fts WHERE episodes_fts MATCH ? "
                "ORDER BY score LIMIT 50",
                (match,),
            ):
                candidates[r["episode_id"]] = max(
                    candidates.get(r["episode_id"], float("-inf")),
                    -float(r["score"]),
                )
        except sqlite3.Error:
            pass
        try:
            for r in conn.execute(
                "SELECT entity_id, name FROM entities_fts "
                "WHERE entities_fts MATCH ?",
                (match,),
            ):
                # R1: only boost when the entity surface matches the query on boundaries
                ent = conn.execute(
                    "SELECT name FROM entities WHERE id = ?", (r["entity_id"],)
                ).fetchone()
                surfaces = [ent["name"] if ent else ""]
                for a in conn.execute(
                    "SELECT alias FROM entity_aliases WHERE entity_id = ?",
                    (r["entity_id"],),
                ):
                    surfaces.append(a["alias"] or "")
                if not any(
                    surface_matches_text(s, query) for s in surfaces if s and s.strip()
                ):
                    continue
                for link in conn.execute(
                    "SELECT episode_id FROM episode_entities WHERE entity_id = ?",
                    (r["entity_id"],),
                ):
                    eid = link["episode_id"]
                    candidates[eid] = max(candidates.get(eid, 0.0), 1.0)
        except sqlite3.Error:
            pass

    for eid in entity_eps:
        candidates[eid] = max(candidates.get(eid, 0.0), 1.0)

    if not candidates:
        memlog.write_event(
            memlog.LOG_EVENT_RETRIEVE,
            candidates=0,
            returned=0,
            top_score=0,
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )
        return ""

    suppressed = forget.is_suppressed(conn, list(candidates.keys()))
    qualified: List[Tuple[str, float]] = []
    for eid, score in candidates.items():
        if eid in suppressed:
            continue
        entity_hit = eid in entity_eps
        blob = _episode_blob(conn, eid)
        if not candidate_passes_gate(
            entity_hit=entity_hit,
            query_terms=terms,
            query_numbers=query_numbers,
            episode_text=blob,
        ):
            continue
        if score > EPISODE_MIN_SCORE:
            qualified.append((eid, score))

    qualified.sort(key=lambda x: x[1], reverse=True)
    top = qualified[:MAX_EPISODES_PER_TURN]
    top_score = top[0][1] if top else 0.0

    now = time_context.capture_now()
    lines: List[str] = []
    for eid, _score in top:
        row = conn.execute(
            "SELECT summary, event_time, open_items_json, source_user_time "
            "FROM episodes WHERE id = ?",
            (eid,),
        ).fetchone()
        if row is None:
            continue
        try:
            open_items = json.loads(row["open_items_json"] or "[]")
        except json.JSONDecodeError:
            open_items = []
        if not isinstance(open_items, list):
            open_items = []
        lines.append(
            format_episode_line(
                source_user_time=row["source_user_time"],
                event_time=row["event_time"],
                summary=row["summary"] or "",
                open_items=[str(x) for x in open_items],
                now=now,
            )
        )

    memlog.write_event(
        memlog.LOG_EVENT_RETRIEVE,
        candidates=len(candidates),
        returned=len(lines),
        top_score=round(top_score, 4),
        elapsed_ms=int((time.perf_counter() - t0) * 1000),
    )
    if not lines:
        return ""
    return EPISODES_BLOCK_HEADER + "\n" + "\n".join(lines)
