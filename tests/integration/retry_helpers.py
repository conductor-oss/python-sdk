"""Shared transient-retry helper for the aggregate ``test_all`` integration bucket.

The bucket runs against a shared dev server whose transport occasionally blips
(read timeout, "server disconnected without a response", HTTP/2 GOAWAY, stale
keep-alive) and surfaces as ``ApiException(status=0)``. Those are not real test
failures.

Rather than re-running the whole suite on such a blip, ``test_all`` establishes
a single overall wall-clock deadline once, and each *scenario* is retried on a
transient blip until that deadline passes, with capped exponential backoff. Real
errors (assertion failures, genuine 4xx/5xx) raise immediately.

Scenario-level (rather than per-request) granularity is deliberate: a retried
scenario starts from scratch (fresh workflows, fresh signals), which keeps
otherwise non-idempotent operations — notably ``start_workflow`` and the sync
``signal`` calls whose returned ``SignalResponse`` the tests assert on — safe to
re-run without duplicating side effects against a single workflow instance.
"""

import logging
import time

from conductor.client.http.rest import ApiException

logger = logging.getLogger(__name__)

# Default overall budget for the whole aggregate suite (all sub-suites share it).
DEFAULT_OVERALL_DEADLINE_SECONDS = 600  # 10 minutes

# Backoff bounds between scenario retries.
DEFAULT_BASE_DELAY_SECONDS = 1.0
DEFAULT_MAX_DELAY_SECONDS = 30.0


def first_transient_api_exception(exc):
    """Walk the exception chain (``__cause__`` / ``__context__``) and return the
    first transient ``ApiException`` (flagged transient, or status 0/None), or
    ``None`` if there isn't one.

    Inner test helpers sometimes catch an ApiException and re-raise it as a bare
    ``Exception`` (losing the type), so we can't rely on the outermost exception
    type alone; implicit chaining still records the original on ``__context__``
    (or ``__cause__`` when ``raise ... from`` is used).
    """
    seen = set()
    cur = exc
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        if isinstance(cur, ApiException) and (
                getattr(cur, 'transient', False) or cur.status in (0, None)):
            return cur
        cur = cur.__cause__ or cur.__context__
    return None


def retry_scenario(label, func, *args, deadline=None,
                   base_delay=DEFAULT_BASE_DELAY_SECONDS,
                   max_delay=DEFAULT_MAX_DELAY_SECONDS, **kwargs):
    """Run ``func(*args, **kwargs)``, retrying only on a transient (status 0)
    transport blip until the shared ``deadline`` passes.

    Args:
        label: Human-readable scenario name for logs.
        func: The scenario callable to run.
        deadline: ``time.monotonic()`` value after which we stop retrying. When
            ``None`` (e.g. the standalone ``main.py`` runner), the scenario runs
            exactly once with no transient retry — preserving prior behaviour.
        base_delay / max_delay: capped exponential backoff bounds (seconds).

    Non-transient errors (assertion failures, genuine 4xx/5xx) raise
    immediately. A transient blip at/after the deadline re-raises so the suite
    fails cleanly rather than hanging past the CI job timeout.
    """
    if deadline is None:
        logger.info('running scenario %s (attempt 1, no transient retry)', label)
        return func(*args, **kwargs)

    attempt = 0
    while True:
        logger.info('running scenario %s (attempt %d)', label, attempt + 1)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            transient = first_transient_api_exception(e)
            if transient is None:
                raise
            now = time.monotonic()
            if now >= deadline:
                logger.error(
                    'transient (%s) in %s but overall deadline exceeded by '
                    '%.0fs; giving up: %s',
                    transient.status, label, now - deadline, transient)
                raise
            delay = min(base_delay * (2 ** attempt), max_delay)
            delay = min(delay, max(0.0, deadline - now))
            logger.warning(
                'transient (%s) in %s (attempt %d); retrying in %.1fs '
                '(%.0fs left in overall budget): %s',
                transient.status, label, attempt + 1, delay,
                deadline - now, transient)
            time.sleep(delay)
            attempt += 1
