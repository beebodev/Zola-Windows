"""Visible text from HTML and the shared body cap (P8-D08)."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import List, Tuple

# P8-READ: body cap and trim rules — P8-D08
BODY_CHAR_CAP = 4000

_SKIP_TAGS = frozenset({"script", "style", "head"})
_QUOTE_CLASSES = frozenset({"gmail_quote", "gmail_quote_container"})
_BLOCK_TAGS = frozenset({"p", "div", "tr", "li", "h1", "h2", "h3", "h4", "blockquote"})
# P8-READ: void elements are never stacked; a later end tag must not pop them — P8-D08
_VOID_TAGS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)

_ON_WROTE_RE = re.compile(r"^On .+ wrote:\s*$")
_PROP_RE_TMPL = r"{prop}\s*:\s*([^;]+)"


def _zeroish(raw: str) -> bool:
    text = raw.strip().casefold()
    text = re.sub(r"(px|pt|em|rem|%)$", "", text).strip()
    try:
        return float(text) == 0.0
    except ValueError:
        return False


def style_hides(style: str) -> bool:
    """True for the supported inline-hidden cases. External CSS is not applied."""
    # P8-READ: inline hidden only; a class from an external sheet stays — P8-D08
    if not style:
        return False
    folded = style.casefold()
    display = re.search(_PROP_RE_TMPL.format(prop="display"), folded)
    if display and display.group(1).strip() == "none":
        return True
    visibility = re.search(_PROP_RE_TMPL.format(prop="visibility"), folded)
    if visibility and visibility.group(1).strip() == "hidden":
        return True
    font = re.search(_PROP_RE_TMPL.format(prop="font-size"), folded)
    if font and _zeroish(font.group(1)):
        return True
    opacity = re.search(_PROP_RE_TMPL.format(prop="opacity"), folded)
    if opacity and _zeroish(opacity.group(1)):
        return True
    return False


def _attrs(attrs) -> dict:
    out = {}
    for key, value in attrs or []:
        out[str(key).casefold()] = "" if value is None else str(value)
    return out


def _class_tokens(raw: str) -> set:
    return {part for part in raw.split() if part}


# P8-READ: these close when another of the same kind opens — P8-D08
_OPTIONAL_END = frozenset({"li", "p", "td", "th", "tr", "option", "dt", "dd"})


class _VisibleHTML(HTMLParser):
    """One stack of every open element. Hidden and skipped nodes sit on it too."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: List[str] = []
        self._open: List[Tuple[str, bool]] = []

    def _suppressed(self) -> bool:
        return any(flag for _, flag in self._open)

    def _close_through(self, name: str) -> bool:
        """Pop through name, which also closes anything open inside it."""
        if not any(open_name == name for open_name, _flag in self._open):
            return False
        while self._open:
            open_name, _flag = self._open.pop()
            if open_name == name:
                return True
        return True

    def _suppresses(self, name: str, attrs) -> bool:
        ad = _attrs(attrs)
        if name in _SKIP_TAGS:
            return True
        if _QUOTE_CLASSES.intersection(_class_tokens(ad.get("class", ""))):
            return True
        if "hidden" in ad or style_hides(ad.get("style", "")):
            return True
        return False

    def handle_starttag(self, tag: str, attrs) -> None:
        name = tag.casefold()
        if name in _VOID_TAGS:
            if name == "br" and not self._suppressed():
                self._parts.append("\n")
            return
        if name in _OPTIONAL_END:
            self._close_through(name)
        suppressed = self._suppresses(name, attrs)
        if name in _BLOCK_TAGS and not suppressed and not self._suppressed():
            self._parts.append("\n")
        self._open.append((name, suppressed))

    def handle_endtag(self, tag: str) -> None:
        name = tag.casefold()
        if name in _VOID_TAGS:
            return
        if not self._close_through(name):
            return
        if name in _BLOCK_TAGS and not self._suppressed():
            self._parts.append("\n")

    def handle_startendtag(self, tag: str, attrs) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if self._suppressed():
            return
        self._parts.append(data)

    def handle_comment(self, data: str) -> None:
        return

    def text(self) -> str:
        raw = "".join(self._parts)
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in raw.splitlines()]
        return "\n".join(line for line in lines if line).strip()


def html_to_visible_text(html: str) -> str:
    """Drop supported hidden HTML. An external-stylesheet class is left in the text."""
    parser = _VisibleHTML()
    try:
        parser.feed(html or "")
        parser.close()
    except Exception:
        return ""
    return parser.text()


def trim_quotes(text: str) -> str:
    """Drop quoted lines, an On-wrote line, and a signature after a `-- ` line."""
    # P8-READ: trim before the cap — P8-D08
    kept: List[str] = []
    for line in (text or "").splitlines():
        if line.startswith(">"):
            continue
        if _ON_WROTE_RE.match(line):
            continue
        if line == "-- ":
            break
        kept.append(line)
    return "\n".join(kept).strip()


def cap_text(text: str, limit: int = BODY_CHAR_CAP) -> Tuple[str, bool, int]:
    """Return (excerpt, truncated, total_chars) after trim has already run."""
    body = text or ""
    total = len(body)
    if total <= limit:
        return body, False, total
    return body[:limit], True, total


def prepare_body(text: str, *, html: bool) -> Tuple[str, bool, int]:
    visible = html_to_visible_text(text) if html else (text or "")
    return cap_text(trim_quotes(visible))
