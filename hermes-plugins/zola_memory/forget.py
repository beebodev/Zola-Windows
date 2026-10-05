"""Forget-intent, cascade erase, disposition, hold, and forget_memory tool (P6-D06)."""

from __future__ import annotations

import json
import re
import sqlite3
import time
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

try:
    from . import log as memlog
except ImportError:  # P6-STORE: flat unittest discover top — P6-D03
    import log as memlog

# P6-STORE: forget-intent phrases — escalation only — P6-D06
FORGET_INTENT_PHRASES = (
    "forget",
    "don't remember",
    "do not remember",
    "don't keep",
    "do not keep",
    "stop remembering",
    "delete",
    "erase",
    "remove that",
    "get rid of",
    "no longer remember",
)

# P6-STORE: bare "forget" cancelled inside these phrases — P6-D06
FORGET_INTENT_EXCLUSIONS = (
    "don't forget",
    "do not forget",
    "never forget",
    "won't forget",
    "not forget",
)

RECORD_KIND_FACT = "fact"
RECORD_KIND_EPISODE = "episode"
RECORD_KIND_PENDING = "pending_turn"
KIND_NOTEBOOK_FACT = "notebook_fact"

ERASE_REASON_REMOVE = "remove"
ERASE_REASON_FORGET_INTENT = "forget_intent"
ERASE_REASON_FILE_CHECK = "file_check"
ERASE_REASON_PENDING_RETRY = "pending_retry"
ERASE_REASON_TOOL = "tool"
ERASE_REASON_HOLD_EXECUTE = "hold_execute"

META_PENDING_ERASURES = "pending_erasures"
META_CONSOLIDATION_GENERATION = "consolidation_generation"
META_FORGET_HOLD = "forget_hold"

# P6-FORGET: hold / disposition tunables — P6-D06
FORGET_HOLD_MAX_MINUTES = 30
DISPOSITION_ENTRY_TTL_MINUTES = 30
HOLD_MAX_TURNS = 3

# P6-FORGET: same Brian-conversation predicate as time_context — P6-D06
USER_TURN_PLATFORMS = frozenset({"tui"})

TOOL_NAME = "forget_memory"
MEMORY_TOOL_NAME = "memory"

# P6-EPISODES: G3 confirm=false / ask_brian=true + confirm=true guard block — P6-D04
MSG_ASK_BRIAN_MULTI = (
    "These look like different things. Ask Brian which one he means before calling "
    "confirm=true. Do not use the memory tool to remove or replace anything until he "
    "answers — those calls are blocked until then."
)
# P6-EPISODES: G2 memory remove/replace block while ask pending — P6-D04
MSG_ASK_BRIAN_MEMORY_BLOCK = (
    "Brian hasn't said which one yet — ask him which he means before removing anything."
)

TOOL_DESCRIPTION = (
    "Erase provider-held memory copies (index facts, episodes, pending turns) after Brian asks "
    "to forget something. Erase-only: never creates or edits notes. Current notebook facts in "
    "USER.md/MEMORY.md must be removed with the memory tool's remove action (that path also runs "
    "the erase cascade). Two steps: confirm=false to list candidates; confirm=true with target_ids "
    "Brian chose. If candidates are different subjects, ask him which one before confirming."
)

FORGET_MEMORY_SCHEMA: Dict[str, Any] = {
    "name": TOOL_NAME,
    "description": TOOL_DESCRIPTION,
    "parameters": {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "What Brian wants forgotten (his words or a short paraphrase).",
            },
            "confirm": {
                "type": "boolean",
                "description": (
                    "false = search and return candidates only; "
                    "true = erase target_ids from the last candidate list."
                ),
            },
            "target_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "IDs from the latest confirm=false result. Required when confirm=true.",
            },
        },
        "required": ["description", "confirm"],
    },
}

# P6-FORGET: matcher stopwords / always-present — P6-D06
_STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "to",
        "of",
        "and",
        "or",
        "in",
        "on",
        "at",
        "for",
        "with",
        "from",
        "that",
        "this",
        "it",
        "as",
        "by",
        "he",
        "she",
        "they",
        "we",
        "you",
        "i",
        "my",
        "his",
        "her",
        "their",
        "our",
        "about",
        "into",
        "than",
        "then",
        "so",
        "if",
        "but",
        "not",
        "no",
        "yes",
        "just",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "can",
        "could",
        "should",
        "brian",
        "zola",
        "forget",
        "delete",
        "remove",
        "remember",
        "please",
        "mon",
        "tue",
        "wed",
        "thu",
        "fri",
        "sat",
        "sun",
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    }
)

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+", re.UNICODE)

# P6-STORE: test hook to simulate mid-erase failure — P6-D06
_erase_failure_hook: Optional[Callable[[], None]] = None


def set_erase_failure_hook(hook: Optional[Callable[[], None]]) -> None:
    global _erase_failure_hook
    _erase_failure_hook = hook


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_apostrophes(message: str) -> str:
    # P6-STORE: curly quotes → ASCII before phrase match — P6-D06
    return (message or "").replace("\u2019", "'").replace("\u2018", "'")


def has_forget_intent(message: str) -> bool:
    """True when the current user message matches a forget phrase (exclusions applied)."""
    if not message:
        return False
    lower = normalize_apostrophes(message).lower()
    exclusion_spans = []
    for excl in FORGET_INTENT_EXCLUSIONS:
        for match in re.finditer(re.escape(excl), lower):
            exclusion_spans.append((match.start(), match.end()))

    def _inside_exclusion(start: int, end: int) -> bool:
        return any(es <= start and end <= ee for es, ee in exclusion_spans)

    for phrase in FORGET_INTENT_PHRASES:
        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
        for match in re.finditer(pattern, lower):
            if phrase == "forget" and _inside_exclusion(match.start(), match.end()):
                continue
            return True
    return False


def new_id() -> str:
    return str(uuid.uuid4())


def is_brian_conversation(platform: Optional[str], parent_session_id: Optional[str]) -> bool:
    # P6-FORGET: tui + empty parent only — P6-D06
    return (platform or "").lower() in USER_TURN_PLATFORMS and not (parent_session_id or "")


def normalize_disposition_key(text: str) -> str:
    """Normalize user text for disposition keys (skill-strip best-effort + casefold)."""
    raw = text if isinstance(text, str) else ""
    try:
        from agent.memory_manager import MemoryManager

        stripped = MemoryManager._strip_skill_scaffolding(raw) or ""
    except Exception:
        stripped = raw
    collapsed = " ".join(unicodedata.normalize("NFKC", stripped).split())
    return collapsed.casefold()


# --- pending erasures / generation -------------------------------------------------


def _load_pending(conn: sqlite3.Connection) -> list[str]:
    row = conn.execute(
        "SELECT value FROM meta WHERE key = ?",
        (META_PENDING_ERASURES,),
    ).fetchone()
    if not row:
        return []
    try:
        data = json.loads(row[0])
        return [str(x) for x in data] if isinstance(data, list) else []
    except Exception:
        return []


def _save_pending(conn: sqlite3.Connection, ids: list[str]) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (META_PENDING_ERASURES, json.dumps(ids, separators=(",", ":"))),
    )


def _mark_pending_erasure(conn: sqlite3.Connection, fact_id: str) -> None:
    ok = False
    try:
        conn.execute("BEGIN IMMEDIATE")
        ids = _load_pending(conn)
        if fact_id not in ids:
            ids.append(fact_id)
        _save_pending(conn, ids)
        conn.execute("COMMIT")
        ok = True
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
    memlog.write_event(memlog.LOG_EVENT_PENDING_ERASURE_MARK, fact_id=fact_id, ok=ok)


def _remove_pending_erasure(conn: sqlite3.Connection, fact_id: str) -> None:
    ids = [x for x in _load_pending(conn) if x != fact_id]
    _save_pending(conn, ids)


def get_consolidation_generation(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT value FROM meta WHERE key = ?",
        (META_CONSOLIDATION_GENERATION,),
    ).fetchone()
    if not row:
        return 0
    try:
        return int(row[0])
    except Exception:
        return 0


def _bump_consolidation_generation(conn: sqlite3.Connection) -> None:
    """Bump generation; caller may be inside or outside a txn."""
    gen = get_consolidation_generation(conn) + 1
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (META_CONSOLIDATION_GENERATION, str(gen)),
    )


def bump_consolidation_generation_best_effort(conn: sqlite3.Connection) -> None:
    # P6-FORGET: failed cascade still bumps generation in a separate txn — P6-D06
    try:
        from . import store as _store
    except ImportError:
        import store as _store

    with _store.locked(conn):
        try:
            conn.execute("BEGIN IMMEDIATE")
            _bump_consolidation_generation(conn)
            conn.execute("COMMIT")
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass


def begin_consolidation(conn: sqlite3.Connection) -> Dict[str, Any]:
    pending_ids = sorted(
        str(r["id"])
        for r in conn.execute("SELECT id FROM pending_turns").fetchall()
    )
    return {
        "generation": get_consolidation_generation(conn),
        "pending_ids": pending_ids,
    }


def can_commit(conn: sqlite3.Connection, token: Dict[str, Any]) -> bool:
    # P6-FORGET: cannot commit while pending_erasures non-empty — P6-D06
    if _load_pending(conn):
        return False
    if get_consolidation_generation(conn) != int(token.get("generation", -1)):
        return False
    current = sorted(
        str(r["id"])
        for r in conn.execute("SELECT id FROM pending_turns").fetchall()
    )
    return current == list(token.get("pending_ids") or [])


def is_suppressed(conn: sqlite3.Connection, record_ids: Sequence[str]) -> Set[str]:
    pending = set(_load_pending(conn))
    return {str(x) for x in record_ids if str(x) in pending}


# --- matcher ----------------------------------------------------------------------


def _tokenize_with_spans(text: str) -> List[Tuple[str, int, bool]]:
    """Return (token_lower, start_index, is_capitalized_original)."""
    out: List[Tuple[str, int, bool]] = []
    for m in _TOKEN_RE.finditer(text or ""):
        raw = m.group(0)
        capped = (raw[:1].isupper() and raw[1:].islower()) or (
            raw.isupper() and len(raw) > 1
        )
        out.append((raw.lower(), m.start(), capped))
    return out


def _is_sentence_initial(text: str, start: int) -> bool:
    if start <= 0:
        return True
    i = start - 1
    while i >= 0 and text[i].isspace():
        i -= 1
    if i < 0:
        return True
    return text[i] in ".!?"


def derive_terms(texts: Sequence[str]) -> Tuple[Set[str], Set[str]]:
    """Return (strong_terms, ordinary_distinctive) from source texts."""
    strong: Set[str] = set()
    ordinary: Set[str] = set()
    for text in texts:
        tokens = _tokenize_with_spans(text or "")
        for tok, start, capitalized in tokens:
            if len(tok) < 3 or tok in _STOPWORDS:
                continue
            has_digit = any(ch.isdigit() for ch in tok)
            # P6-FORGET: proper name = capitalized, not sentence-initial, not stopword — P6-D06
            is_proper = capitalized and not _is_sentence_initial(text, start)
            if has_digit or is_proper:
                strong.add(tok)
            else:
                ordinary.add(tok)
    ordinary -= strong
    return strong, ordinary


def row_matches_terms(
    row_text: str,
    *,
    strong: Set[str],
    ordinary: Set[str],
    fact_ids: Set[str],
    row_fact_refs: Set[str],
) -> bool:
    if row_fact_refs & fact_ids:
        return True
    blob = (row_text or "").lower()
    if any(re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", blob) for t in strong):
        return True
    hits = sum(
        1
        for t in ordinary
        if re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", blob)
    )
    return hits >= 2


def derive_search_terms(description: str) -> Set[str]:
    """Recall-oriented terms for candidate search (D3) — not the cascade matcher.

    Any distinctive token (stopwords / command words excluded). Capitalized tokens
    count as names regardless of sentence position. Match is later ANY-term.
    """
    terms: Set[str] = set()
    # P6-FORGET: search does not apply sentence-initial proper-name exclusion — P6-D06
    for tok, _start, _capitalized in _tokenize_with_spans(description or ""):
        if len(tok) < 3 or tok in _STOPWORDS:
            continue
        terms.add(tok)
    return terms


def row_matches_search(row_text: str, terms: Set[str]) -> bool:
    """True if the row contains any distinctive search term (recall-oriented)."""
    if not terms:
        return False
    blob = (row_text or "").lower()
    return any(
        re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", blob) for t in terms
    )


def _episode_blob(row: sqlite3.Row) -> str:
    parts = [
        row["summary"] or "",
        row["significance"] or "",
        row["open_items_json"] or "",
        row["event_time_evidence"] or "",
    ]
    return "\n".join(parts)


def _pending_blob(row: sqlite3.Row) -> str:
    return f"{row['user_text'] or ''}\n{row['assistant_text'] or ''}"


# --- cascade ----------------------------------------------------------------------


def forget_cascade(
    conn: sqlite3.Connection,
    targets: Sequence[Dict[str, str]],
    *,
    reason: str,
    terms_source: Optional[str] = None,
) -> Tuple[bool, Dict[str, int]]:
    """Erase targets + linked/matched copies in one IMMEDIATE txn. Returns (ok, counts)."""
    try:
        from . import store as _store
    except ImportError:
        import store as _store

    zero = {
        "fact_rows": 0,
        "history_rows": 0,
        "fts_rows": 0,
        "episode_rows": 0,
        "pending_rows": 0,
        "link_rows": 0,
        "entity_rows": 0,
    }
    t0 = time.perf_counter()
    fact_ids = [t["id"] for t in targets if t.get("kind") == RECORD_KIND_FACT]
    episode_ids = {t["id"] for t in targets if t.get("kind") == RECORD_KIND_EPISODE}
    pending_ids = {t["id"] for t in targets if t.get("kind") == RECORD_KIND_PENDING}

    with _store.locked(conn):
        try:
            conn.execute("BEGIN IMMEDIATE")
            source_texts: List[str] = []
            if terms_source:
                source_texts.append(terms_source)

            counts = dict(zero)
            fts_tables_touched: List[str] = []
            for fact_id in list(fact_ids):
                row = conn.execute(
                    "SELECT id, text FROM facts WHERE id = ?",
                    (fact_id,),
                ).fetchone()
                if row is None:
                    continue
                source_texts.append(row["text"] or "")
                hist = conn.execute(
                    "SELECT COUNT(*) FROM fact_history WHERE fact_id = ?",
                    (fact_id,),
                ).fetchone()[0]
                fts = conn.execute(
                    "SELECT COUNT(*) FROM facts_fts WHERE fact_id = ?",
                    (fact_id,),
                ).fetchone()[0]
                conn.execute("DELETE FROM fact_history WHERE fact_id = ?", (fact_id,))
                conn.execute("DELETE FROM facts_fts WHERE fact_id = ?", (fact_id,))
                conn.execute("DELETE FROM facts WHERE id = ?", (fact_id,))
                counts["fact_rows"] += 1
                counts["history_rows"] += int(hist)
                counts["fts_rows"] += int(fts)
                if int(fts) > 0 and "facts_fts" not in fts_tables_touched:
                    fts_tables_touched.append("facts_fts")
                _remove_pending_erasure(conn, fact_id)

            if _erase_failure_hook is not None and counts["fact_rows"]:
                _erase_failure_hook()

            strong, ordinary = derive_terms(source_texts)
            fact_id_set = set(fact_ids)

            # Episodes via fact refs
            for fid in fact_id_set:
                for r in conn.execute(
                    "SELECT episode_id FROM episode_fact_refs WHERE fact_id = ?",
                    (fid,),
                ):
                    episode_ids.add(r["episode_id"])

            # Episodes via term match
            for r in conn.execute("SELECT * FROM episodes"):
                refs = {
                    x["fact_id"]
                    for x in conn.execute(
                        "SELECT fact_id FROM episode_fact_refs WHERE episode_id = ?",
                        (r["id"],),
                    )
                }
                if row_matches_terms(
                    _episode_blob(r),
                    strong=strong,
                    ordinary=ordinary,
                    fact_ids=fact_id_set,
                    row_fact_refs=refs,
                ):
                    episode_ids.add(r["id"])

            for eid in list(episode_ids):
                links = conn.execute(
                    "SELECT COUNT(*) FROM episode_entities WHERE episode_id = ?",
                    (eid,),
                ).fetchone()[0]
                refs_n = conn.execute(
                    "SELECT COUNT(*) FROM episode_fact_refs WHERE episode_id = ?",
                    (eid,),
                ).fetchone()[0]
                fts_n = 0
                try:
                    fts_n = conn.execute(
                        "SELECT COUNT(*) FROM episodes_fts WHERE episode_id = ?",
                        (eid,),
                    ).fetchone()[0]
                    conn.execute(
                        "DELETE FROM episodes_fts WHERE episode_id = ?", (eid,)
                    )
                    if int(fts_n) > 0 and "episodes_fts" not in fts_tables_touched:
                        fts_tables_touched.append("episodes_fts")
                except Exception:
                    pass
                conn.execute("DELETE FROM episode_entities WHERE episode_id = ?", (eid,))
                conn.execute("DELETE FROM episode_fact_refs WHERE episode_id = ?", (eid,))
                conn.execute("DELETE FROM episodes WHERE id = ?", (eid,))
                counts["episode_rows"] += 1
                counts["link_rows"] += int(links) + int(refs_n)
                counts["fts_rows"] += int(fts_n)

            for r in conn.execute("SELECT * FROM pending_turns"):
                if r["id"] in pending_ids or row_matches_terms(
                    _pending_blob(r),
                    strong=strong,
                    ordinary=ordinary,
                    fact_ids=fact_id_set,
                    row_fact_refs=set(),
                ):
                    pending_ids.add(r["id"])

            for pid in list(pending_ids):
                cur = conn.execute("DELETE FROM pending_turns WHERE id = ?", (pid,))
                counts["pending_rows"] += cur.rowcount

            # Orphan entities
            for ent in conn.execute("SELECT id FROM entities").fetchall():
                n = conn.execute(
                    "SELECT COUNT(*) FROM episode_entities WHERE entity_id = ?",
                    (ent["id"],),
                ).fetchone()[0]
                if n == 0:
                    try:
                        fts_n = conn.execute(
                            "SELECT COUNT(*) FROM entities_fts WHERE entity_id = ?",
                            (ent["id"],),
                        ).fetchone()[0]
                        conn.execute(
                            "DELETE FROM entities_fts WHERE entity_id = ?",
                            (ent["id"],),
                        )
                        counts["fts_rows"] += int(fts_n)
                        if int(fts_n) > 0 and "entities_fts" not in fts_tables_touched:
                            fts_tables_touched.append("entities_fts")
                    except Exception:
                        pass
                    conn.execute(
                        "DELETE FROM entity_aliases WHERE entity_id = ?",
                        (ent["id"],),
                    )
                    conn.execute("DELETE FROM entities WHERE id = ?", (ent["id"],))
                    counts["entity_rows"] += 1

            tomb_id = fact_ids[0] if fact_ids else (next(iter(episode_ids), None) or new_id())
            conn.execute(
                "INSERT OR REPLACE INTO tombstones (id, record_kind, erased_at, counts_json) "
                "VALUES (?, ?, ?, ?)",
                (
                    tomb_id,
                    RECORD_KIND_FACT if fact_ids else RECORD_KIND_EPISODE,
                    _utc_now(),
                    json.dumps(counts, separators=(",", ":")),
                ),
            )
            _bump_consolidation_generation(conn)
            conn.execute("COMMIT")
            memlog.write_event(
                memlog.LOG_EVENT_FORGET_CASCADE,
                reason=reason,
                **counts,
                ok=True,
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
            )
            if fact_ids:
                memlog.write_event(
                    memlog.LOG_EVENT_FACT_ERASE,
                    fact_id=fact_ids[0],
                    reason=reason,
                    history_rows=counts["history_rows"],
                    ok=True,
                )
            # P6-EPISODES: G-ERASE sanitize after commit, outside txn — P6-D04
            try:
                _store.sanitize_after_erase(
                    conn, fts_tables_touched=fts_tables_touched or list(_store.FTS_TABLES)
                )
            except Exception:
                pass
            return True, counts
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            memlog.write_event(
                memlog.LOG_EVENT_ERASE_ROLLBACK,
                fact_id=fact_ids[0] if fact_ids else "-",
            )
            for fid in fact_ids:
                _mark_pending_erasure(conn, fid)
            bump_consolidation_generation_best_effort(conn)
            memlog.write_event(
                memlog.LOG_EVENT_FORGET_CASCADE,
                reason=reason,
                **zero,
                ok=False,
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
            )
            if fact_ids:
                memlog.write_event(
                    memlog.LOG_EVENT_FACT_ERASE,
                    fact_id=fact_ids[0],
                    reason=reason,
                    history_rows=0,
                    ok=False,
                )
            return False, zero


def erase_fact(
    conn: sqlite3.Connection,
    fact_id: str,
    *,
    reason: str,
) -> bool:
    """Track-2 compatible wrapper: cascade a single fact target."""
    ok, _counts = forget_cascade(
        conn,
        [{"id": fact_id, "kind": RECORD_KIND_FACT}],
        reason=reason,
        terms_source=None,
    )
    return ok


# --- disposition / hold (process memory) ------------------------------------------


@dataclass
class ForgetSessionState:
    """Per-provider process memory for disposition, hold, and candidates."""

    disposition_drops: Dict[str, float] = field(default_factory=dict)
    forget_in_session: bool = False
    hold_user_texts: List[str] = field(default_factory=list)
    hold_started_at: Optional[float] = None
    hold_turn_count: int = 0
    candidate_ids: Set[str] = field(default_factory=set)
    candidate_meta: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # P6-EPISODES: multi-group ask unresolved — gates memory remove/replace + confirm=true — P6-D04
    ask_brian_pending: bool = False

    def clear_hold_process(self) -> None:
        self.hold_user_texts.clear()
        self.hold_started_at = None
        self.hold_turn_count = 0
        self.candidate_ids.clear()
        self.candidate_meta.clear()
        self.ask_brian_pending = False

    def clear_on_shutdown(self) -> None:
        self.disposition_drops.clear()
        self.forget_in_session = False
        self.clear_hold_process()


def mark_drop(state: ForgetSessionState, user_text: str) -> None:
    key = normalize_disposition_key(user_text)
    deadline = time.time() + DISPOSITION_ENTRY_TTL_MINUTES * 60
    state.disposition_drops[key] = deadline


def mark_after_notify_cascade(provider: Any, *, ok: bool) -> None:
    """D2: committed remove / replace-with-forget-intent marks the current turn (P6-D06)."""
    if not ok or provider is None:
        return
    state: ForgetSessionState = provider._forget_state
    state.forget_in_session = True
    mark_drop(state, getattr(provider, "_current_user_message", "") or "")


def expire_disposition_drops(state: ForgetSessionState) -> None:
    now = time.time()
    dead = [k for k, exp in state.disposition_drops.items() if exp <= now]
    for k in dead:
        del state.disposition_drops[k]


def turn_disposition(state: ForgetSessionState, user_content: str) -> Tuple[str, str]:
    """Return (keep|drop, reason). Cleared only by consumption / TTL / shutdown (E1).

    Drop when any of: (a) exact normalized key match; (b) a marked key is contained in
    the normalized sync content (Hermes active-turn redirect wraps the original); (c)
    has_forget_intent(user_content). Consume the matched key on (a)/(b) only.
    """
    expire_disposition_drops(state)
    key = normalize_disposition_key(user_content)
    if key in state.disposition_drops:
        del state.disposition_drops[key]
        return "drop", "marked"
    # (b) redirect-augmented sync: marked original is a substring of sync content
    for marked in list(state.disposition_drops):
        if marked and marked in key:
            del state.disposition_drops[marked]
            return "drop", "marked_contained"
    if has_forget_intent(user_content or ""):
        return "drop", "forget_intent"
    if state.forget_in_session and key == "":
        return "drop", "uncertain_after_forget"
    return "keep", "ordinary"


def hold_active(state: ForgetSessionState) -> bool:
    return state.hold_started_at is not None


def hold_expired_wall(state: ForgetSessionState) -> bool:
    if state.hold_started_at is None:
        return False
    return (time.time() - state.hold_started_at) >= FORGET_HOLD_MAX_MINUTES * 60


def set_hold_meta(conn: sqlite3.Connection, session_id: str) -> None:
    payload = json.dumps(
        {"session_id": session_id or "", "started_at": _utc_now()},
        separators=(",", ":"),
    )
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (META_FORGET_HOLD, payload),
    )


def clear_hold_meta(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM meta WHERE key = ?", (META_FORGET_HOLD,))


def load_hold_meta(conn: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        "SELECT value FROM meta WHERE key = ?",
        (META_FORGET_HOLD,),
    ).fetchone()
    if not row:
        return None
    try:
        data = json.loads(row[0])
        return data if isinstance(data, dict) else None
    except Exception:
        return None


# --- tool search / handle ---------------------------------------------------------


def _short_label(
    text: str,
    *,
    matched_terms: Optional[Set[str]] = None,
    limit: int = 40,
) -> str:
    """Minimal disambiguator; never logged. Rank: names/digits, then search hits, then others."""
    matched = matched_terms or set()
    ranked: List[Tuple[int, int, int, str]] = []
    for i, (tok, _start, capitalized) in enumerate(_tokenize_with_spans(text or "")):
        if len(tok) < 3 or tok in _STOPWORDS:
            continue
        has_digit = any(ch.isdigit() for ch in tok)
        # P6-FORGET: names (capitalized, any position) + digits first; prefer search hits — P6-D06
        if has_digit or capitalized:
            tier = 0
        elif tok in matched:
            tier = 1
        else:
            tier = 2
        # Within a tier, prefer terms that matched the description (e.g. Nimbus over Talked)
        hit = 0 if tok in matched else 1
        ranked.append((tier, hit, i, tok))
    ranked.sort(key=lambda x: (x[0], x[1], x[2]))
    ordered: List[str] = []
    seen: Set[str] = set()
    for _tier, _hit, _i, tok in ranked:
        if tok in seen:
            continue
        seen.add(tok)
        ordered.append(tok)
        if len(ordered) >= 2:
            break
    if not ordered:
        return "note"
    return ", ".join(ordered)[:limit]


def search_candidates(
    conn: sqlite3.Connection,
    description: str,
) -> List[Dict[str, Any]]:
    """Return candidate dicts for confirm=false (may include notebook_fact).

    P6-FORGET: D3 recall-oriented search (any distinctive term); cascade matcher
    unchanged and unused here — P6-D06.
    """
    terms = derive_search_terms(description or "")
    out: List[Dict[str, Any]] = []

    for r in conn.execute(
        "SELECT id, text, target, learned_at, updated_at FROM facts WHERE state = 'active'"
    ):
        text = r["text"] or ""
        if row_matches_search(text, terms):
            out.append(
                {
                    "id": r["id"],
                    "kind": KIND_NOTEBOOK_FACT,
                    "action": "use memory remove",
                    "date": (r["updated_at"] or r["learned_at"] or "")[:10],
                    "label": _short_label(text, matched_terms=terms),
                    "_text": text,
                }
            )

    for r in conn.execute("SELECT * FROM episodes"):
        blob = _episode_blob(r)
        if row_matches_search(blob, terms):
            out.append(
                {
                    "id": r["id"],
                    "kind": RECORD_KIND_EPISODE,
                    "date": (r["recorded_at"] or r["event_time"] or "")[:10],
                    "label": _short_label(blob, matched_terms=terms),
                    "_text": blob,
                }
            )

    for r in conn.execute("SELECT * FROM pending_turns"):
        blob = _pending_blob(r)
        if row_matches_search(blob, terms):
            out.append(
                {
                    "id": r["id"],
                    "kind": RECORD_KIND_PENDING,
                    "date": (r["created_at"] or "")[:10],
                    "label": _short_label(blob, matched_terms=terms),
                    "_text": blob,
                }
            )
    return out


def group_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group by label (full disambiguator); mark ask_brian when >1 group."""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for c in candidates:
        # P6-FORGET: full label keeps same-name subjects distinguishable (e.g. Mara) — P6-D06
        key = (c.get("label") or "note").strip().lower() or "note"
        groups.setdefault(key, []).append(c)
    ask = len(groups) > 1
    result = []
    for i, (key, items) in enumerate(groups.items(), start=1):
        clean = [
            {
                "id": x["id"],
                "kind": x["kind"],
                **({"action": x["action"]} if "action" in x else {}),
                "date": x.get("date") or "",
                "label": x.get("label") or "note",
            }
            for x in items
        ]
        result.append(
            {
                "subject_key": f"g{i}",
                "ask_brian": ask,
                "candidates": clean,
            }
        )
    return result


def handle_forget_memory(
    provider: Any,
    args: Dict[str, Any],
) -> str:
    """Dispatch forget_memory for a provider instance. Returns JSON string."""
    t0 = time.perf_counter()
    state: ForgetSessionState = provider._forget_state
    conn = provider._conn

    def _done(payload: Dict[str, Any], *, refused: str = "-") -> str:
        memlog.write_event(
            memlog.LOG_EVENT_FORGET_TOOL,
            confirm=bool(args.get("confirm")),
            candidate_count=int(payload.get("_cand_count", 0)),
            group_count=int(payload.get("_group_count", 0)),
            refused_reason=refused,
            ok=bool(payload.get("ok")),
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )
        payload.pop("_cand_count", None)
        payload.pop("_group_count", None)
        return json.dumps(payload, separators=(",", ":"))

    if not is_brian_conversation(provider._platform, provider._parent_session_id):
        return _done(
            {
                "ok": False,
                "refused_reason": "platform",
                "message": "Forget is only available in Brian's interactive conversation.",
            },
            refused="platform",
        )

    if conn is None:
        return _done(
            {"ok": False, "refused_reason": "no_conn", "message": "Memory store is not open."},
            refused="no_conn",
        )

    expire_orphan_hold_on_restart(provider)

    try:
        from . import store as _store
    except ImportError:
        import store as _store

    confirm = bool(args.get("confirm"))
    description = str(args.get("description") or "")

    if not confirm:
        cands = search_candidates(conn, description)
        # P6-FORGET: all listed IDs (incl. notebook_fact) for hold-end; confirm=true refuses notebook — P6-D06
        state.candidate_ids = {c["id"] for c in cands}
        state.candidate_meta = {c["id"]: c for c in cands}
        groups = group_candidates(cands)
        if cands:
            state.hold_started_at = time.time()
            state.hold_turn_count = 0
            mark_drop(state, provider._current_user_message or "")
            if provider._current_user_message:
                key = normalize_disposition_key(provider._current_user_message)
                if key not in state.hold_user_texts:
                    state.hold_user_texts.append(key)
            with _store.locked(conn):
                try:
                    conn.execute("BEGIN IMMEDIATE")
                    set_hold_meta(conn, provider._session_id or "")
                    conn.execute("COMMIT")
                except Exception:
                    try:
                        conn.execute("ROLLBACK")
                    except Exception:
                        pass
            memlog.write_event(
                memlog.LOG_EVENT_FORGET_HOLD,
                action="set",
                held_count=len(state.hold_user_texts),
                ok=True,
            )
        ask_brian = bool(groups) and any(g.get("ask_brian") for g in groups)
        if ask_brian:
            state.ask_brian_pending = True
            msg = MSG_ASK_BRIAN_MULTI
        elif cands:
            state.ask_brian_pending = False
            msg = "One match. Ask Brian to confirm before erasing."
        else:
            state.ask_brian_pending = False
            msg = "No matches."
        # P6-EPISODES: sanitize on every confirm=false (incl. no matches) — Phase 7-WAL
        try:
            _store.sanitize_after_erase(conn)
        except Exception:
            pass
        # Strip private _text before return
        for g in groups:
            for c in g["candidates"]:
                c.pop("_text", None)
        return _done(
            {
                "ok": True,
                "confirm": False,
                "groups": groups,
                "message": msg,
                "_cand_count": len(cands),
                "_group_count": len(groups),
            }
        )

    # confirm=true
    target_ids = [str(x) for x in (args.get("target_ids") or [])]
    authority = has_forget_intent(provider._current_user_message or "") or hold_active(state)
    if not authority or not is_brian_conversation(provider._platform, provider._parent_session_id):
        return _done(
            {
                "ok": False,
                "refused_reason": "authority",
                "message": "Confirm erase only after Brian asks to forget or while clarifying which item.",
            },
            refused="authority",
        )
    if not target_ids or any(tid not in state.candidate_ids for tid in target_ids):
        return _done(
            {
                "ok": False,
                "refused_reason": "unbound_targets",
                "message": "target_ids must come from the latest confirm=false candidate list.",
            },
            refused="unbound_targets",
        )

    targets: List[Dict[str, str]] = []
    for tid in target_ids:
        meta = state.candidate_meta.get(tid) or {}
        kind = meta.get("kind") or RECORD_KIND_EPISODE
        # P6-FORGET: E6/C3 — notebook facts listed for guidance but never erasable via tool — P6-D06
        if kind == KIND_NOTEBOOK_FACT:
            return _done(
                {
                    "ok": False,
                    "refused_reason": "active_fact",
                    "message": (
                        "That ID is a current notebook fact. Use the memory tool remove on "
                        "USER.md/MEMORY.md; the cascade runs from that notification."
                    ),
                },
                refused="active_fact",
            )
        targets.append({"id": tid, "kind": kind})

    ok, counts = forget_cascade(
        conn,
        targets,
        reason=ERASE_REASON_TOOL,
        terms_source=description,
    )
    state.forget_in_session = True
    mark_drop(state, provider._current_user_message or "")
    for ht in state.hold_user_texts:
        state.disposition_drops[ht] = time.time() + DISPOSITION_ENTRY_TTL_MINUTES * 60
    held_n = len(state.hold_user_texts)
    state.clear_hold_process()
    with _store.locked(conn):
        try:
            conn.execute("BEGIN IMMEDIATE")
            clear_hold_meta(conn)
            conn.execute("COMMIT")
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
    memlog.write_event(
        memlog.LOG_EVENT_FORGET_HOLD,
        action="executed",
        held_count=held_n,
        ok=ok,
    )
    erased = [{"id": t["id"], "kind": t["kind"]} for t in targets]
    return _done(
        {
            "ok": ok,
            "confirm": True,
            "erased": erased,
            "counts": counts,
            "message": (
                "Erased from provider memory. Tell Brian plainly it is gone from your memory; "
                "conversation logs still have it."
            ),
            "_cand_count": len(erased),
            "_group_count": 0,
        }
    )


def end_hold_if_candidate_removed(
    provider: Any,
    fact_id: str,
) -> None:
    """E3: memory-tool remove of a candidate-set fact ends the hold."""
    state: ForgetSessionState = provider._forget_state
    # P6-EPISODES: never clear hold/ask via memory remove while ask_brian pending — P6-D04
    if state.ask_brian_pending:
        return
    if fact_id not in state.candidate_ids:
        return
    held_n = len(state.hold_user_texts)
    state.clear_hold_process()
    conn = provider._conn
    if conn is not None:
        try:
            from . import store as _store
        except ImportError:
            import store as _store

        with _store.locked(conn):
            try:
                conn.execute("BEGIN IMMEDIATE")
                clear_hold_meta(conn)
                conn.execute("COMMIT")
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except Exception:
                    pass
    memlog.write_event(
        memlog.LOG_EVENT_FORGET_HOLD,
        action="executed",
        held_count=held_n,
        ok=True,
    )


def expire_orphan_hold_on_restart(provider: Any) -> None:
    """E3: meta hold with empty process candidate set after restart → expired."""
    state: ForgetSessionState = provider._forget_state
    conn = provider._conn
    if conn is None:
        return
    try:
        from . import store as _store
    except ImportError:
        import store as _store

    with _store.locked(conn):
        meta = load_hold_meta(conn)
        if meta and not hold_active(state) and not state.candidate_ids:
            try:
                conn.execute("BEGIN IMMEDIATE")
                clear_hold_meta(conn)
                conn.execute("COMMIT")
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except Exception:
                    pass
            memlog.write_event(
                memlog.LOG_EVENT_FORGET_HOLD,
                action="expired",
                held_count=0,
                ok=True,
            )


def on_turn_start_forget_hooks(provider: Any, message: str) -> None:
    """E2/E3: mark forget-intent drops; maintain hold turn budget; expiry checks."""
    state: ForgetSessionState = provider._forget_state
    expire_disposition_drops(state)
    expire_orphan_hold_on_restart(provider)

    # P6-EPISODES: next Brian turn ends ask_brian_pending (turn boundary; no content parse) — P6-D04
    if state.ask_brian_pending:
        state.ask_brian_pending = False

    if has_forget_intent(message or ""):
        mark_drop(state, message or "")

    if hold_active(state):
        if hold_expired_wall(state):
            _expire_hold(provider, reason="ttl")
        elif state.hold_turn_count >= HOLD_MAX_TURNS:
            # P6-FORGET: E3 — 4th user turn after hold is keep; prior marks stay — P6-D06
            _expire_hold(provider, reason="max_turns")
        else:
            state.hold_turn_count += 1
            key = normalize_disposition_key(message or "")
            if key not in state.hold_user_texts:
                state.hold_user_texts.append(key)
            mark_drop(state, message or "")


def _expire_hold(provider: Any, *, reason: str) -> None:
    state: ForgetSessionState = provider._forget_state
    held_n = len(state.hold_user_texts)
    # Marks stay; only clear hold process + meta (+ ask_brian_pending)
    state.clear_hold_process()
    conn = provider._conn
    if conn is not None:
        try:
            from . import store as _store
        except ImportError:
            import store as _store

        with _store.locked(conn):
            try:
                conn.execute("BEGIN IMMEDIATE")
                clear_hold_meta(conn)
                conn.execute("COMMIT")
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except Exception:
                    pass
    memlog.write_event(
        memlog.LOG_EVENT_FORGET_HOLD,
        action="expired",
        held_count=held_n,
        ok=True,
    )


def on_session_switch_forget_hooks(provider: Any) -> None:
    """E3: hold ends on switch; E1: disposition drops are NOT cleared."""
    if hold_active(provider._forget_state) or load_hold_meta_safe(provider):
        _expire_hold(provider, reason="switch")


def _memory_args_are_remove_or_replace(args: Any) -> bool:
    if not isinstance(args, dict):
        return False
    action = str(args.get("action") or "").strip().lower()
    if action in ("remove", "replace"):
        return True
    ops = args.get("operations")
    if isinstance(ops, list):
        for op in ops:
            if not isinstance(op, dict):
                continue
            if str(op.get("action") or "").strip().lower() in ("remove", "replace"):
                return True
    return False


def pre_tool_call_hook(
    tool_name: str = "",
    args: Any = None,
    **kwargs: Any,
) -> Optional[Dict[str, str]]:
    """G2: while ask_brian_pending, block memory remove/replace and forget_memory confirm=true.

    Resolves provider via session registry only (``session_id`` kwarg from
    ``tool_hook_ids`` / ``inline_tool_executors.py`` L18–26). Never reads module ``_provider``.
    """
    try:
        from . import registry as _registry
    except ImportError:
        import registry as _registry

    sid = str(kwargs.get("session_id") or "")
    provider = _registry.get(sid)
    if provider is None:
        return None
    if not is_brian_conversation(
        getattr(provider, "_platform", "") or "",
        getattr(provider, "_parent_session_id", "") or "",
    ):
        return None

    state: ForgetSessionState = provider._forget_state
    name = str(tool_name or "")

    if name == MEMORY_TOOL_NAME:
        if not _memory_args_are_remove_or_replace(args):
            return None
        if state.ask_brian_pending:
            memlog.write_event(
                memlog.LOG_EVENT_FORGET_GUARD,
                action="blocked",
                tool=MEMORY_TOOL_NAME,
                ok=False,
            )
            return {"action": "block", "message": MSG_ASK_BRIAN_MEMORY_BLOCK}
        memlog.write_event(
            memlog.LOG_EVENT_FORGET_GUARD,
            action="allowed",
            tool=MEMORY_TOOL_NAME,
            ok=True,
        )
        return None

    if name == TOOL_NAME:
        if not isinstance(args, dict) or not bool(args.get("confirm")):
            return None
        if state.ask_brian_pending:
            memlog.write_event(
                memlog.LOG_EVENT_FORGET_GUARD,
                action="blocked",
                tool=TOOL_NAME,
                ok=False,
            )
            return {"action": "block", "message": MSG_ASK_BRIAN_MULTI}
        memlog.write_event(
            memlog.LOG_EVENT_FORGET_GUARD,
            action="allowed",
            tool=TOOL_NAME,
            ok=True,
        )
        return None

    return None


def load_hold_meta_safe(provider: Any) -> bool:
    conn = provider._conn
    if conn is None:
        return False
    try:
        return load_hold_meta(conn) is not None
    except Exception:
        return False
