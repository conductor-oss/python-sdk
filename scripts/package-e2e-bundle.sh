#!/usr/bin/env bash
set -euo pipefail

# ── Package the agent e2e suite as a standalone bundle ───────────────────────
# Builds conductor-ai-e2e-python-<version>.tar.gz: a self-contained pytest
# project carrying the agent e2e test sources (repo-root e2e/), pinned to the
# published conductor-python[agents]==<version> package from PyPI (no SDK
# source vendored).
#
# Downstream repos (e.g. orkes-io/orkes-conductor) download the bundle from
# the python-sdk GitHub release and run it against their own server build.
# This replaces the agentspan-sdk-e2e-python-* bundles formerly cut from
# agentspan-ai/agentspan — python-sdk is now the canonical home of these
# suites. Mirrors conductor-oss/java-sdk (conductor-ai-e2e/release/) and
# conductor-oss/javascript-sdk (scripts/).
#
# Usage:
#   ./scripts/package-e2e-bundle.sh --version 2.0.0-rc2 [--out DIR]
#
# Packaging is static (no install, no network) — the pinned version does not
# have to be on PyPI yet, so this can run before the publish job finishes.
# Note: pip normalizes PEP 440 spellings, so pinning ==2.0.0-rc2 resolves the
# PyPI artifact 2.0.0rc2.

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"

VERSION=""
OUT_DIR="$HERE/e2e-bundle-dist"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --out)     OUT_DIR="$2"; shift 2 ;;
    *) echo "ERROR: unknown arg '$1' (want --version X.Y.Z [--out DIR])" >&2; exit 1 ;;
  esac
done

[[ -n "$VERSION" ]] || { echo "ERROR: --version is required" >&2; exit 1; }

NAME="conductor-ai-e2e-python-$VERSION"
STAGE="$OUT_DIR/$NAME"

echo "Packaging agent e2e bundle ($NAME)..."
rm -rf "$STAGE"
mkdir -p "$STAGE"

# Suites import the SDK by package (conductor.ai.agents), so the sources copy
# over verbatim — imports resolve from the installed PyPI package.
cp -R "$REPO_ROOT/e2e" "$STAGE/e2e"

# Deps mirror the repo's agent-e2e.yml install step, with the editable SDK
# install swapped for the published pin.
cat > "$STAGE/requirements.txt" <<'EOF'
# Pins the published SDK (with the agents extra) to the python-sdk release
# this bundle was cut from.
conductor-python[agents]==@VERSION@

# Test runner + e2e support deps (mirrors .github/workflows/agent-e2e.yml).
pytest
pytest-asyncio
pytest-xdist
pytest-rerunfailures

# Live MCP server used by the MCP tool suites.
mcp-testkit
EOF

cat > "$STAGE/run.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
# Runs the agent e2e suite against a live Conductor server with the agent
# runtime enabled (conductor-oss >= 3.32.0-rc.8, or orkes-conductor with
# agentspan.embedded=true).
#
# Required services (NOT started by this script):
#   - Conductor server → AGENTSPAN_SERVER_URL (default http://localhost:8080/api)
#   - mcp-testkit      → MCP_TESTKIT_URL      (default http://localhost:3001)
# Optional:
#   - AGENTSPAN_LLM_MODEL (default openai/gpt-4o-mini); the provider API key
#     must be configured on the SERVER — the suites never read it.
#   - AGENTSPAN_CLI_PATH (default `agentspan` on PATH) — CLI suites skip if absent.
#
# Requires python 3.10–3.13 on PATH as `python` (use a venv; the harness deps
# may not build on newer interpreters). Usage: ./run.sh [extra pytest args]
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
python -m pip install -r requirements.txt
mkdir -p results
python -m pytest e2e/ -v --tb=short -n 3 --dist=loadgroup \
  --junitxml=results/junit-e2e.xml "$@"
python e2e/report_generator.py results/junit-e2e.xml results/report.html || true
echo "Results: $HERE/results/junit-e2e.xml (report.html alongside)"
EOF
chmod +x "$STAGE/run.sh"

cat > "$STAGE/README.md" <<'EOF'
# Conductor Agent SDK (python) — E2E suite @VERSION@

Self-contained end-to-end tests for the Conductor Python agent SDK, pinned to
release **@VERSION@**. Resolves `conductor-python[agents]==@VERSION@` from
PyPI — no SDK source is vendored. Cut from
[conductor-oss/python-sdk](https://github.com/conductor-oss/python-sdk)
(`e2e/`); supersedes the `agentspan-sdk-e2e-python-*` bundles formerly
released from agentspan-ai/agentspan.

## Prerequisites (you provide these)

| Requirement                       | Env var                | Default                     |
|-----------------------------------|------------------------|-----------------------------|
| python 3.10–3.13 (use a venv)     | —                      | —                           |
| Conductor server w/ agent runtime | `AGENTSPAN_SERVER_URL` | `http://localhost:8080/api` |
| LLM model                         | `AGENTSPAN_LLM_MODEL`  | `openai/gpt-4o-mini`        |
| mcp-testkit (MCP suites)          | `MCP_TESTKIT_URL`      | `http://localhost:3001`     |
| agentspan CLI (CLI suites)        | `AGENTSPAN_CLI_PATH`   | `agentspan` (on `PATH`)     |

The server needs the agent runtime: conductor-oss `>= 3.32.0-rc.8`, or
orkes-conductor booted with `agentspan.embedded=true`. LLM provider API keys
(e.g. `OPENAI_API_KEY`) go to the **server** process, not this suite.
Suites that need an absent optional service (CLI, LangGraph) skip rather
than fail.

## Run

```bash
python3.12 -m venv .venv && source .venv/bin/activate
./run.sh                   # full suite
./run.sh -k suite1         # filter, plus any pytest args
```

JUnit XML lands in `results/junit-e2e.xml`, HTML report in
`results/report.html`.

## Testing an unreleased SDK

```bash
pip install /path/to/conductor_python-X.Y.Z-py3-none-any.whl'[agents]'
python -m pytest e2e/ -v --tb=short -n 3 --dist=loadgroup
```
EOF

# Stamp the version everywhere (skip binary assets).
find "$STAGE" -type f ! -name '*.png' ! -name '*.jpg' ! -name '*.jpeg' \
    ! -name '*.gif' ! -name '*.webp' ! -name '*.pdf' -print0 \
  | xargs -0 sed -i.bak "s/@VERSION@/$VERSION/g"
find "$STAGE" -name '*.bak' -delete

mkdir -p "$OUT_DIR"
tar -czf "$OUT_DIR/$NAME.tar.gz" -C "$OUT_DIR" "$NAME"
rm -rf "$STAGE"

echo "OK: $OUT_DIR/$NAME.tar.gz"
