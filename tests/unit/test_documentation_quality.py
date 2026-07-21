"""Guard the README shape and public Conductor-agent documentation terminology."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
README_SECTIONS = [
    "Choose your path",
    "Choose your Conductor server",
    "Why Conductor?",
    "Requirements and compatibility",
    "Install the SDK",
    "AI agent quickstart",
    "Workflow and worker quickstart",
    "Common tasks",
    "Troubleshooting",
    "Support and project policies",
    "License",
]
PRIMARY_GUIDES = [
    "docs/agents/concepts/agents.md",
    "docs/agents/concepts/tools.md",
    "docs/agents/concepts/multi-agent.md",
    "docs/agents/concepts/guardrails.md",
    "docs/agents/concepts/deploy-serve-run.md",
    "docs/agents/concepts/streaming-hitl.md",
    "docs/agents/reference/runtime.md",
    "docs/agents/reference/client.md",
]


def test_readme_mirrors_the_java_sdk_information_architecture():
    headings = re.findall(r"^## (.+)$", (ROOT / "README.md").read_text(), re.MULTILINE)
    positions = [headings.index(section) for section in README_SECTIONS]
    assert positions == sorted(positions)
    readme = (ROOT / "README.md").read_text()
    assert "conductor-oss/python-sdk" in readme
    assert "CONDUCTOR_AGENT_LLM_MODEL" in readme
    assert "AGENTSPAN" not in readme


def test_primary_agent_guides_include_navigation_and_outcome_sections():
    for relative_path in PRIMARY_GUIDES:
        content = (ROOT / relative_path).read_text()
        assert "## Prerequisites" in content, relative_path
        assert "## Expected result" in content or "## Expected result and" in content, relative_path
        assert "## Next steps" in content or "## Cleanup and next steps" in content or "## Expected result and next steps" in content, relative_path


def test_public_documentation_and_examples_do_not_use_legacy_branding():
    paths = [ROOT / "README.md", *[p for p in (ROOT / "docs").rglob("*.md") if "docs/design" not in str(p)]]
    paths.extend((ROOT / "examples" / "agents").rglob("*.md"))
    paths.extend((ROOT / "examples" / "agents").rglob("*.py"))
    violations = []
    for path in paths:
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            if "copyright" in line.lower():
                continue
            if re.search(r"agentspan|agent span", line, re.IGNORECASE):
                violations.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")
    assert not violations, "Legacy branding remains:\n" + "\n".join(violations)
