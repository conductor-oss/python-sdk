"""Tests for conductor.ai.agents.testing.semantic.

Imported through the package rather than the submodule, deliberately: that is
the path ``semantic.py``'s docstring tells users to take, so exercising it here
keeps the re-export honest.  ``litellm`` is an optional dependency and is
stubbed throughout, following ``test_guardrail.py``.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from conductor.ai.agents.result import AgentResult
from conductor.ai.agents.testing import assert_output_satisfies


def _judge_returning(payload: str) -> MagicMock:
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = payload
    return response


def _result(output: str = "Sunny in NYC, 22C") -> AgentResult:
    return AgentResult(output=output)


def test_passes_when_score_meets_threshold():
    with patch.dict("sys.modules", {"litellm": MagicMock()}):
        sys.modules["litellm"].completion.return_value = _judge_returning(
            '{"score": 0.9, "reason": "covers NYC weather"}'
        )

        assert_output_satisfies(_result(), criterion="mentions NYC weather", threshold=0.7)


def test_fails_below_threshold_and_reports_the_judge_reason():
    with patch.dict("sys.modules", {"litellm": MagicMock()}):
        sys.modules["litellm"].completion.return_value = _judge_returning(
            '{"score": 0.2, "reason": "no weather at all"}'
        )

        with pytest.raises(AssertionError, match="no weather at all"):
            assert_output_satisfies(_result(), criterion="mentions NYC weather", threshold=0.7)


def test_criterion_and_output_reach_the_judge():
    with patch.dict("sys.modules", {"litellm": MagicMock()}):
        sys.modules["litellm"].completion.return_value = _judge_returning(
            '{"score": 1.0, "reason": "ok"}'
        )

        assert_output_satisfies(_result("Sunny in NYC"), criterion="mentions NYC")

        prompt = sys.modules["litellm"].completion.call_args.kwargs["messages"][1]
        assert "mentions NYC" in prompt["content"]
        assert "Sunny in NYC" in prompt["content"]


def test_unparseable_judge_reply_fails_rather_than_passing():
    with patch.dict("sys.modules", {"litellm": MagicMock()}):
        sys.modules["litellm"].completion.return_value = _judge_returning("not json")

        with pytest.raises(AssertionError, match="unparseable"):
            assert_output_satisfies(_result(), criterion="anything")


def test_missing_litellm_raises_with_an_install_hint():
    with patch.dict("sys.modules", {"litellm": None}):
        with pytest.raises(ImportError, match="litellm"):
            assert_output_satisfies(_result(), criterion="anything")
