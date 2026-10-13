"""The L6 harness must not change a forget-hold row it did not create."""

from __future__ import annotations

from typing import Optional


def harness_hold_decision(existing: Optional[str]) -> str:
    """Return skip when a hold row is already stored. proceed only when there is none."""
    if existing:
        return "skip"
    return "proceed"
