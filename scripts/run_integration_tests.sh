#!/usr/bin/env bash
#
# Run the SDK integration test suite locally, mirroring the `integration-test`
# job in .github/workflows/pull_request.yml.
#
# The AI/agentic integration tests are excluded on purpose: they target a
# dedicated AI-enabled server (test_ai_task_types.py and test_ai_examples.py
# hardcode http://localhost:7001/api, and test_agentic_workflows.py needs an
# `openai` LLM provider configured on the server), so they don't run against
# the standard test server this suite targets.
#
# The performance test (test_update_task_v2_perf.py) is also excluded by
# default: it submits ~1000 workflows and takes several minutes. Pass
# --with-perf to include it.
#
# Server connection is read from the environment (see
# src/conductor/client/configuration/configuration.py):
#   CONDUCTOR_SERVER_URL   (required; defaults to http://localhost:8080/api)
#   CONDUCTOR_AUTH_KEY     (optional; needed for Orkes/authenticated servers)
#   CONDUCTOR_AUTH_SECRET  (optional; needed for Orkes/authenticated servers)
#
# Usage:
#   export CONDUCTOR_SERVER_URL="http://localhost:8080/api"
#   ./scripts/run_integration_tests.sh
#   ./scripts/run_integration_tests.sh --with-perf   # also run the perf test
#
# Any other arguments are passed straight through to pytest, which is handy for
# targeting a subset of tests or getting more detail on failures:
#
#   # run a subset (by keyword or path) with live output
#   ./scripts/run_integration_tests.sh -s -k lease
#   ./scripts/run_integration_tests.sh tests/integration/test_lease_extension.py
#
#   # short tracebacks + a one-line reason for every failure/skip, with live logs
#   ./scripts/run_integration_tests.sh -ra --tb=short --log-cli-level=INFO
#
#   # stop at the first failure instead of waiting for the whole suite
#   ./scripts/run_integration_tests.sh -x --tb=long
#
#   # re-run just specific tests, e.g. the ones that failed
#   ./scripts/run_integration_tests.sh -s -k "upsert_group or create_role"
#
#   # show the 15 slowest tests (setup/call/teardown timings) after the run
#   ./scripts/run_integration_tests.sh --durations=15

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# The perf test is skipped by default; --with-perf opts back in.
perf_ignore=(--ignore=tests/integration/test_update_task_v2_perf.py)
pytest_args=()
for arg in "$@"; do
  if [[ "$arg" == "--with-perf" ]]; then
    perf_ignore=()
  else
    pytest_args+=("$arg")
  fi
done

# Note: the "${arr[@]+"${arr[@]}"}" form is required so empty arrays don't trip
# "unbound variable" under `set -u` on bash 3.2 (the default macOS bash).
exec python3 -m pytest tests/integration -v \
  --ignore=tests/integration/test_ai_task_types.py \
  --ignore=tests/integration/test_ai_examples.py \
  --ignore=tests/integration/test_agentic_workflows.py \
  ${perf_ignore[@]+"${perf_ignore[@]}"} \
  ${pytest_args[@]+"${pytest_args[@]}"}
