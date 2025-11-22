#!/bin/bash

# Script to run all example scripts in the examples folder
# Each example is run with a timeout to prevent hanging

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default timeout (seconds)
TIMEOUT=${TIMEOUT:-30}

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Examples that require credentials (will expect failures)
REQUIRES_AUTH=(
    "kitchensink.py"
    "dynamic_workflow.py"
    "test_workflows.py"
    "workflow_ops.py"
    "workflow_status_listner.py"
)

# Examples that are workers (need to be killed after timeout)
WORKER_EXAMPLES=(
    "async_worker_example.py"
    "asyncio_workers.py"
    "multiprocessing_workers.py"
    "task_workers.py"
    "shell_worker.py"
    "worker_configuration_example.py"
    "worker_discovery_example.py"
    "worker_discovery_sync_async_example.py"
)

# Examples to skip (if any)
SKIP_EXAMPLES=(
    "__init__.py"
    "untrusted_host.py"  # Requires specific SSL setup
)

function is_in_array() {
    local needle="$1"
    shift
    local haystack=("$@")
    for item in "${haystack[@]}"; do
        if [[ "$item" == "$needle" ]]; then
            return 0
        fi
    done
    return 1
}

function run_example() {
    local example="$1"
    local requires_auth=false
    local is_worker=false

    if is_in_array "$example" "${REQUIRES_AUTH[@]}"; then
        requires_auth=true
    fi

    if is_in_array "$example" "${WORKER_EXAMPLES[@]}"; then
        is_worker=true
    fi

    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}Running: $example${NC}"
    if $requires_auth; then
        echo -e "${YELLOW}  (Expects auth credentials - may fail)${NC}"
    fi
    if $is_worker; then
        echo -e "${YELLOW}  (Worker process - will timeout after ${TIMEOUT}s)${NC}"
    fi
    echo -e "${BLUE}================================================${NC}"

    if $is_worker; then
        # Run worker examples with timeout
        timeout $TIMEOUT python3 "$example" 2>&1 || {
            exit_code=$?
            if [ $exit_code -eq 124 ]; then
                echo -e "${GREEN}✓ Worker ran for ${TIMEOUT}s (timeout expected)${NC}"
                return 0
            else
                echo -e "${RED}✗ Worker failed with exit code $exit_code${NC}"
                return 1
            fi
        }
    else
        # Run regular examples
        if python3 "$example" 2>&1; then
            echo -e "${GREEN}✓ Success${NC}"
            return 0
        else
            exit_code=$?
            if $requires_auth && [[ $exit_code -ne 0 ]]; then
                echo -e "${YELLOW}⚠ Failed (expected - requires auth)${NC}"
                return 0
            else
                echo -e "${RED}✗ Failed with exit code $exit_code${NC}"
                return 1
            fi
        fi
    fi

    echo ""
}

# Track results
total=0
passed=0
failed=0
skipped=0

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Running Conductor Python SDK Examples${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Run all Python files in examples directory
for example in *.py; do
    # Skip if in skip list
    if is_in_array "$example" "${SKIP_EXAMPLES[@]}"; then
        echo -e "${YELLOW}⊘ Skipping: $example${NC}"
        ((skipped++))
        continue
    fi

    ((total++))

    if run_example "$example"; then
        ((passed++))
    else
        ((failed++))
    fi
done

# Summary
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "Total:   $total"
echo -e "${GREEN}Passed:  $passed${NC}"
if [ $failed -gt 0 ]; then
    echo -e "${RED}Failed:  $failed${NC}"
else
    echo -e "Failed:  $failed"
fi
if [ $skipped -gt 0 ]; then
    echo -e "${YELLOW}Skipped: $skipped${NC}"
fi
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}All examples completed successfully!${NC}"
    exit 0
else
    echo -e "${RED}Some examples failed.${NC}"
    exit 1
fi
