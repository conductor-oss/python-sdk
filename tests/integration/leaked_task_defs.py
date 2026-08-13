"""Recognise and reclaim task definitions left behind by integration runs.

The integration suites register per-run task defs
(``sync_basic_<run id>``, ``async_lease_heartbeat_task_<run id>``, ...). Until
the ``tearDownClass`` cleanup landed, every run left its own behind, and on the
shared server they accumulated until the account hit its cap::

    402 System has reached the maximum allowed Task Definitions limit of 1000.

At that point registration fails for every branch, so unrelated PRs go red.
Cleanup on teardown stops the leak; this module reclaims what earlier runs
already leaked, and is also what ``scripts/prune_leaked_test_task_defs.py``
matches on.
"""

import logging
import os
import re
import time

logger = logging.getLogger(__name__)

# Prefixes owned by the integration suites, each followed by a per-run id.
# A name is only a candidate if it matches one of these AND ends in a run id,
# so a hand-registered or production task def is never touched.
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
_RUN_ID = re.compile(r"^(?:[0-9a-f]{8}|[0-9A-Za-z]{20,25})$")

# Four integration jobs run in parallel, and other PRs run at the same time.
# Only defs older than this are reclaimed, so a concurrent run never has the
# task def it is mid-test on deleted from under it.
STALE_AFTER_SECONDS = 2 * 60 * 60


def is_leaked_task_def(name):
    """True if ``name`` is a per-run task def owned by the integration suites."""
    for prefix in TEST_PREFIXES:
        if name.startswith(prefix) and _RUN_ID.match(name[len(prefix):]):
            return True
    return False


def stale_leaked_task_defs(task_defs, now=None):
    """Names in ``task_defs`` that are leaked AND older than STALE_AFTER_SECONDS.

    A def with no ``create_time`` is left alone: without an age there is no way
    to tell it from one a concurrent run just registered.
    """
    cutoff_ms = ((now if now is not None else time.time()) - STALE_AFTER_SECONDS) * 1000
    return sorted(
        d.name
        for d in task_defs
        if is_leaked_task_def(d.name) and (d.create_time or 0) and d.create_time < cutoff_ms
    )


def reclaim_task_def_quota(config):
    """Delete stale leaked task defs so registration has room again.

    Best-effort and never raises: this runs before the suites do, and a server
    that will not answer is the tests' problem to report, not this helper's.
    Returns the number deleted. Set CONDUCTOR_SKIP_TASK_DEF_RECLAIM=1 to skip.
    """
    if os.environ.get("CONDUCTOR_SKIP_TASK_DEF_RECLAIM"):
        return 0

    from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient

    client = OrkesMetadataClient(config)
    try:
        all_defs = client.get_all_task_defs()
    except Exception as e:
        logger.warning("reclaim: could not list task defs: %s", e)
        return 0

    stale = stale_leaked_task_defs(all_defs)
    if not stale:
        return 0

    deleted = 0
    for name in stale:
        try:
            client.unregister_task_def(name)
            deleted += 1
        except Exception as e:
            logger.warning("reclaim: could not unregister %s: %s", name, e)

    # print(), not logger: logging is not configured yet at session start.
    print(
        f"reclaimed {deleted} of {len(stale)} stale test task defs "
        f"({len(all_defs)} defs on {config.host} before pruning)"
    )
    return deleted
