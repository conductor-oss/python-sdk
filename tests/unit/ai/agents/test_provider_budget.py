import pytest

from e2e.provider_budget import (
    OUT_OF_BUDGET_ENV,
    out_of_budget_providers,
    provider_from_model,
    require_llm_provider,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("anthropic/claude-sonnet-4-6", "anthropic"),
        ("claude-sonnet-4-6", "anthropic"),
        ("openai/gpt-4o-mini", "openai"),
        ("gpt-4o-mini", "openai"),
    ],
)
def test_provider_from_model(value, expected):
    assert provider_from_model(value) == expected


def test_out_of_budget_providers_parses_multiple_values():
    assert out_of_budget_providers(
        " Anthropic, OPENAI, google_gemini, aws_bedrock ,, "
    ) == {
        "anthropic",
        "openai",
        "google_gemini",
        "aws_bedrock",
    }


def test_out_of_budget_providers_allows_empty_value():
    assert out_of_budget_providers("") == set()


def test_require_llm_provider_skips_matching_provider(monkeypatch):
    monkeypatch.setenv(OUT_OF_BUDGET_ENV, "anthropic")

    with pytest.raises(pytest.skip.Exception, match="anthropic provider"):
        require_llm_provider("anthropic/claude-sonnet-4-6")


def test_require_llm_provider_allows_other_provider(monkeypatch):
    monkeypatch.setenv(OUT_OF_BUDGET_ENV, "anthropic")

    require_llm_provider("openai/gpt-4o-mini")


def test_require_llm_provider_safely_matches_unknown_provider(monkeypatch):
    monkeypatch.setenv(OUT_OF_BUDGET_ENV, "anthropic,aws_bedrock")

    with pytest.raises(pytest.skip.Exception, match="aws_bedrock provider"):
        require_llm_provider("aws_bedrock/model-used-by-another-repository")
