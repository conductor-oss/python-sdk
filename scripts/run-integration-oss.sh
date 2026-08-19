#!/usr/bin/env bash
#
# Spin up a local Conductor OSS stack and run the SDK integration suite
# against it, mirroring the `integration-tests-oss` job in
# .github/workflows/pull_request.yml. Orkes-Enterprise-only tests/classes/
# modules (Authorization, Secrets, Schema, Service Registry, Signal API,
# metadata/scheduler tags) check `os.environ.get('CONDUCTOR_SERVER_TYPE')`
# directly and skip themselves when it's "oss" (confirmed empirically not
# implemented by plain OSS Conductor -- see the individual test files for
# details on each gap).
#
# The stack (Conductor OSS + Postgres + httpbin) is defined in
# scripts/docker-compose-oss.yaml and is torn down automatically on exit.
#
# Usage:
#   scripts/run-integration-oss.sh [--keep-up] [--version <tag>] [-- pytest args]
# Examples:
#   scripts/run-integration-oss.sh                        # run scripts/run_integration_tests.sh --bucket=core against `latest`
#   scripts/run-integration-oss.sh --version 3.32.0-rc18
#   scripts/run-integration-oss.sh --keep-up
#   scripts/run-integration-oss.sh -- --bucket=all
set -euo pipefail

KEEP_UP=0
extra=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep-up) KEEP_UP=1; shift ;;
    --version) OSS_CONDUCTOR_VERSION="${2:?--version needs a tag}"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--keep-up] [--version <tag>] [-- pytest args]"
      exit 0
      ;;
    --) shift; extra=("$@"); break ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

export OSS_CONDUCTOR_VERSION="${OSS_CONDUCTOR_VERSION:-latest}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose-oss.yaml"
cd "${REPO_ROOT}"

compose() { docker compose -f "${COMPOSE_FILE}" "$@"; }

cleanup() {
  if [[ "${KEEP_UP}" == "1" ]]; then
    echo "--keep-up set: leaving the OSS stack running. Tear down with:"
    echo "  docker compose -f ${COMPOSE_FILE} down -v"
    return
  fi
  echo "Tearing down Conductor OSS stack..."
  compose down -v || true
}
trap cleanup EXIT

echo "Starting Conductor OSS stack (conductoross/conductor:${OSS_CONDUCTOR_VERSION})..."
compose up -d

echo "Waiting for Conductor to be healthy..."
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-180}"
deadline=$(( SECONDS + HEALTH_TIMEOUT ))
until curl -sf http://localhost:8080/health >/dev/null 2>&1; do
  if (( SECONDS >= deadline )); then
    echo "Error: Conductor did not become healthy within ${HEALTH_TIMEOUT}s." >&2
    compose logs conductor-server || true
    exit 1
  fi
  sleep 5
done
echo "Conductor is up."

export CONDUCTOR_SERVER_URL="http://localhost:8080/api"
export CONDUCTOR_SERVER_TYPE="oss"

bash scripts/run_integration_tests.sh ${extra[@]+"${extra[@]}"}
