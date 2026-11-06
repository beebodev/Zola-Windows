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


# P10-READ: RCS sender forms. Only a plain tel:+E.164 or sip:+E.164@host is read.
# Anything else, including a business-agent sip URI, is unparsed with no canonical.
_TEL_BODY = re.compile(r"^\+[0-9][0-9().\-]*$")
_SIP_USER = re.compile(r"^\+[0-9]+$")
_SIP_HOST = re.compile(r"^[0-9A-Za-z]([0-9A-Za-z.\-]*[0-9A-Za-z])?(:[0-9]{1,5})?$")


def _rcs_e164(number: str) -> str:
    """Canonical E.164 for a leading-plus number, else empty."""
    kind, canonical = normalize(number)
    return canonical if kind == KIND_E164 and number.startswith("+") else ""


def extract_rcs_sender(raw: str) -> tuple:
    """Return (kind, canonical) for an RCS sender. normalize() is not touched."""
    text = str(raw or "").strip()
    scheme, sep, rest = text.partition(":")
    scheme = scheme.casefold()
    if not sep or not rest:
        return KIND_UNPARSED, ""
    if scheme == "tel":
        # P10-READ: no tel parameters, no local numbers; a plus is required
        if _TEL_BODY.fullmatch(rest):
            canonical = _rcs_e164(rest)
            if canonical:
                return KIND_E164, canonical
        return KIND_UNPARSED, ""
    if scheme in ("sip", "sips"):
        user, at, host = rest.partition("@")
        # user part must be only +digits; ;user=phone style params live on the host side
        host = host.partition(";")[0]
        if at and _SIP_USER.fullmatch(user) and _SIP_HOST.fullmatch(host):
            canonical = _rcs_e164(user)
            if canonical:
                return KIND_E164, canonical
    return KIND_UNPARSED, ""


_GROUP_GAP = re.compile(r"[\s().\-]+")


def spoken_number(text: str) -> tuple:
    """Return (kind, canonical) for the number spoken in text.

    A 3-3-4 group with spaces or dashes, a bare 10-digit run, and a +1 form
    all go through normalize. The watch path and the number-forget path both
    call this. Only an e164 result is returned; anything else is unparsed.
    """
    raw = str(text or "")
    kind, canonical = normalize(raw)
    if kind == KIND_E164:
        return kind, canonical
    groups = list(re.finditer(r"\d+", raw))
    for start, group in enumerate(groups):
        end = group.end()
        piece_start = group.start() - 1 if group.start() and raw[group.start() - 1] == "+" else group.start()
        kind, canonical = normalize(raw[piece_start:end])
        if kind == KIND_E164:
            return kind, canonical
        digits = group.group()
        for nxt in groups[start + 1 :]:
            gap = raw[end : nxt.start()]
            if not gap or _GROUP_GAP.fullmatch(gap) is None:
                break
            digits += nxt.group()
            end = nxt.end()
            if len(digits) > E164_INTL_MAX_DIGITS:
                break
            kind, canonical = normalize(raw[piece_start:end])
            if kind == KIND_E164:
                return kind, canonical
    return KIND_UNPARSED, ""


def matchable(kind: str) -> bool:
    return kind in MATCHABLE_KINDS


def hash(canonical: str) -> str:
    # P10-STORE: one hash helper, byte-identical with the watcher — P10-D10
    return address_hash.address_hash(canonical)
