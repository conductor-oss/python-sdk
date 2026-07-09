# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Kitchen Sink helpers — mock services, data fixtures, external worker stubs.

These simulate external dependencies so the kitchen sink can run standalone
without real APIs. In production, these would be replaced by actual services.
"""

import re
from typing import Any, Dict, List

from pydantic import BaseModel


# ── Structured Output Models ──────────────────────────────────────────


class ClassificationResult(BaseModel):
    """Stage 1 output: article classification."""

    category: str
    priority: int
    tags: List[str]
    metadata: Dict[str, Any]


class ArticleReport(BaseModel):
    """Stage 8 output: analytics report."""

    word_count: int
    sentiment_score: float
    readability_grade: str
    top_keywords: List[str]


# ── Mock Data ─────────────────────────────────────────────────────────

MOCK_RESEARCH_DATA = {
    "quantum_computing": {
        "title": "Quantum Computing Advances in 2026",
        "sources": [
            "Nature Physics Vol 22",
            "IEEE Quantum Computing Summit 2026",
            "arXiv:2601.12345",
        ],
        "key_findings": [
            "1000+ qubit processors achieved by 3 vendors",
            "Quantum error correction breakthrough at Google",
            "First commercial quantum advantage in drug discovery",
        ],
    }
}

MOCK_PAST_ARTICLES = [
    {"id": "art-001", "title": "Quantum Computing in 2025", "score": 0.92},
    {"id": "art-002", "title": "AI and Quantum Synergies", "score": 0.85},
    {"id": "art-003", "title": "Post-Quantum Cryptography", "score": 0.78},
]


# ── Guardrail Patterns ───────────────────────────────────────────────

PII_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
    r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",  # Credit card
]

SQL_INJECTION_PATTERNS = [
    r"(?i)(union\s+select|drop\s+table|delete\s+from|insert\s+into)",
    r"(?i)(--\s|;\s*drop|'\s*or\s+'1'\s*=\s*'1')",
]


def contains_pii(text: str) -> bool:
    """Check if text contains PII patterns (SSN or credit card)."""
    for pattern in PII_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def contains_sql_injection(text: str) -> bool:
    """Check if text contains SQL injection patterns."""
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


# ── Callback Logger ──────────────────────────────────────────────────


class CallbackLog:
    """Captures callback events for testing."""

    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def log(self, event_type: str, **kwargs):
        self.events.append({"type": event_type, **kwargs})

    def clear(self):
        self.events.clear()


callback_log = CallbackLog()
