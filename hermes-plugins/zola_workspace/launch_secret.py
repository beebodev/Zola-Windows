"""The phone launch secret lives in this process only (P10-D12)."""

from __future__ import annotations

import os

SECRET_ENV = "ZOLA_PHONE_LAUNCH_SECRET"
_value = ""


def take() -> str:
    # P10-INTAKE: register removes the variable before any tool can start a subprocess — P10-D12
    global _value
    if SECRET_ENV in os.environ:
        _value = os.environ.pop(SECRET_ENV)
    return _value


def current() -> str:
    return _value
