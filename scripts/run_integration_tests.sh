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
# Buckets (--bucket=<name>): the slowest tests are split into their own buckets
# so they can run as separate parallel CI jobs and are skipped by default
# locally. Each slow bucket is path-scoped so it only imports its own module.
#   core        (default) everything except the slow buckets below
#   long-sync   sync lease-extension tests   (test_lease_extension.py, ~90s)
#   long-async  async lease-extension tests  (test_async_lease_extension.py, ~90s)
#   test-all    aggregate workflow-client test_all (test_workflow_client_intg.py, ~83s)
#   all         the full suite (no bucket filtering) — for a complete local run
#
#   ./scripts/run_integration_tests.sh                  # fast: skips slow buckets
#   ./scripts/run_integration_tests.sh --bucket=long-sync
#   ./scripts/run_integration_tests.sh --bucket=all     # run everything
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

# Slow-test files that get their own buckets / CI jobs (see --bucket above).
LEASE_SYNC=tests/integration/test_lease_extension.py
LEASE_ASYNC=tests/integration/test_async_lease_extension.py
TEST_ALL_FILE=tests/integration/test_workflow_client_intg.py

# The perf test is skipped by default; --with-perf opts back in.
perf_ignore=(--ignore=tests/integration/test_update_task_v2_perf.py)
bucket="core"
pytest_args=()
for arg in "$@"; do
  case "$arg" in
    --with-perf) perf_ignore=() ;;
    --bucket=*)  bucket="${arg#*=}" ;;
    *)           pytest_args+=("$arg") ;;
  esac
done

# The AI/agentic tests always target a dedicated server (see header) and are
# never part of these buckets.
ai_ignore=(
  --ignore=tests/integration/test_ai_task_types.py
  --ignore=tests/integration/test_ai_examples.py
  --ignore=tests/integration/test_agentic_workflows.py
)

# Build the target paths + selection for the chosen bucket. The slow buckets are
# path-scoped so each job only imports its own module: this keeps
# scan_for_annotated_workers from starting unrelated workers and lets the four
# buckets run in parallel against one server without stealing each other's tasks.
case "$bucket" in
  core)
    targets=(tests/integration)
    select=("${ai_ignore[@]}" ${perf_ignore[@]+"${perf_ignore[@]}"} \
      --ignore="$LEASE_SYNC" --ignore="$LEASE_ASYNC" --ignore="$TEST_ALL_FILE")
    ;;
  all)
    targets=(tests/integration)
    select=("${ai_ignore[@]}" ${perf_ignore[@]+"${perf_ignore[@]}"})
    ;;
  # The slow buckets below target a single specific file, so the perf test is
  # never in scope and perf_ignore is unnecessary here. This also means
  # --with-perf has no effect on these buckets; the perf test is only reachable
  # via the core/all buckets.
  long-sync)
    targets=("$LEASE_SYNC")
    select=(-m slow_sync)
    ;;
  long-async)
    targets=("$LEASE_ASYNC")
    select=(-m slow_async)
    ;;
  test-all)
    targets=("$TEST_ALL_FILE")
    select=(-m slow_test_all)
    ;;
  *)
    echo "Unknown --bucket='$bucket' (expected: core, long-sync, long-async, test-all, all)" >&2
    exit 2
    ;;
esac

# Note: the "${arr[@]+"${arr[@]}"}" form is required so empty arrays don't trip
# "unbound variable" under `set -u` on bash 3.2 (the default macOS bash).
exec python3 -m pytest -v \
  "${targets[@]}" \
  ${select[@]+"${select[@]}"} \
  ${pytest_args[@]+"${pytest_args[@]}"}
