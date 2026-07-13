# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Unit tests for the JWT-expiry decoder.

Token minting/caching moved to the SDK ``ApiClient`` — see ``test_agent_http.py``
for the worker HTTP path. This module only covers ``decode_jwt_exp``.
"""

import base64
import json

from conductor.ai.agents._internal.token_utils import decode_jwt_exp


def _jwt(exp: int) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode()).rstrip(b"=").decode()
    return f"{header}.{payload}.sig"


def test_decode_jwt_exp_reads_exp():
    assert decode_jwt_exp(_jwt(1700000000)) == 1700000000.0


def test_decode_jwt_exp_opaque_or_malformed_returns_zero():
    assert decode_jwt_exp("opaque-token") == 0.0
    assert decode_jwt_exp("") == 0.0
    assert decode_jwt_exp("a.b") == 0.0  # payload segment not valid JSON


def test_decode_jwt_exp_missing_exp_returns_zero():
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps({"sub": "x"}).encode()).rstrip(b"=").decode()
    assert decode_jwt_exp(f"{header}.{payload}.sig") == 0.0
