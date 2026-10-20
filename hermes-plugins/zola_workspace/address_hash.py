"""WT-G8 address hash. Standard library only."""

from __future__ import annotations

import hashlib


def address_hash(address: str) -> str:
    # P9-STORE: forget matches the hash, so the pending record need not keep the address — P9-D06
    return hashlib.sha256(address.strip().casefold().encode("utf-8")).hexdigest()
