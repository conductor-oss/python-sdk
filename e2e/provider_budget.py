"""Helpers for skipping E2E calls to providers with exhausted budgets."""

import os

import pytest


OUT_OF_BUDGET_ENV = "LLM_PROVIDERS_OUT_OF_BUDGET"


def provider_from_model(model_or_provider: str) -> str:
    """Return the provider name from either ``provider/model`` or a model name."""
    value = model_or_provider.strip().lower()
    if "/" in value:
        return value.split("/", 1)[0]
    if value.startswith("claude"):
        return "anthropic"
    if value.startswith(("gpt-", "o1", "o3", "o4")):
        return "openai"
    return value


def out_of_budget_providers(raw_value: str | None = None) -> set[str]:
    """Parse the comma-separated provider circuit breaker."""
    value = os.environ.get(OUT_OF_BUDGET_ENV, "") if raw_value is None else raw_value
    return {
        provider_from_model(provider)
        for provider in value.split(",")
        if provider.strip()
    }


def require_llm_provider(model_or_provider: str) -> None:
    """Skip the current test when its LLM provider is marked out of budget."""
    provider = provider_from_model(model_or_provider)
    if provider in out_of_budget_providers():
        pytest.skip(
            f"{provider} provider is marked out of budget by {OUT_OF_BUDGET_ENV}"
        )
