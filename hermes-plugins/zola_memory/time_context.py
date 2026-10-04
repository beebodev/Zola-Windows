"""Ambient turn timestamps and cross-session gap (P6-D05)."""

from __future__ import annotations

import time as _time
from datetime import datetime, timezone
from typing import Any, Callable, Optional

try:
    from . import log as memlog
    from . import store
except ImportError:  # P6-TIME: flat unittest discover top — P6-D05
    import log as memlog
    import store

# P6-TIME: only genuine Brian TUI turns update the marker — P6-D05
USER_TURN_PLATFORMS = frozenset({"tui"})

# P6-TIME: tunable gap threshold (minutes) — P6-D05
MEANINGFUL_GAP_MINUTES = 30

# P6-TIME: locale-independent English names — P6-D05
DOW_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MONTH_NAMES = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)

# P6-TIME: Windows long TZ names → short abbrev (US zones) — P6-D05
WINDOWS_TZ_ABBREV = {
    "Pacific Standard Time": "PST",
    "Pacific Daylight Time": "PDT",
    "Mountain Standard Time": "MST",
    "Mountain Daylight Time": "MDT",
    "Central Standard Time": "CST",
    "Central Daylight Time": "CDT",
    "Eastern Standard Time": "EST",
    "Eastern Daylight Time": "EDT",
    "Alaskan Standard Time": "AKST",
    "Alaskan Daylight Time": "AKDT",
    "Hawaiian Standard Time": "HST",
    "Hawaiian Daylight Time": "HDT",
}

_UNSET = object()
_clock_override: Optional[Callable[[], datetime]] = None
_tz_override: object = _UNSET


def set_clock_for_tests(
    clock: Optional[Callable[[], datetime]] = None,
    *,
    timezone: object = _UNSET,
) -> None:
    """Test helper: inject clock and/or timezone (``timezone=None`` = system-local)."""
    global _clock_override, _tz_override
    _clock_override = clock
    if timezone is not _UNSET:
        _tz_override = timezone
    elif clock is None:
        _tz_override = _UNSET


def capture_now() -> datetime:
    """Capture the single turn instant (G-ORDER)."""
    if _clock_override is not None:
        return _clock_override()
    from hermes_time import now as hermes_now

    return hermes_now()


def get_active_timezone() -> Any:
    """Configured Hermes timezone, or None for server-local (test-overridable)."""
    if _tz_override is not _UNSET:
        return _tz_override
    from hermes_time import get_timezone

    return get_timezone()


def localize_marker(last: datetime) -> datetime:
    """Localize a stored marker for display and calendar-day math."""
    # P6-TIME: never last.astimezone(now.tzinfo) — fixed offsets break DST hours — P6-D05
    tz = get_active_timezone()
    if tz is not None:
        return last.astimezone(tz)
    return last.astimezone()


def is_user_turn(platform: str, parent_session_id: str) -> bool:
    """Allow-list predicate: tui + empty parent only (fail closed)."""
    # P6-TIME: unknown/future platforms never stamp or move the marker — P6-D05
    return (
        str(platform or "").strip().lower() in USER_TURN_PLATFORMS
        and not str(parent_session_id or "").strip()
    )


def short_zone_label(when: datetime) -> str:
    """Short zone: IANA %Z if short; else Windows long-name map; else UTC±HH:MM."""
    abbrev = when.strftime("%Z") or ""
    if abbrev and len(abbrev) <= 5 and " " not in abbrev:
        return abbrev
    mapped = WINDOWS_TZ_ABBREV.get(abbrev)
    if mapped:
        return mapped
    offset = when.utcoffset()
    if offset is None:
        return "UTC"
    total = int(offset.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    hours, rem = divmod(total, 3600)
    minutes = rem // 60
    return f"UTC{sign}{hours:02d}:{minutes:02d}"


def format_stamp_body(when: datetime) -> str:
    """``Fri Oct 2, 3:45 PM PDT`` — integers for day/hour/minute; fixed English names."""
    dow = DOW_NAMES[when.weekday()]
    month = MONTH_NAMES[when.month - 1]
    day = when.day
    hour24 = when.hour
    minute = when.minute
    hour12 = hour24 % 12
    if hour12 == 0:
        hour12 = 12
    ampm = "AM" if hour24 < 12 else "PM"
    zone = short_zone_label(when)
    return f"{dow} {month} {day}, {hour12}:{minute:02d} {ampm} {zone}"


def format_stamp(now: datetime) -> str:
    """Labeled stamp line for model-facing injection."""
    return f"[Time: {format_stamp_body(now)}]"


def format_relative(now: datetime, last: datetime) -> str:
    """Relative gap wording (calendar day/week buckets; singular forms)."""
    # P6-TIME: Track 5 reuses this function — P6-D05
    last_local = localize_marker(last)
    now_local = localize_marker(now)

    delta = now_local - last_local
    total_seconds = int(delta.total_seconds())
    if total_seconds < 0:
        total_seconds = 0
    total_minutes = total_seconds // 60
    cal_days = (now_local.date() - last_local.date()).days

    if total_seconds < 60:
        return "less than a minute ago"
    if total_minutes < 60:
        if total_minutes == 1:
            return "1 minute ago"
        return f"{total_minutes} minutes ago"
    if cal_days == 1:
        return "yesterday"
    if 2 <= cal_days < 14:
        return f"{cal_days} days ago"
    if cal_days >= 14:
        weeks = cal_days // 7
        if weeks == 1:
            return "a week ago"
        return f"{weeks} weeks ago"
    # Same calendar day, ≥ 60 minutes
    hours = max(1, int(round(total_minutes / 60)))
    if hours == 1:
        return "about an hour ago"
    return f"about {hours} hours ago"


def build_turn_time_context(now: datetime, last_interaction_at: Optional[str]) -> str:
    """Build stamp (+ gap line when threshold met). Pure; no I/O."""
    stamp = format_stamp(now)
    last = _parse_marker(last_interaction_at)
    if last is None:
        return stamp
    delta = now - last
    gap_minutes = int(delta.total_seconds() // 60)
    if gap_minutes < MEANINGFUL_GAP_MINUTES:
        return stamp
    last_local = localize_marker(last)
    relative = format_relative(now, last)
    past_body = format_stamp_body(last_local)
    gap = f"[Gap: Brian's last message to me was {relative} ({past_body}).]"
    return stamp + "\n" + gap


def _parse_marker(value: Optional[str]) -> Optional[datetime]:
    if not value or not str(value).strip():
        return None
    text = str(value).strip()
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def marker_iso(now: datetime) -> str:
    """ISO-8601 with offset; time only (no gap text)."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc).astimezone()
    return now.isoformat(timespec="seconds")


def handle_pre_llm_call(provider: Any, **kwargs: Any) -> Optional[dict]:
    """G-ORDER hook: predicate → now → read → build → persist → return context."""
    t0 = _time.perf_counter()
    try:
        platform = kwargs.get("platform") or ""
        parent_session_id = kwargs.get("parent_session_id") or ""
        if not is_user_turn(platform, parent_session_id):
            return None

        conn = getattr(provider, "_conn", None)
        if conn is None:
            memlog.write_event(
                memlog.LOG_EVENT_TIME_CONTEXT,
                ok=False,
                gap_minutes="-",
                gap_line=False,
                elapsed_ms=int((_time.perf_counter() - t0) * 1000),
            )
            return None

        # P6-TIME: capture_now inside try — hook never raises into Hermes — P6-D05
        now = capture_now()
        with store.locked(conn):
            previous = store.meta_get(conn, store.META_LAST_INTERACTION_AT)
            block = build_turn_time_context(now, previous)
            last = _parse_marker(previous)
            gap_minutes_out: Any = "-"
            gap_line = False
            if last is not None:
                gap_minutes_val = int((now - last).total_seconds() // 60)
                if gap_minutes_val >= MEANINGFUL_GAP_MINUTES:
                    gap_minutes_out = gap_minutes_val
                    gap_line = True

            # P6-TIME: persist only after successful construction — P6-D05
            marker_ok = True
            try:
                conn.execute("BEGIN IMMEDIATE")
                try:
                    store.meta_set(conn, store.META_LAST_INTERACTION_AT, marker_iso(now))
                    conn.commit()
                except Exception:
                    marker_ok = False
                    conn.rollback()
            except Exception:
                marker_ok = False

        memlog.write_event(
            memlog.LOG_EVENT_TIME_MARKER_UPDATE,
            ok=marker_ok,
        )
        memlog.write_event(
            memlog.LOG_EVENT_TIME_CONTEXT,
            ok=True,
            gap_minutes=gap_minutes_out,
            gap_line=gap_line,
            elapsed_ms=int((_time.perf_counter() - t0) * 1000),
        )
        # P6-TIME: keep AUD-36 pre_llm_call visibility — P6-D05
        memlog.write_event(
            memlog.LOG_EVENT_PRE_LLM_CALL,
            session_id=kwargs.get("session_id") or "-",
            observer=1,
        )
        return {"context": block}
    except Exception:
        memlog.write_event(
            memlog.LOG_EVENT_TIME_CONTEXT,
            ok=False,
            gap_minutes="-",
            gap_line=False,
            elapsed_ms=int((_time.perf_counter() - t0) * 1000),
        )
        return None
