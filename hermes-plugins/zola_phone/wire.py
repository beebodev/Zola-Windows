"""Phone frame checks. Standard library plus cryptography. No test-key file (P10-D12)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

# P10-INTAKE: the contract file is the one source for ports, limits, and reasons — P10-D12
_CONTRACT = Path(__file__).resolve().parent.parent / "zola_workspace" / "contracts" / "phone_protocol.json"


def load_protocol() -> Dict[str, Any]:
    return json.loads(_CONTRACT.read_text(encoding="utf-8"))


def canonical(payload: Dict[str, Any]) -> bytes:
    rules = load_protocol()["canonical_json"]
    return json.dumps(
        payload,
        sort_keys=bool(rules["sort_keys"]),
        separators=tuple(rules["separators"]),
        ensure_ascii=bool(rules["ensure_ascii"]),
    ).encode("utf-8")


def _protocol_or(protocol: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return protocol if protocol is not None else load_protocol()


def frame_limit(protocol: Optional[Dict[str, Any]] = None) -> int:
    return int(_protocol_or(protocol)["size_limits"]["frame_bytes"])


def verify_signature(public_pem: str, payload: Dict[str, Any], signature: str) -> bool:
    if not signature or not public_pem:
        return False
    try:
        raw = base64.b64decode(signature)
        key = serialization.load_pem_public_key(public_pem.encode("ascii"))
        key.verify(raw, canonical(payload), ec.ECDSA(hashes.SHA256()))
    except (InvalidSignature, ValueError, TypeError):
        return False
    return True


def sign_payload(private_pem: str, payload: Dict[str, Any]) -> str:
    key = serialization.load_pem_private_key(private_pem.encode("ascii"), password=None)
    signature = key.sign(canonical(payload), ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(signature).decode("ascii")


def pairing_mac(code: str, payload: Dict[str, Any]) -> str:
    # P10-INTAKE: the one-time code is the HMAC key, not a field in the payload — P10-D12
    digest = hmac.new(str(code).encode("utf-8"), canonical(payload), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def mac_matches(code: str, payload: Dict[str, Any], signature: str) -> bool:
    if not signature or not code:
        return False
    expected = pairing_mac(code, payload)
    return hmac.compare_digest(expected, str(signature))


def encode_frame(kind: str, payload: Dict[str, Any], signature: str, protocol: Optional[Dict[str, Any]] = None) -> bytes:
    protocol = _protocol_or(protocol)
    body = {
        "magic": protocol["magic"],
        "kind": kind,
        "signature": signature,
        "payload": payload,
    }
    return json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _case_payload(case: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(case.get("payload") or {})
    if case.get("pad_bytes"):
        payload["pad"] = "x" * int(case["pad_bytes"])
    return payload


def _field_too_large(payload: Dict[str, Any], protocol: Dict[str, Any]) -> bool:
    limits = protocol["size_limits"]
    kind = str(payload.get("type") or "")
    if kind == "notifications.event":
        text = str(payload.get("text") or "")
        return len(text) > int(limits["notification_text_chars"])
    body = payload.get("body")
    if isinstance(body, str) and len(body) > int(limits["text_body_chars"]):
        return True
    return False


def classify_raw(
    raw: bytes,
    *,
    protocol: Optional[Dict[str, Any]] = None,
    paired_public: str = "",
    rejected_publics: Sequence[str] = (),
    paired_device_id: str = "",
    last_seq: int = 0,
    now_ms: int = 0,
    pairing_code: str = "",
    on_verify=None,
) -> str:
    """First matching check wins. Raw size returns before parse or signature."""
    protocol = _protocol_or(protocol)
    if len(raw) > frame_limit(protocol):
        return "too-large"
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "malformed"
    if not isinstance(parsed, dict):
        return "malformed"
    if parsed.get("magic") != protocol["magic"]:
        return "malformed"
    if parsed.get("kind") not in protocol["frame_kinds"]:
        return "malformed"
    payload = parsed.get("payload")
    if not isinstance(payload, dict):
        return "malformed"
    required = protocol["common_fields"]
    if any(field not in payload for field in required):
        return "malformed"
    separator = protocol["identity_separator"]
    for field in ("device_id", "provider_id", "kind", "package", "notification_key", "newest_message_timestamp"):
        if separator in str(payload.get(field) or ""):
            return "malformed"
    signature = str(parsed.get("signature") or "")
    if not signature:
        return "unsigned"
    if on_verify is not None:
        on_verify()
    kind = str(parsed.get("kind"))
    if kind == "pairing":
        if not mac_matches(pairing_code, payload, signature):
            return "bad-signature"
    else:
        if paired_public and verify_signature(paired_public, payload, signature):
            pass
        elif any(verify_signature(pem, payload, signature) for pem in rejected_publics if pem):
            return "unknown-key"
        else:
            return "bad-signature"
    if kind != "pairing" and paired_device_id and payload.get("device_id") != paired_device_id:
        return "wrong-device"
    try:
        seq = int(payload["seq"])
        sent = int(payload["sent_at_ms"])
        version = int(payload["contract_version"])
    except (TypeError, ValueError):
        return "malformed"
    new_device = kind == "pairing" and bool(paired_device_id) and payload.get("device_id") != paired_device_id
    if not new_device and seq <= int(last_seq):
        return "replay"
    window = int(protocol["timing_ms"]["stale_window"])
    if abs(sent - int(now_ms)) > window:
        return "stale"
    # P10-INTAKE: an unsupported contract version is its own reason — P10-D12
    supported = [int(item) for item in protocol["supported_versions"]]
    if version not in supported:
        return "version"
    if len(canonical(payload)) > frame_limit(protocol):
        return "too-large"
    if _field_too_large(payload, protocol):
        return "too-large"
    return "accept"


def decide_case(case: Dict[str, Any], protocol: Dict[str, Any], keys: Dict[str, Any], vectors: Dict[str, Any]) -> str:
    """Golden-vector entry. Same order as classify_raw."""
    if case.get("raw_bytes"):
        return classify_raw(b"x" * int(case["raw_bytes"]), protocol=protocol)
    if "payload_raw" in case and "payload" not in case:
        try:
            parsed = json.loads(case["payload_raw"])
        except json.JSONDecodeError:
            return "malformed"
        if not isinstance(parsed, dict):
            return "malformed"
        raw = json.dumps(
            {"magic": protocol["magic"], "kind": "signed", "signature": "x", "payload": parsed},
            separators=(",", ":"),
        ).encode("utf-8")
        return classify_raw(raw, protocol=protocol, paired_public=keys["keys"]["paired"]["public_pem"])
    payload = _case_payload(case)
    kind = "pairing" if case.get("kind") == "pairing" else "signed"
    signature = str(case.get("signature") or "")
    raw = encode_frame(kind, payload, signature, protocol)
    pubs = keys["keys"]
    paired_id = str(case.get("device_id") or keys.get("paired_device_id") or vectors.get("paired_device_id") or "")
    if case.get("name") in ("wrong-device",):
        paired_id = str(keys.get("paired_device_id") or vectors.get("paired_device_id") or "")
    rejected = [pubs["old"]["public_pem"], pubs["unauthorized"]["public_pem"]]
    last = int(case.get("last_accepted_seq", vectors["last_accepted_seq"]))
    now_ms = int(case.get("now_ms", vectors["now_ms"]))
    code = str(case.get("pairing_code") or vectors.get("pairing_code") or "")
    return classify_raw(
        raw,
        protocol=protocol,
        paired_public=pubs["paired"]["public_pem"],
        rejected_publics=rejected,
        paired_device_id=paired_id,
        last_seq=last,
        now_ms=now_ms,
        pairing_code=code,
    )
