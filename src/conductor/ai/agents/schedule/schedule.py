# Copyright (c) 2026 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

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
