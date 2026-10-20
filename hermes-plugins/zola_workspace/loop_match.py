"""Pure watch predicate matcher. Standard library only (P10-D12)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _instant(value: str) -> Optional[datetime]:
    text = str(value or "").strip()
    if not text:
        return None
    if text.isdigit():
        try:
            return datetime.fromtimestamp(int(text) / 1000.0, timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _occurred_at(item: Dict[str, Any]) -> Optional[datetime]:
    if str(item.get("source") or "") == "calendar" or item.get("event_id"):
        return _instant(str(item.get("event_updated") or ""))
    return _instant(str(item.get("internal_date") or ""))


def _node_matches(node: Dict[str, Any], item: Dict[str, Any]) -> bool:
    op = node.get("op")
    if op == "all":
        return all(_node_matches(child, item) for child in node.get("args") or [])
    if op == "any":
        return any(_node_matches(child, item) for child in node.get("args") or [])
    if op == "gmail_thread":
        return str(item.get("thread_id") or "") == str(node.get("thread_id") or "")
    if op == "gmail_message":
        return str(item.get("message_id") or "") == str(node.get("message_id") or "")
    if op == "sender_is":
        return str(item.get("sender_address_hash") or "") == str(node.get("address_hash") or "")
    if op == "not_source":
        message_id = str(item.get("message_id") or "")
        banned = {str(value) for value in (node.get("message_ids") or []) if str(value)}
        if not message_id or not banned:
            return False
        return message_id not in banned
    if op == "after":
        # P9-SPEAK: message time or event updated, not the watcher insert time — P9-D09
        occurred = _occurred_at(item)
        threshold = _instant(str(node.get("at") or ""))
        if occurred is None or threshold is None:
            return False
        return occurred >= threshold
    if op == "calendar_event":
        return str(item.get("event_id") or "") == str(node.get("event_id") or "")
    if op == "calendar_cancelled":
        return str(item.get("calendar_status") or "").casefold() == "cancelled"
    if op == "calendar_status_differs":
        current = str(item.get("calendar_status") or "")
        return bool(current) and current != str(node.get("from_status") or "")
    if op == "brian_confirms":
        return False
    return False


# P10-INTAKE: moved out of loops.py so zola-phone does not import the Google stack — P10-D12
def evaluate(predicate: Dict[str, Any], item: Dict[str, Any]) -> bool:
    """Pure. True means matched. The caller does not close the loop."""
    return _node_matches(predicate, item)
