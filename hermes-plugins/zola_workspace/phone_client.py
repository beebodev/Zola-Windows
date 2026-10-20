"""Serve-side client for zola-phone. The secret stays out of logs (P10-D12)."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from zola_phone.serve import pipe_request
from zola_phone.wire import load_protocol

try:
    from . import launch_secret
except ImportError:
    import launch_secret

SECRET_ENV = "ZOLA_PHONE_LAUNCH_SECRET"


def call(kind: str, **fields: Any) -> Dict[str, Any]:
    protocol = load_protocol()
    body = {"type": kind}
    body.update(fields)
    if protocol["local_requests"].get(kind, {}).get("secret"):
        body["secret"] = launch_secret.current() or os.environ.get(SECRET_ENV, "")
    try:
        return pipe_request(protocol["pipe_name"], body)
    except OSError:
        return {"ok": False, "status": "phone_unavailable", "reason": "no_connection"}
