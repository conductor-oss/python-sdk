# Copyright (c) 2026 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Backward-compat shim — schedule exceptions moved to ``conductor.client.ai``.

Import from :mod:`conductor.client.ai.schedule_errors` (or ``conductor.client.ai``)
going forward. Same class objects, so ``except`` clauses are unaffected.
"""

from __future__ import annotations

from conductor.client.ai.schedule_errors import (  # noqa: F401
    InvalidCronExpression,
    ScheduleError,
    ScheduleNameConflict,
    ScheduleNotFound,
)
