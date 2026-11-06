"""Loop predicate compile and evaluate, and the zola_loops tool (P9-D09)."""

from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List, Optional

try:
    from . import loop_match
    from . import proactive_store
    from . import read_common
    from . import recorded_results
    from . import taint
    from . import turn_context
    from . import log as wslog
except ImportError:
    import loop_match
    import proactive_store
    import read_common
    import recorded_results
    import taint
    import turn_context
    import log as wslog

# P10-INTAKE: one matcher object for the watcher, the tool, and zola-phone — P10-D12
evaluate = loop_match.evaluate

# P9-STORE: the model does not supply ids; these are the only actions — P9-D09
TOOL_NAME = "zola_loops"
TOOLSET_NAME = "zola_workspace"

# P9-STORE: list is the only source for what she is watching; memory is not — P9-D09
_DESCRIPTION = (
    "What Brian asked you to watch for: list, add, or close. "
    "Not for the mail watcher's health; use workspace_status for that. "
    "When Brian says what are you watching for, what are you keeping an eye on, "
    "what am I waiting on, any open loops, or what did I ask you to watch, call list. "
    "The list result is the only source of what you are watching. "
    "Never answer that question from memory or from the conversation. "
    "If the tool fails, say you could not check. "
    "Pass a handle from a tool result in this conversation. "
    "If Brian's words do not single out one result, ask him which one before you call create. "
    "If several results are live and you pass a handle, the reply names the sender and subject "
    "of that one result. Say those back to Brian before you treat the loop as settled. "
    "Do not pass a message id, thread id, event id, or email address. "
    "A yes or a no after you asked him to confirm a name is another call to this tool. "
    "On a turn where he asks you to watch, you may close an older watch for that same person "
    "only after the new watch exists, and only when the new one covers every channel and the "
    "lifetime of the older one. Say the tool's sentence for that widen. If the close is refused, "
    "the older watch stays. "
    "When your reply is to a request he just made, you may repeat a number he said in that request. "
    "A line you speak on your own, when a text or email arrives, never says the digits."
)

_FORBIDDEN_KEYS = frozenset(
    {
        "message_id",
        "thread_id",
        "event_id",
        "address",
        "from",
        "email",
        "sender",
        "subject",
    }
)
_ALLOWED_KEYS = frozenset(
    {"action", "handle", "intent", "loop_id", "person", "number", "channel"}
)
_INTENTS = frozenset(
    {"reply", "cancelled", "status_change", "confirm_close", "person", "number"}
)
_SENT_LABELS = frozenset({"SENT", "DRAFT"})

_listed: Dict[str, set] = {}
_session_people: Dict[str, Dict[str, Dict[str, str]]] = {}
_confirms: Dict[str, Dict[str, Any]] = {}
_created_on_turn: Dict[str, List[str]] = {}
_confirm_clock = time.monotonic
# P10-WATCH: a yes covers the whole proposed action — verdict 2
CONFIRM_TTL_SECONDS = 120


def set_confirm_clock_for_tests(fn) -> None:
    global _confirm_clock
    _confirm_clock = fn or time.monotonic


def note_session_person(session_id: str, handle: str, name: str, loop_id: str = "") -> None:
    # P10-WATCH: a pronoun resolves only through records this session wrote — verdict 10
    if not session_id or not handle:
        return
    bucket = _session_people.setdefault(session_id, {})
    current = dict(bucket.get(handle) or {})
    if name:
        current["name"] = name
    if loop_id:
        current["loop_id"] = loop_id
    current["handle"] = handle
    bucket[handle] = current


def reset_for_tests() -> None:
    _listed.clear()
    _session_people.clear()
    _confirms.clear()
    _created_on_turn.clear()
    global _confirm_clock
    _confirm_clock = time.monotonic


def _schema() -> Dict[str, Any]:
    return {
        "name": TOOL_NAME,
        "description": _DESCRIPTION,
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["create", "list", "close"]},
                "handle": {"type": "string"},
                "intent": {
                    "type": "string",
                    "enum": [
                        "reply",
                        "cancelled",
                        "status_change",
                        "confirm_close",
                        "person",
                        "number",
                    ],
                },
                "loop_id": {"type": "string"},
                "person": {"type": "string"},
                "number": {"type": "string"},
                "channel": {"type": "string", "enum": ["text", "email", "both"]},
            },
            "required": ["action"],
            "additionalProperties": False,
        },
    }


def loops_schema() -> Dict[str, Any]:
    return _schema()


def _refuse(reason: str, **extra: Any) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"ok": False, "refused_reason": reason}
    payload.update(extra)
    return payload


def _kind_for(intent: str) -> str:
    if intent == "reply":
        return recorded_results.KIND_GMAIL
    if intent in ("cancelled", "status_change"):
        return recorded_results.KIND_CALENDAR
    return ""


def compile_predicate(intent: str, record: Optional[Dict[str, Any]], *, created_at: str) -> Dict[str, Any]:
    """Pure. Returns {ok, predicate} or a refusal. Does not write a loop."""
    if intent == "confirm_close":
        return {"ok": True, "predicate": {"op": "brian_confirms"}}
    if record is None:
        return _refuse("unknown_handle")
    if intent == "reply":
        labels = {str(item).upper() for item in (record.get("labels") or [])}
        hashes = list(record.get("address_hashes") or [])
        thread_id = str(record.get("thread_id") or "")
        message_id = str(record.get("message_id") or "")
        if labels & _SENT_LABELS:
            # P9-STORE: a message he sent does not name the other party — P9-D09
            return _refuse("sent_only")
        if not thread_id or not hashes or not message_id:
            return _refuse("not_compilable")
        return {
            "ok": True,
            "predicate": {
                "op": "all",
                "args": [
                    {"op": "gmail_thread", "thread_id": thread_id},
                    {"op": "sender_is", "address_hash": hashes[0]},
                    # P9-SPEAK: the message the loop was compiled from is not a reply — P9-D09
                    {"op": "not_source", "message_ids": [message_id]},
                    {"op": "after", "at": created_at},
                ],
            },
        }
    if intent == "cancelled":
        event_id = str(record.get("event_id") or "")
        if not event_id:
            return _refuse("not_compilable")
        return {
            "ok": True,
            "predicate": {
                "op": "all",
                "args": [
                    {"op": "calendar_event", "event_id": event_id},
                    {"op": "calendar_cancelled"},
                    {"op": "after", "at": created_at},
                ],
            },
        }
    if intent == "status_change":
        event_id = str(record.get("event_id") or "")
        status = str(record.get("calendar_status") or "")
        if not event_id or not status:
            return _refuse("not_compilable")
        return {
            "ok": True,
            "predicate": {
                "op": "all",
                "args": [
                    {"op": "calendar_event", "event_id": event_id},
                    {"op": "calendar_status_differs", "from_status": status},
                    {"op": "after", "at": created_at},
                ],
            },
        }
    return _refuse("bad_args")


def _session() -> tuple:
    turn_id = turn_context.current_turn_id_from_context()
    record = turn_context.get_record(turn_id) if turn_id else None
    if record is None:
        return "", ""
    return str(record.session_id or ""), str(record.turn_id or "")


def _untrusted(args: Dict[str, Any]) -> bool:
    if any(key not in _ALLOWED_KEYS for key in args):
        return True
    if any(key in args for key in _FORBIDDEN_KEYS):
        return True
    handle = str(args.get("handle") or "")
    if "@" in handle:
        return True
    return False


def _contacts():
    try:
        from . import contact_index
        from . import phone_ids
    except ImportError:
        import contact_index
        import phone_ids
    return contact_index, phone_ids


def _folded(message: str) -> str:
    return " ".join(str(message or "").casefold().split())


def _is_watch_request(message: str) -> bool:
    # P10-WATCH: a watch is created only when the words are a request to watch — verdict 15
    text = _folded(message)
    blocked = (
        "don't watch",
        "dont watch",
        "do not watch",
        "stop watching",
        "what are you watching",
        "what are you watching for",
    )
    if any(phrase in text for phrase in blocked):
        return False
    tokens = re.findall(r"[a-z']+", text)
    neg = {"dont", "don't", "never", "not", "no"}
    for index, token in enumerate(tokens):
        if token in ("watch", "watching"):
            if any(item in neg for item in tokens[max(0, index - 4) : index]):
                return False
    return any(
        cue in text
        for cue in ("watch for", "watch ", "let me know", "tell me when", "when i hear", "keep an eye")
    )


def _lifetime_of(message: str) -> str:
    text = _folded(message)
    if any(phrase in text for phrase in ("every time", "whenever", "each time")):
        return "standing"
    if "keep an eye" in text:
        return "ask"
    return "once"


def _text_verb(text: str) -> bool:
    for match in re.finditer(r"\b(texts|texted|text)\b", text):
        prefix = text[max(0, match.start() - 16) : match.start()]
        if re.search(r"\b(the|a|an|about|that|this)\s+$", prefix):
            continue
        return True
    return False


def _channel_of(message: str) -> str:
    # P10-WATCH: "the text I sent" is not a channel. "hear from" is both — verdict 1
    text = _folded(message)
    both = any(
        phrase in text
        for phrase in ("hear from", "gets back to me", "get back to me", "reaches out", "contacts me")
    )
    email = any(
        phrase in text
        for phrase in ("emails", "emailed", "sends an email", "send an email", "email me")
    )
    text_verb = _text_verb(text) or any(
        phrase in text for phrase in ("texts back", "text back", "messages me")
    )
    if text_verb and email:
        return "both"
    if text_verb and not both:
        return "text"
    if email and not both and not text_verb:
        return "email"
    return "both"


def _answer_of(message: str) -> str:
    text = _folded(message)
    if "never mind" in text or "wrong person" in text or text == "wrong":
        return "no"
    if "that's right" in text or "thats right" in text:
        return "yes"
    tokens = re.findall(r"[a-z']+", text)
    neg = {"dont", "don't", "never", "not", "no"}
    if any(token in ("no", "nope", "cancel") for token in tokens):
        return "no"
    for index, token in enumerate(tokens):
        if token in ("yes", "yeah", "yep", "correct"):
            if any(item in neg for item in tokens[max(0, index - 4) : index]):
                return "no"
            return "yes"
    return ""


def _name_in_message(display_name: str, message: str) -> bool:
    contact_index, _phone_ids = _contacts()
    spoken = contact_index._speech_form(display_name)
    if not spoken:
        return False
    return spoken in contact_index._speech_form(message)


def _number_in_message(canonical: str, message: str) -> bool:
    digits = "".join(ch for ch in canonical if ch.isdigit())
    heard = "".join(ch for ch in message if ch.isdigit())
    if not digits or not heard:
        return False
    if digits in heard:
        return True
    # A spoken 10-digit number is the same number as the +1 form.
    return len(digits) == 11 and digits.startswith("1") and digits[1:] in heard


def _groups_requested(message: str) -> bool:
    text = _folded(message)
    return any(phrase in text for phrase in ("including group", "group thread", "in groups", "and groups"))


def _mint(session_id: str, action: str, plan: Dict[str, Any]) -> None:
    _confirms[session_id] = {
        "action": action,
        "plan": plan,
        "expires": _confirm_clock() + CONFIRM_TTL_SECONDS,
    }


def _message_answers_confirmation(message: str, action: str) -> bool:
    # The next turn keeps the token only when its words are the answer the tool applies.
    if action == "watch_lifetime":
        text = _folded(message)
        return any(
            phrase in text
            for phrase in ("every time", "whenever", "each time", "next", "once", "just the")
        )
    return _answer_of(message) in ("yes", "no")


def note_turn(session_id: str, user_message: str) -> None:
    """Drop an open confirmation at the next turn unless this turn answers it.

    A turn that can answer arms the token for its tool call. If that call does not
    consume the token, the following turn drops it before any later yes can.
    """
    if not session_id:
        return
    token = _confirm_pending(session_id)
    if token is None:
        return
    if token.get("armed"):
        _confirms.pop(session_id, None)
        return
    if _message_answers_confirmation(user_message, str(token.get("action") or "")):
        token["armed"] = True
        return
    _confirms.pop(session_id, None)


def _confirm_pending(session_id: str) -> Optional[Dict[str, Any]]:
    token = _confirms.get(session_id)
    if not token:
        return None
    if _confirm_clock() > float(token["expires"]):
        _confirms.pop(session_id, None)
        return None
    return token


def _predicate_for(channel: str, hashes: List[str], created_at: str, *, direct_only: bool, handle: str, lifetime: str) -> Dict[str, Any]:
    args: List[Dict[str, Any]] = [
        {"op": "sender_any", "address_hashes": list(hashes)},
        {"op": "channel", "channel": channel},
        {"op": "after", "at": created_at},
    ]
    if direct_only:
        args.append({"op": "not_group"})
    return {
        "op": "all",
        "args": args,
        "lifetime": lifetime,
        "groups": not direct_only,
        "person_handle": handle,
        "channel": channel,
    }


def _store_watch(conn, session_id, intent, predicate, display_name, name_source, hashes) -> Dict[str, Any]:
    stored = proactive_store.insert_loop(
        conn,
        intent=intent,
        predicate=predicate,
        session_id=session_id,
        sender_display_name=display_name,
        name_source=name_source,
        subject="",
        source_ids=[],
        address_hashes=list(hashes),
    )
    if not stored.get("ok"):
        return stored
    _listed.setdefault(session_id, set()).add(stored["id"])
    _session_id, turn_id = _session()
    if turn_id:
        bucket = _created_on_turn.setdefault(turn_id, [])
        if stored["id"] not in bucket:
            bucket.append(stored["id"])
    if predicate.get("person_handle"):
        note_session_person(session_id, str(predicate["person_handle"]), display_name, stored["id"])
    return stored


def _create_contact_watch(conn, args, session_id, user_message) -> Dict[str, Any]:
    # P10-WATCH: person and number watches compile here — P10-D13 / verdicts 1, 14, 15
    if not _is_watch_request(user_message):
        return _refuse("not_a_watch")
    contact_index, phone_ids = _contacts()
    if contact_index.contacts_unavailable():
        return _refuse("contacts_unavailable")
    intent = str(args.get("intent") or "")
    lifetime = _lifetime_of(user_message)
    if lifetime == "ask":
        _mint(session_id, "watch_lifetime", {"message": user_message, "args": dict(args)})
        return {
            "ok": False,
            "refused_reason": "confirm_needed",
            "say": "Every time, or just the next one?",
        }
    channel = _channel_of(user_message)
    supplied = str(args.get("channel") or "")
    # A number watch is text. Passing text is not a disagreement with a both-phrase.
    if intent == "number":
        if supplied and supplied != "text":
            return _refuse("channel_disagrees")
    elif supplied and supplied != channel:
        return _refuse("channel_disagrees")
    from datetime import datetime, timezone

    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if intent == "number":
        kind, canonical = phone_ids.spoken_number(str(args.get("number") or user_message))
        if kind != phone_ids.KIND_E164 or not _number_in_message(canonical, user_message):
            return _refuse("number_not_in_message")
        digest = phone_ids.hash(canonical)
        owner = contact_index.resolve_person_by_phone_hash(digest)
        shared = False
        index = contact_index.get_index()
        if index is not None and len(index.by_number_hash(digest)) > 1:
            shared = True
            owner = None
        if shared:
            return _refuse("shared_number")
        predicate = _predicate_for("text", [digest], created_at, direct_only=False, handle="", lifetime="once")
        predicate["lifetime"] = "once"
        stored = _store_watch(conn, session_id, "number", predicate, "a number", "mail", [digest])
        if not stored.get("ok"):
            return stored
        say = "I'll let you know when that number texts."
        if owner is not None:
            say = (
                "I'll let you know when that number texts. That's "
                + owner.display_name
                + "'s number. Want me to watch for "
                + owner.display_name
                + " on any channel?"
            )
            widen_plan = {
                "handle": owner.handle,
                "display_name": owner.display_name,
                "created_at": created_at,
            }
            widen_plan.update(_identifier_snapshot(owner))
            _mint(session_id, "watch_widen", widen_plan)
        return {"ok": True, "loop_id": stored["id"], "intent": "number", "say": say, "channel": "text"}
    query = str(args.get("person") or "").strip()
    if not query:
        return _refuse("bad_args")
    if contact_index._speech_form(query) not in contact_index._speech_form(user_message):
        return _refuse("name_not_in_message")
    hits = contact_index.match_people_by_name(query)
    if not hits:
        return {
            "ok": False,
            "refused_reason": "not_in_contacts",
            "say": "I can't find that name in your contacts. If you tell me the number, I can watch that.",
        }
    if len(hits) > 1:
        return {
            "ok": False,
            "refused_reason": "which",
            "names": [person.display_name for person in hits],
        }
    person = hits[0]
    quality = contact_index.match_quality(person, query)
    groups = _groups_requested(user_message)
    direct_only = lifetime == "standing" and not groups
    plan = {
        "handle": person.handle,
        "display_name": person.display_name,
        "channel": channel,
        "lifetime": lifetime,
        "direct_only": direct_only,
        "created_at": created_at,
    }
    if quality != "exact":
        plan.update(_identifier_snapshot(person))
        _mint(session_id, "watch_person", plan)
        return {
            "ok": False,
            "refused_reason": "confirm_needed",
            "say": "Did you mean " + person.display_name + "?",
            "display_name": person.display_name,
        }
    if not _name_in_message(person.display_name, user_message):
        plan.update(_identifier_snapshot(person))
        _mint(session_id, "watch_person", plan)
        return {
            "ok": False,
            "refused_reason": "confirm_needed",
            "say": "Did you mean " + person.display_name + "?",
            "display_name": person.display_name,
        }
    return _commit_person_plan(conn, session_id, plan)


def _commit_person_plan(conn, session_id: str, plan: Dict[str, Any]) -> Dict[str, Any]:
    contact_index, phone_ids = _contacts()
    person = None
    index = contact_index.get_index()
    if index is not None:
        person = index.by_handle.get(plan["handle"])
    if person is None:
        return _refuse("not_in_contacts")
    numbers = list(contact_index.canonical_numbers_for(person))
    number_hashes = [phone_ids.hash(number) for number in numbers]
    email_hashes = list(person.email_hashes)
    # P10-WATCH: a yes is the action that was proposed. Changed identifiers are refused — verdict 2
    if "number_hashes" in plan or "email_hashes" in plan:
        if sorted(plan.get("number_hashes") or []) != sorted(number_hashes) or sorted(
            plan.get("email_hashes") or []
        ) != sorted(email_hashes):
            return _refuse("confirm_stale")
    channel = plan["channel"]
    if channel == "text":
        hashes = number_hashes
    elif channel == "email":
        hashes = email_hashes
    else:
        hashes = number_hashes + email_hashes
    if not hashes:
        return _refuse("not_compilable")
    predicate = _predicate_for(
        channel,
        hashes,
        plan["created_at"],
        direct_only=bool(plan["direct_only"]),
        handle=person.handle,
        lifetime=plan["lifetime"],
    )
    stored = _store_watch(
        conn,
        session_id,
        "person",
        predicate,
        person.display_name,
        "contacts_index",
        hashes,
    )
    if not stored.get("ok"):
        return stored
    channel_words = {"text": "texts", "email": "emails", "both": "texts or emails"}[channel]
    say = (
        "I'll let you know when "
        + person.display_name
        + " "
        + channel_words
        + ". I'll use the numbers and email addresses saved for them right now."
    )
    if plan["lifetime"] == "standing" and plan["direct_only"]:
        say += " That's direct texts only. Want me to include group threads?"
        _mint(session_id, "watch_groups", {"loop_id": stored["id"]})
    elif plan["lifetime"] == "standing":
        say = say.replace("I'll let you know when", "I'll let you know every time", 1)
    return {
        "ok": True,
        "loop_id": stored["id"],
        "intent": "person",
        "say": say,
        "channel": channel,
        "lifetime": plan["lifetime"],
        "display_name": person.display_name,
    }


def _identifier_snapshot(person: Any) -> Dict[str, Any]:
    contact_index, phone_ids = _contacts()
    numbers = list(contact_index.canonical_numbers_for(person))
    return {
        "number_hashes": [phone_ids.hash(number) for number in numbers],
        "email_hashes": list(person.email_hashes),
    }


def _proposal_disagrees(message: str, plan: Dict[str, Any]) -> bool:
    # A bare yes agrees. An explicit channel, lifetime, or group change does not — verdict 2
    text = _folded(message)
    lifetime = str(plan.get("lifetime") or "")
    if any(phrase in text for phrase in ("every time", "whenever", "each time")) and lifetime != "standing":
        return True
    if lifetime == "standing" and any(phrase in text for phrase in ("just the next", "only once", "just once")):
        return True
    channel = str(plan.get("channel") or "")
    text_verb = _text_verb(text)
    email = any(phrase in text for phrase in ("emails", "emailed", "sends an email", "send an email", "email me"))
    if text_verb and not email and channel == "email":
        return True
    if email and not text_verb and channel == "text":
        return True
    if _groups_requested(message) and plan.get("direct_only"):
        return True
    if "direct texts only" in text and not plan.get("direct_only"):
        return True
    return False


def _apply_confirmation(conn, session_id: str, message: str, intent: str = "") -> Optional[Dict[str, Any]]:
    token = _confirm_pending(session_id)
    if token is None:
        return None
    answer = _answer_of(message)
    action = token["action"]
    if action == "watch_lifetime":
        text = _folded(message)
        if "every time" in text:
            chosen = "standing"
        elif "next" in text or "once" in text or "just the" in text:
            chosen = "once"
        else:
            _confirms.pop(session_id, None)
            return _refuse("lapsed")
        plan_args = token["plan"]["args"]
        rewritten = message + (" every time" if chosen == "standing" else " let me know when")
        _confirms.pop(session_id, None)
        return _create_contact_watch(conn, plan_args, session_id, rewritten)
    if answer == "no":
        _confirms.pop(session_id, None)
        return {"ok": True, "say": "All right. I didn't change anything.", "created": False}
    if answer != "yes":
        _confirms.pop(session_id, None)
        return _refuse("lapsed")
    if intent and intent not in ("person", "number") and str(action).startswith("watch"):
        _confirms.pop(session_id, None)
        return _refuse("lapsed")
    plan = token["plan"]
    if isinstance(plan, dict) and _proposal_disagrees(message, plan):
        _confirms.pop(session_id, None)
        return _refuse("confirm_stale")
    _confirms.pop(session_id, None)
    if action == "watch_person":
        return _commit_person_plan(conn, session_id, plan)
    if action == "watch_widen":
        widened = dict(plan)
        widened["channel"] = "both"
        widened["lifetime"] = "once"
        widened["direct_only"] = False
        from datetime import datetime, timezone

        widened["created_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return _commit_person_plan(conn, session_id, widened)
    if action == "watch_groups":
        row = conn.execute(
            "SELECT predicate_json FROM loops WHERE id = ? AND status = 'open'",
            (plan["loop_id"],),
        ).fetchone()
        if row is None:
            return {"ok": True, "say": "That one already closed."}
        predicate = json.loads(row["predicate_json"] or "{}")
        predicate["groups"] = True
        predicate["args"] = [child for child in predicate.get("args") or [] if child.get("op") != "not_group"]
        saved = proactive_store.replace_loop_predicate(conn, plan["loop_id"], predicate)
        if not saved.get("ok"):
            return {"ok": True, "say": "That one already closed."}
        return {"ok": True, "say": "I'll include group threads.", "loop_id": plan["loop_id"]}
    return _refuse("lapsed")


def _close_by_reference(conn, session_id: str) -> Dict[str, Any]:
    # P10-WATCH: the handler finds the loop. The model does not supply the id — verdict 10
    people = _session_people.get(session_id) or {}
    if not people:
        return _refuse("no_reference")
    if len(people) > 1:
        return {"ok": False, "refused_reason": "which", "names": [item.get("name") or "" for item in people.values()]}
    info = next(iter(people.values()))
    loop_id = str(info.get("loop_id") or "")
    if not loop_id:
        handle = str(info.get("handle") or "")
        for row in conn.execute("SELECT id, predicate_json FROM loops WHERE status = 'open'"):
            try:
                predicate = json.loads(row["predicate_json"] or "{}")
            except json.JSONDecodeError:
                continue
            if str(predicate.get("person_handle") or "") == handle:
                loop_id = str(row["id"])
                break
    if not loop_id:
        return {"ok": True, "say": "That one already closed."}
    _listed.setdefault(session_id, set()).add(loop_id)
    closed = proactive_store.close_loop(conn, loop_id, closed_intent="cancelled")
    if not closed.get("ok"):
        return {"ok": True, "say": "That one already closed."}
    return {"ok": True, "loop_id": loop_id, "closed_intent": "cancelled"}


def create_loop(conn: Any, args: Dict[str, Any]) -> Dict[str, Any]:
    if not turn_context.is_brian_turn():
        return _refuse("origin")
    if _untrusted(args):
        return _refuse("untrusted_argument")
    intent = str(args.get("intent") or "")
    if intent not in _INTENTS:
        return _refuse("bad_args")
    session_id, turn_id = _session()
    if not session_id:
        return _refuse("origin")
    turn_record = turn_context.get_record(turn_id) if turn_id else None
    user_message = turn_record.user_message if turn_record and isinstance(turn_record.user_message, str) else ""
    confirmed = _apply_confirmation(conn, session_id, user_message, intent)
    if confirmed is not None:
        return confirmed
    if intent in ("person", "number"):
        return _create_contact_watch(conn, args, session_id, user_message)
    record = None
    if intent != "confirm_close":
        kind = _kind_for(intent)
        resolved = recorded_results.resolve(session_id, kind, str(args.get("handle") or ""))
        if not resolved.get("ok"):
            return _refuse(str(resolved.get("refused_reason") or "unknown_handle"), count=resolved.get("count", 0))
        record = resolved["record"]
    from datetime import datetime, timezone

    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    compiled = compile_predicate(intent, record, created_at=created_at)
    if not compiled.get("ok"):
        return compiled
    try:
        try:
            from . import speech
        except ImportError:
            import speech
        source, chosen = speech.provenance(
            session_id,
            "" if record is None else str(record.get("sender_display_name") or ""),
            [] if record is None else list(record.get("address_hashes") or []),
            user_message,
        )
    except Exception:
        source, chosen = "mail", "" if record is None else str(record.get("sender_display_name") or "")
    display_name = chosen if source != "mail" else ("" if record is None else str(record.get("sender_display_name") or ""))
    stored = proactive_store.insert_loop(
        conn,
        intent=intent,
        predicate=compiled["predicate"],
        session_id=session_id,
        sender_display_name=display_name,
        name_source=source,
        subject="" if record is None else str(record.get("subject") or ""),
        source_ids=[]
        if record is None
        else [value for value in (record.get("message_id"), record.get("thread_id"), record.get("event_id")) if value],
        address_hashes=[] if record is None else list(record.get("address_hashes") or []),
    )
    if not stored.get("ok"):
        return stored
    _listed.setdefault(session_id, set()).add(stored["id"])
    watching = {
        "sender_display_name": "" if record is None else str(record.get("sender_display_name") or ""),
        "subject": "" if record is None else str(record.get("subject") or ""),
    }
    return {
        "ok": True,
        "loop_id": stored["id"],
        "intent": intent,
        "operators": _operator_names(compiled["predicate"]),
        "watching": watching,
    }


def _operator_names(predicate: Dict[str, Any]) -> List[str]:
    names = [str(predicate.get("op") or "")]
    for child in predicate.get("args") or []:
        if isinstance(child, dict):
            names.extend(_operator_names(child))
    return [name for name in names if name and name not in ("all", "any")]


def list_loops(conn: Any) -> Dict[str, Any]:
    if not turn_context.is_brian_turn():
        return _refuse("origin")
    session_id, _turn_id = _session()
    if not session_id:
        return _refuse("origin")
    listed = proactive_store.list_open_loops(conn)
    if not listed.get("ok"):
        return listed
    _listed[session_id] = {row["id"] for row in listed["loops"]}
    return listed


def _is_stop(message: str) -> bool:
    # P10-WATCH: "stop watching for <person>" is a cancel, by name or by pronoun
    return "stop watching" in _folded(message)


def _json_dict(text: str) -> Dict[str, Any]:
    try:
        value = json.loads(text or "{}")
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _json_list(text: str) -> List[str]:
    try:
        value = json.loads(text or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _channel_set(channel: str) -> set:
    if channel == "both":
        return {"text", "email"}
    if channel in ("text", "email"):
        return {channel}
    return set()


def _same_person(old_pred: Dict[str, Any], new_pred: Dict[str, Any], old_hashes: List[str], new_hashes: List[str]) -> bool:
    old_handle = str(old_pred.get("person_handle") or "")
    new_handle = str(new_pred.get("person_handle") or "")
    if old_handle and old_handle == new_handle:
        return True
    return bool(set(old_hashes) & set(new_hashes))


def _covers(new_pred: Dict[str, Any], old_pred: Dict[str, Any]) -> bool:
    # The new watch covers the old one when every old channel is included and the lifetime is at least as long.
    old_life = str(old_pred.get("lifetime") or "")
    new_life = str(new_pred.get("lifetime") or "")
    if old_life == "standing":
        if new_life != "standing":
            return False
    elif old_life != "once" or new_life not in ("once", "standing"):
        return False
    return _channel_set(str(old_pred.get("channel") or "")) <= _channel_set(str(new_pred.get("channel") or ""))


def _widen_say(old_pred: Dict[str, Any], new_pred: Dict[str, Any]) -> str:
    old_ch = str(old_pred.get("channel") or "")
    new_ch = str(new_pred.get("channel") or "")
    old_life = str(old_pred.get("lifetime") or "")
    new_life = str(new_pred.get("lifetime") or "")
    sentences: List[str] = []
    if old_ch == "text" and "email" in _channel_set(new_ch):
        sentences.append("I've widened your text watch to cover email.")
    elif old_ch == "email" and "text" in _channel_set(new_ch):
        sentences.append("I've widened your email watch to cover texts.")
    if old_life == "once" and new_life == "standing":
        kind = {"text": "text watch", "email": "email watch"}.get(old_ch, "watch")
        sentences.append("I've widened your " + kind + " to every time.")
    if not sentences:
        sentences.append("The new watch covers that one.")
    return " ".join(sentences)


def _widen_close(conn: Any, turn_id: str, loop_id: str) -> Optional[Dict[str, Any]]:
    old = conn.execute(
        "SELECT status, predicate_json, address_hashes_json FROM loops WHERE id = ?",
        (loop_id,),
    ).fetchone()
    if old is None or old["status"] != "open":
        return None
    old_pred = _json_dict(old["predicate_json"])
    old_hashes = _json_list(old["address_hashes_json"])
    say = ""
    for created_id in _created_on_turn.get(turn_id, []):
        if created_id == loop_id:
            continue
        row = conn.execute(
            "SELECT status, predicate_json, address_hashes_json FROM loops WHERE id = ?",
            (created_id,),
        ).fetchone()
        if row is None or row["status"] != "open":
            continue
        new_pred = _json_dict(row["predicate_json"])
        if not _same_person(old_pred, new_pred, old_hashes, _json_list(row["address_hashes_json"])):
            continue
        if _covers(new_pred, old_pred):
            say = _widen_say(old_pred, new_pred)
            break
    if not say:
        return _refuse("not_covered")
    return {"ok": True, "say": say}


def _is_widen_turn(message: str) -> bool:
    # "watch that mail" is a reply watch. A widen close is only a contact-watch turn.
    if not _is_watch_request(message):
        return False
    text = _folded(message)
    return any(
        cue in text
        for cue in (
            "watch for",
            "let me know",
            "tell me when",
            "hear from",
            "keep an eye",
            "texts",
            "emails",
        )
    )


def _reason_on_his_turn(user_message: str, args: Dict[str, Any]) -> str:
    # A stop, a missing reason, or a watch intent all record cancelled. An explicit close reason is kept.
    if _is_stop(user_message):
        return "cancelled"
    intent = str(args.get("intent") or "")
    if intent in proactive_store.CLOSED_INTENTS:
        return intent
    return "cancelled"


def close_listed(conn: Any, args: Dict[str, Any]) -> Dict[str, Any]:
    if not turn_context.is_brian_turn():
        return _refuse("origin")
    if _untrusted(args):
        return _refuse("untrusted_argument")
    session_id, turn_id = _session()
    record = turn_context.get_record(turn_id) if turn_id else None
    user_message = record.user_message if record and isinstance(record.user_message, str) else ""
    loop_id = str(args.get("loop_id") or "")
    if not loop_id:
        if not session_id:
            return _refuse("origin")
        return _close_by_reference(conn, session_id)
    if not session_id or loop_id not in _listed.get(session_id, set()):
        return _refuse("unknown_loop")
    if _is_widen_turn(user_message):
        verdict = _widen_close(conn, turn_id, loop_id)
        if verdict is not None and not verdict.get("ok"):
            return verdict
        closed = proactive_store.close_loop(conn, loop_id, closed_intent="cancelled")
        if not closed.get("ok") or verdict is None:
            return closed
        closed["say"] = verdict["say"]
        closed["closed_intent"] = "cancelled"
        return closed
    return proactive_store.close_loop(
        conn, loop_id, closed_intent=_reason_on_his_turn(user_message, args)
    )


def _watching_has_text(result: Dict[str, Any]) -> bool:
    watching = result.get("watching") or {}
    if not isinstance(watching, dict):
        return False
    return bool(
        str(watching.get("sender_display_name") or "").strip()
        or str(watching.get("subject") or "").strip()
    )


def _present(action: str, result: Dict[str, Any]) -> str:
    """Frame mail text the way a Gmail read does, and taint the session first."""
    if not result.get("ok"):
        return json.dumps(result, ensure_ascii=False)
    if action == "list":
        # P9-STORE: sender and subject came from mail, so the list is untrusted content — P9-D09
        return read_common.mark_then_frame(
            TOOL_NAME,
            result,
            empty_key="loops",
            log_event=wslog.LOG_EVENT_LOOPS,
            log_fields={"state": "complete", "count": len(result.get("loops") or [])},
        )
    if action == "create" and _watching_has_text(result):
        session_id, task_id = read_common._ids_for_turn()
        # P9-STORE: a create echo taints only when this session has not already read mail — P9-D09
        if not taint.is_tainted(session_id, task_id or None):
            return read_common.mark_then_frame(
                TOOL_NAME,
                result,
                empty_key="watching",
                log_event=wslog.LOG_EVENT_LOOPS,
                log_fields={"state": "complete", "count": 1},
            )
        return read_common.dump_result(TOOL_NAME, result)
    return json.dumps(result, ensure_ascii=False)


def loops_handler(args: dict, **kwargs: Any) -> str:
    """Ticket-checked create, list, and close. Never raises."""
    try:
        payload = args if isinstance(args, dict) else {}
        action = str(payload.get("action") or "")
        path = proactive_store.profile_db_path()
        if path is None:
            return json.dumps(_refuse("missing"), ensure_ascii=False)
        conn = proactive_store.connect(path)
        try:
            if action == "create":
                result = create_loop(conn, payload)
            elif action == "list":
                result = list_loops(conn)
            elif action == "close":
                result = close_listed(conn, payload)
            else:
                result = _refuse("bad_args")
        finally:
            conn.close()
        return _present(action, result)
    except Exception:
        return json.dumps(_refuse("error"), ensure_ascii=False)
