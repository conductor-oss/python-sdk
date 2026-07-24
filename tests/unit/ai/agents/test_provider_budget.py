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
        ("azureopenai/gpt-4o-mini", "azure_openai"),
        ("azure_openai/gpt-4o-mini", "azure_openai"),
        ("gemini/gemini-2.5-flash", "google_gemini"),
        ("google_gemini/gemini-2.5-flash", "google_gemini"),
        ("vertex_ai/gemini-2.5-flash", "google_vertex_ai"),
        ("google_vertex_ai/gemini-2.5-flash", "google_vertex_ai"),
        ("bedrock/us.anthropic.claude-haiku-4-5", "aws_bedrock"),
        ("aws_bedrock/us.anthropic.claude-haiku-4-5", "aws_bedrock"),
        ("cohere/command-a-vision-07-2025", "cohere"),
        ("grok/grok-4.5", "grok"),
        ("xai/grok-4.5", "grok"),
        ("perplexity/sonar", "perplexity"),
        ("mistral/pixtral-large", "mistral"),
        ("huggingface/model", "hugging_face"),
        ("hugging_face/model", "hugging_face"),
        ("stability/model", "stability"),
    ],
)
def test_provider_from_model(value, expected):
    assert provider_from_model(value) == expected


def test_out_of_budget_providers_parses_multiple_values():
    assert out_of_budget_providers(" Anthropic, OPENAI ,, ") == {
        "anthropic",
        "openai",
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
