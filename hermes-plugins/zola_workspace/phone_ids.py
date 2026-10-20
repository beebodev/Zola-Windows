"""US phone-sender normalizer. Standard library plus the shared hash helper."""

from __future__ import annotations

import re

# P10-STORE: package load uses a relative import; flat tests use the fallback — P10-D10
try:
    from . import address_hash
except ImportError:
    import address_hash

# P10-STORE: US rules only; Google canonicalForm covers contacts — P10-D10
US_COUNTRY_CODE = "1"
E164_LOCAL_DIGITS = 10
E164_NANP_DIGITS = 11
E164_INTL_MIN_DIGITS = 8
E164_INTL_MAX_DIGITS = 15
SHORTCODE_MIN_DIGITS = 3
SHORTCODE_MAX_DIGITS = 6
ALNUM_MIN_LENGTH = 1
ALNUM_MAX_LENGTH = 11
KIND_E164 = "e164"
KIND_SHORTCODE = "shortcode"
KIND_ALNUM = "alnum"
KIND_UNPARSED = "unparsed"
MATCHABLE_KINDS = frozenset({KIND_E164})

_SPACE = re.compile(r"\s+")
_ALNUM = re.compile(r"^[0-9A-Za-z]+$")


def _strip_spaces(raw: str) -> str:
    return _SPACE.sub("", str(raw or ""))


def _ascii_digits(text: str) -> bool:
    return bool(text) and all("0" <= char <= "9" for char in text)


def _digits_of(spaced: str) -> str:
    """Drop ASCII punctuation other than a leading +."""
    if not spaced:
        return ""
    lead = ""
    rest = spaced
    if rest.startswith("+"):
        lead = "+"
        rest = rest[1:]
    kept = []
    # P10-STORE: a non-ASCII digit is not the digit path — P10-D10
    for char in rest:
        if "0" <= char <= "9":
            kept.append(char)
        elif char.isalpha() or char.isdigit() or char == "+":
            return ""
    return lead + "".join(kept)


def normalize(raw: str) -> tuple:
    """Return (kind, canonical). Only e164 is matchable."""
    spaced = _strip_spaces(str(raw or ""))
    digits = _digits_of(spaced)
    if digits and digits.startswith("+"):
        body = digits[1:]
        if _ascii_digits(body) and E164_INTL_MIN_DIGITS <= len(body) <= E164_INTL_MAX_DIGITS:
            return KIND_E164, digits
    elif _ascii_digits(digits):
        if len(digits) == E164_LOCAL_DIGITS:
            return KIND_E164, "+" + US_COUNTRY_CODE + digits
        if len(digits) == E164_NANP_DIGITS and digits.startswith(US_COUNTRY_CODE):
            return KIND_E164, "+" + digits
        if SHORTCODE_MIN_DIGITS <= len(digits) <= SHORTCODE_MAX_DIGITS:
            return KIND_SHORTCODE, digits
    if (
        ALNUM_MIN_LENGTH <= len(spaced) <= ALNUM_MAX_LENGTH
        and _ALNUM.fullmatch(spaced)
        and any(char.isalpha() for char in spaced)
    ):
        return KIND_ALNUM, spaced.casefold()
    return KIND_UNPARSED, spaced.casefold()


def matchable(kind: str) -> bool:
    return kind in MATCHABLE_KINDS


def hash(canonical: str) -> str:
    # P10-STORE: one hash helper, byte-identical with the watcher — P10-D10
    return address_hash.address_hash(canonical)
