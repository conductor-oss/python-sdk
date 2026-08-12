#!/usr/bin/env python3
"""Delete task definitions left behind by integration-test runs.

The integration suites register per-run task defs (``sync_basic_<run id>``,
``async_lease_heartbeat_task_<run id>``, ...) and, before the tearDownClass
cleanup was added, never removed them. On a shared server those accumulate
until the account hits its Task Definitions cap, at which point every
registration answers::

    402 System has reached the maximum allowed Task Definitions limit of 1000.

and the integration jobs fail on unrelated branches.

The suites now prune stale leftovers themselves at session start (see
tests/integration/leaked_task_defs.py), so this script is for pruning by hand
— including the defs too recent for the automatic pass to touch.

Dry run by default: it prints what it would delete and exits. Pass --delete to
actually remove them. Reads the usual CONDUCTOR_SERVER_URL /
CONDUCTOR_AUTH_KEY / CONDUCTOR_AUTH_SECRET environment.

    python scripts/prune_leaked_test_task_defs.py             # list matches
    python scripts/prune_leaked_test_task_defs.py --delete    # remove them
"""

import argparse
import sys

from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
from tests.integration.leaked_task_defs import (
    STALE_AFTER_SECONDS,
    is_leaked_task_def,
    stale_leaked_task_defs,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--delete",
        action="store_true",
        help="actually unregister the matches (default: dry run)",
    )
    parser.add_argument(
        "--include-recent",
        action="store_true",
        help=(
            "also prune defs newer than "
            f"{STALE_AFTER_SECONDS // 3600}h — only safe when no integration "
            "run is in flight, since a concurrent run's defs are fair game"
        ),
    )
    args = parser.parse_args()

    config = Configuration()
    client = OrkesMetadataClient(config)

    all_defs = client.get_all_task_defs()
    if args.include_recent:
        leaked = sorted(d.name for d in all_defs if is_leaked_task_def(d.name))
    else:
        leaked = stale_leaked_task_defs(all_defs)

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
