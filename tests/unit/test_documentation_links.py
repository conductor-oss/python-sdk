"""Validate maintained documentation links and GitHub-style anchors."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LINK_RE = re.compile(r"(?<!!)\[[^]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)

CORE_GUIDES = (
    "api-map", "compatibility", "connection-authentication", "core-quickstart",
    "debugging", "deployment-scaling", "documentation-parity", "documentation-standard",
    "examples", "observability", "reliability", "schedules-events", "schema-client",
    "security", "server-setup", "upgrading", "workers", "workflow-lifecycle",
    "workflow-testing", "workflows",
)
CANONICAL_DOCS = [
    ROOT / "README.md",
    ROOT / "docs" / "README.md",
    *[ROOT / "docs" / f"{name}.md" for name in CORE_GUIDES],
    *sorted((ROOT / "docs" / "agents").rglob("*.md")),
    ROOT / "examples" / "agents" / "README.md",
    ROOT / "examples" / "agents" / "adk" / "README.md",
    ROOT / "examples" / "agents" / "langgraph" / "README.md",
    ROOT / "examples" / "agents" / "openai" / "README.md",
]


def _slug(heading: str) -> str:
    heading = re.sub(r"`", "", heading).lower()
    heading = re.sub(r"[^\w\s-]", "", heading)
    return re.sub(r"[-\s]+", "-", heading).strip("-")


def _anchors(document: Path) -> set[str]:
    counts: dict[str, int] = {}
    anchors: set[str] = set()
    for heading in HEADING_RE.findall(document.read_text()):
        slug = _slug(heading)
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        anchors.add(slug if count == 0 else f"{slug}-{count}")
    return anchors


def _links(document: Path):
    for target in LINK_RE.findall(document.read_text()):
        target = target.strip().strip("<>")
        if not target or "://" in target or target.startswith(("mailto:", "#")):
            yield target
            continue
        yield target


def test_curated_documentation_links_and_anchors_exist():
    failures = []
    for document in CANONICAL_DOCS:
        assert document.exists(), document
        for target in _links(document):
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            path_text, _, anchor = target.partition("#")
            target_document = document if not path_text else (document.parent / path_text).resolve()
            if not target_document.exists():
                failures.append(f"{document.relative_to(ROOT)} -> missing {path_text}")
            elif anchor and target_document.suffix == ".md" and anchor not in _anchors(target_document):
                failures.append(f"{document.relative_to(ROOT)} -> missing anchor #{anchor} in {path_text or document.name}")
    assert not failures, "Broken documentation links:\n" + "\n".join(failures)
