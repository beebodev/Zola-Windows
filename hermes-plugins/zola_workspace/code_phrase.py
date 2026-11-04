"""Phrase check for the code reader (P10-READ, verdict 2).

Brian's own message for this turn must ask for the code. The model's wish to read it is not
enough, and neither is text that arrives inside a message body or a tool result. The check is
pure: it reads the message string and nothing else, and it fails closed.

A message authorizes a read only when all of these hold:
  * an approved phrase appears outside quotes;
  * the words just before it are not a negation, reported speech, or a question about codes
    (so "don't", "he said", "did you", "if you" refuse, while "I got a text. read me the code"
    still authorizes);
  * the words after it do not turn the phrase into a question about the code ("what was that
    code for?") and do not cancel it ("never mind").
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

try:
    from . import send_gate
except ImportError:  # flat unittest discover
    import send_gate  # type: ignore

# P10-READ: whole-token phrases, apostrophes dropped by send_gate.normalize_tokens
PHRASES: Tuple[Tuple[str, ...], ...] = (
    ("read", "me", "the", "code"),
    ("whats", "the", "code"),
    ("what", "was", "that", "code"),
    ("read", "the", "code"),
    ("speak", "the", "code"),
    ("show", "me", "the", "code"),
)

# P10-READ: look this far before the phrase for blockers. Longer context ("I got a text") is fine.
BLOCKER_WINDOW = 4

# P10-READ: decision 2 negatives — negation / reported speech / non-request about the act of reading
NEGATION = frozenset({"dont", "never", "not", "no"})
REPORTED = frozenset({"said", "asked", "told", "wrote", "says", "asking"})
QUESTION_LEAD = frozenset({"did", "does", "do", "should", "if", "whether", "why", "how", "when"})
# "no need to read…" — "need" right after "no" in the window
NEGATION_FOLLOW = frozenset({"need", "reason", "point"})

# P10-READ: after the phrase, these cancel it. "dont" and "never" are included so a same-turn
# retraction wins over the request.
CANCEL_TOKENS = frozenset(
    {"nevermind", "cancel", "stop", "forget", "wait", "dont", "never", "scratch", "ignore", "nope"}
)
CANCEL_BIGRAMS = frozenset(
    {("never", "mind"), ("hold", "on"), ("not", "now"), ("no", "dont"), ("no", "wait"), ("on", "second")}
)
# P10-READ: "what was that code for" asks about the code. It does not ask to hear it.
NOT_REQUEST_NEXT = frozenset({"for", "about", "supposed", "used", "meant"})

NEWEST_WORDS = frozenset({"latest", "newest", "recent", "newer", "last"})
OLDEST_WORDS = frozenset({"older", "oldest", "previous", "earlier", "first"})

_DOUBLE_QUOTED = re.compile(r'"[^"]*"|\u201c[^\u201d]*\u201d|\u00ab[^\u00bb]*\u00bb|`[^`]*`')
_SINGLE_QUOTED = re.compile(r"(?<![A-Za-z0-9])'[^']*'(?![A-Za-z0-9])|\u2018[^\u2019]*\u2019")
_QUOTE_LINE = re.compile(r"^\s*>.*$", re.MULTILINE)

REASON_OK = "ok"
REASON_NO_MESSAGE = "no_message"
REASON_NO_PHRASE = "no_phrase"
REASON_NOT_REQUEST = "not_request"
REASON_CANCELLED = "cancelled"
REASON_INTERRUPTED = "interrupted"


def _strip_quotes(text: str) -> str:
    out = _QUOTE_LINE.sub(" ", text or "")
    out = _DOUBLE_QUOTED.sub(" ", out)
    out = _SINGLE_QUOTED.sub(" ", out)
    return out


def _occurrences(tokens: Tuple[str, ...]):
    for phrase in PHRASES:
        width = len(phrase)
        for index in range(0, len(tokens) - width + 1):
            if tokens[index : index + width] == phrase:
                yield index, width


def _cancelled_after(rest: Tuple[str, ...]) -> bool:
    if any(token in CANCEL_TOKENS for token in rest):
        return True
    return any(pair in CANCEL_BIGRAMS for pair in zip(rest, rest[1:]))


def _blocked_before(before: Tuple[str, ...]) -> bool:
    # P10-READ: decision 2 — refuse negation / reported speech / "did you…" questions near the phrase
    for position, token in enumerate(before):
        if token in NEGATION:
            nxt = before[position + 1] if position + 1 < len(before) else ""
            if token == "no" and nxt and nxt not in NEGATION_FOLLOW:
                continue
            return True
        if token in REPORTED or token in QUESTION_LEAD:
            return True
    return False


def check(message: Optional[str]) -> Tuple[bool, str, Tuple[str, ...]]:
    """(authorized, reason, words_after_phrase). The words are for the recency check only."""
    text = message if isinstance(message, str) else ""
    if not text.strip():
        return False, REASON_NO_MESSAGE, ()
    if send_gate.INTERRUPTED_MARK in text.casefold():
        return False, REASON_INTERRUPTED, ()
    raw_tokens = send_gate.normalize_tokens(_strip_quotes(text))
    # "read me the newest code": the recency word sits inside the phrase, so lift it out and hand
    # it to the recency check with the words after
    inline = tuple(
        word
        for position, word in enumerate(raw_tokens[:-1])
        if word in (NEWEST_WORDS | OLDEST_WORDS) and raw_tokens[position + 1] == "code"
    )
    tokens = tuple(
        word
        for position, word in enumerate(raw_tokens)
        if not (
            position + 1 < len(raw_tokens)
            and word in (NEWEST_WORDS | OLDEST_WORDS)
            and raw_tokens[position + 1] == "code"
        )
    )
    seen_phrase = False
    saw_cancel = False
    for index, width in sorted(_occurrences(tokens)):
        seen_phrase = True
        before = tokens[max(0, index - BLOCKER_WINDOW) : index]
        if _blocked_before(before):
            continue
        rest = tokens[index + width :]
        if rest and rest[0] in NOT_REQUEST_NEXT:
            continue
        if _cancelled_after(rest):
            saw_cancel = True
            continue
        return True, REASON_OK, rest + inline
    if saw_cancel:
        return False, REASON_CANCELLED, ()
    return False, (REASON_NOT_REQUEST if seen_phrase else REASON_NO_PHRASE), ()


def authorizes(message: Optional[str]) -> bool:
    return check(message)[0]


# P10-READ F7: "show me the code" means display, not speak — even in Voice mode
SHOW_PHRASE: Tuple[str, ...] = ("show", "me", "the", "code")


def prefers_show(message: Optional[str]) -> bool:
    """True when Brian's authorizing phrase was the show form (Claude lean: show means show)."""
    if not authorizes(message):
        return False
    text = message if isinstance(message, str) else ""
    raw_tokens = send_gate.normalize_tokens(_strip_quotes(text))
    tokens = tuple(
        word
        for position, word in enumerate(raw_tokens)
        if not (
            position + 1 < len(raw_tokens)
            and word in (NEWEST_WORDS | OLDEST_WORDS)
            and raw_tokens[position + 1] == "code"
        )
    )
    width = len(SHOW_PHRASE)
    for index in range(0, len(tokens) - width + 1):
        if tokens[index : index + width] != SHOW_PHRASE:
            continue
        before = tokens[max(0, index - BLOCKER_WINDOW) : index]
        if _blocked_before(before):
            continue
        rest = tokens[index + width :]
        if rest and rest[0] in NOT_REQUEST_NEXT:
            continue
        if _cancelled_after(rest):
            continue
        return True
    return False


def recency_choice(words_after: Tuple[str, ...]) -> str:
    """"newest", "oldest", or "" from the words after the phrase.

    Callers must treat "oldest" as a retarget only when exactly two codes are pending;
    "newest" is fine at any count (verdict 2 / Phase 5 G2).
    """
    newest = any(word in NEWEST_WORDS for word in words_after)
    oldest = any(word in OLDEST_WORDS for word in words_after)
    if newest and not oldest:
        return "newest"
    if oldest and not newest:
        return "oldest"
    return ""
