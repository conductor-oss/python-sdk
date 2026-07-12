# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""JWT helper for the agent runtime.

Auth-token minting/caching lives in the SDK ``ApiClient`` (a single token
authority — mint/cache/TTL-refresh/401-retry); the worker HTTP path reuses it via
``conductor.ai.agents._internal.agent_http``. This module only *decodes* a JWT's
expiry.
"""

from __future__ import annotations

import base64
import json


def decode_jwt_exp(token: str) -> float:
    """Best-effort decode of a JWT's ``exp`` claim (unix seconds).

    Returns 0.0 for opaque tokens, malformed JWTs, or tokens without ``exp`` —
    callers treat 0 as "expiry unknown, use until rejected".
    """
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return 0.0
        seg = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(seg))
        return float(payload.get("exp", 0) or 0)
    except Exception:
        return 0.0
