"""Stable, versioned identity for experiment inputs and reports."""

import hashlib
import json
import math
from typing import Any


class CanonicalizationError(ValueError):
    pass


def _validate(value: Any) -> None:
    if value is None or isinstance(value, (bool, str, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalizationError("NaN and infinity have no canonical representation")
        return
    if isinstance(value, list):
        for item in value:
            _validate(item)
        return
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise CanonicalizationError("all object keys must be strings")
        for item in value.values():
            _validate(item)
        return
    raise CanonicalizationError(f"unsupported canonical value: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    """Encode JSON values consistently; callers convert models to JSON first."""
    _validate(value)
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def digest(value: Any, *, domain: str) -> str:
    """Domain separation prevents a config hash being confused with an artifact hash."""
    if not domain or "\x00" in domain:
        raise ValueError("domain must be nonempty and contain no NUL")
    payload = domain.encode("utf-8") + b"\x00" + canonical_bytes(value)
    return "sha256:" + hashlib.sha256(payload).hexdigest()
