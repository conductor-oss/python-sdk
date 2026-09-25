"""Backward-compat shim — ``Schedule``/``ScheduleInfo`` moved to ``conductor.client.ai``.

Import from :mod:`conductor.client.ai` going forward. This module re-exports the
same objects, so existing imports (and ``isinstance`` checks) are unaffected.
"""

from __future__ import annotations

from conductor.client.ai.schedule import (  # noqa: F401
    Schedule,
    ScheduleInfo,
    _prefix,
    _unprefix,
)
