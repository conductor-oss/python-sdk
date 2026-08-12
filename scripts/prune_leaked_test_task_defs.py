#!/usr/bin/env python3
"""Delete task definitions left behind by integration-test runs.

The integration suites register per-run task defs (``sync_basic_<run id>``,
``async_lease_heartbeat_task_<run id>``, ...) and, before the tearDownClass
cleanup was added, never removed them. On a shared server those accumulate
until the account hits its Task Definitions cap, at which point every
registration answers::

    402 System has reached the maximum allowed Task Definitions limit of 1000.

and the integration jobs fail on unrelated branches. This prunes the
leftovers so the cap has room again.

Dry run by default — it prints what it would delete and exits. Pass --delete
to actually remove them. Reads the usual CONDUCTOR_SERVER_URL /
CONDUCTOR_AUTH_KEY / CONDUCTOR_AUTH_SECRET environment.

    python scripts/prune_leaked_test_task_defs.py             # list matches
    python scripts/prune_leaked_test_task_defs.py --delete    # remove them
"""

import argparse
import re
import sys

from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient

# Prefixes owned by the integration suites, each followed by a per-run id.
# Only names matching one of these AND ending in a run id are touched, so a
# hand-registered or production task def is never a candidate.
TEST_PREFIXES = (
    # tests/integration/test_comprehensive_e2e.py
    "sync_basic_",
    "async_basic_",
    "complex_schema_",
    "task_in_progress_",
    "failing_task_",
    # tests/integration/test_lease_extension.py
    "lease_heartbeat_task_",
    "lease_no_heartbeat_task_",
    # tests/integration/test_async_lease_extension.py
    "async_lease_heartbeat_task_",
    "async_lease_no_heartbeat_task_",
    "async_lease_fast_with_hb_",
    "async_lease_fast_no_hb_",
    # tests/integration/client/orkes/test_orkes_clients.py (shortuuid suffix)
    "IntegrationTestOrkesClientsTask_",
)

# uuid4().hex[:8] for most suites; shortuuid for test_orkes_clients.
RUN_ID = re.compile(r"^(?:[0-9a-f]{8}|[0-9A-Za-z]{20,25})$")


def is_leaked(name):
    for prefix in TEST_PREFIXES:
        if name.startswith(prefix) and RUN_ID.match(name[len(prefix):]):
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--delete",
        action="store_true",
        help="actually unregister the matches (default: dry run)",
    )
    args = parser.parse_args()

    config = Configuration()
    client = OrkesMetadataClient(config)

    all_defs = client.get_all_task_defs()
    leaked = sorted(d.name for d in all_defs if is_leaked(d.name))

    print(f"server:          {config.host}")
    print(f"task defs total: {len(all_defs)}")
    print(f"test leftovers:  {len(leaked)}")

    if not leaked:
        return 0

    if not args.delete:
        for name in leaked:
            print(f"  would delete {name}")
        print("\nDry run — re-run with --delete to remove these.")
        return 0

    failed = 0
    for name in leaked:
        try:
            client.unregister_task_def(name)
            print(f"  deleted {name}")
        except Exception as e:
            failed += 1
            print(f"  FAILED  {name}: {e}", file=sys.stderr)

    print(f"\ndeleted {len(leaked) - failed} of {len(leaked)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
