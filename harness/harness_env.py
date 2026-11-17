from __future__ import annotations

import os

_TRUE_VALUES = ("1", "true", "yes", "on")
_FALSE_VALUES = ("0", "false", "no", "off")


def env_int_or_default(key: str, default: int) -> int:
    s = os.environ.get(key, "")
    if not s:
        return default
    try:
        return int(s)
    except ValueError:
        return default


def env_str_or_default(key: str, default: str) -> str:
    return os.environ.get(key, "") or default


def env_bool_or_default(key: str, default: bool) -> bool:
    s = os.environ.get(key, "").strip().lower()
    if s in _TRUE_VALUES:
        return True
    if s in _FALSE_VALUES:
        return False
    return default
