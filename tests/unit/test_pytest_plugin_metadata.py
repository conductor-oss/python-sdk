"""Ensure pytest auto-loads the Conductor-agent plugin exactly once."""

from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_agent_pytest_plugin_has_one_canonical_entry_point():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    plugins = pyproject["tool"]["poetry"]["plugins"]["pytest11"]
    assert plugins == {
        "conductor-agents-testing": "conductor.ai.agents.testing.pytest_plugin"
    }
