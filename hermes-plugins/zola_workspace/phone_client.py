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


def call(request: str, **fields: Any) -> Dict[str, Any]:
    # P10-READ: the first argument is the pipe request type. It is not named `kind`, because
    # read_code and code.arm carry a message `kind` (sms or mms) as a field of their own — RD-G8
    protocol = load_protocol()
    body = {"type": request}
    body.update(fields)
    if protocol["local_requests"].get(request, {}).get("secret"):
        body["secret"] = launch_secret.current() or os.environ.get(SECRET_ENV, "")
    try:
        return pipe_request(protocol["pipe_name"], body)
    except Exception:
        # P10-READ: a missing pipe raises pywintypes.error, which is not an OSError; every failure
        # to reach zola-phone reads as "no connection" and carries no detail
        return {"ok": False, "status": "phone_unavailable", "reason": "no_connection"}
