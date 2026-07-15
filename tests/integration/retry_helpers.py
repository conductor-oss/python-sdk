"""Shared transient-retry / flakiness helpers for the integration suites.

Originally scoped to the aggregate ``test_all`` bucket, this module is now the
single home for the retry/poll primitives shared across the integration tests:
``is_transient`` (the one definition of "transient transport blip"),
``TERMINAL_WORKFLOW_STATES``, the per-request ``retry_on_transient``, and the
scenario-level ``retry_scenario``.

The suites run against a shared dev server whose transport occasionally blips
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

# Canonical set of terminal workflow statuses, shared by the poll-to-terminal
# helpers across the integration suites so the set can't drift file to file.
TERMINAL_WORKFLOW_STATES = ('COMPLETED', 'FAILED', 'TIMED_OUT', 'TERMINATED')


def is_transient(exc):
    """True when ``exc`` is a transient transport blip against the shared dev
    server (read timeout, connection reset, HTTP/2 GOAWAY, stale keep-alive)
    rather than a real failure. status 0/None means no HTTP response arrived.
    """
    return isinstance(exc, ApiException) and (
        getattr(exc, 'transient', False) or exc.status in (0, None))


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
        if is_transient(cur):
            return cur
        cur = cur.__cause__ or cur.__context__
    return None


def retry_on_transient(func, *args, retries=4, base_delay=1, **kwargs):
    """Retry ``func(*args, **kwargs)`` on a transient (status 0) transport blip
    with capped-free exponential backoff. Non-transient errors (real 4xx/5xx,
    assertion failures) raise immediately.

    This is *per-request* retry, suited to idempotent calls (get/register).
    For non-idempotent scenarios (start_workflow, signal) use ``retry_scenario``,
    which re-runs the whole scenario from scratch instead.
    """
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except ApiException as e:
            if is_transient(e) and attempt < retries - 1:
                logger.warning(
                    'transient (%s) API error (attempt %d/%d): %s; retrying',
                    e.status, attempt + 1, retries, e)
                time.sleep(base_delay * (2 ** attempt))
                continue
            raise


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


def wait_for_workflow_terminal(
        client, workflow_id, *,
        timeout_seconds=None, deadline=None, poll_interval=2,
        include_tasks=False, terminal_states=TERMINAL_WORKFLOW_STATES,
        is_terminal=None, swallow='transient',
        log=None, on_poll=None, on_giveup=None):
    """Poll ``client.get_workflow(workflow_id, include_tasks=...)`` until the
    workflow reaches a terminal state (or the wall-clock budget is exhausted),
    returning the last observed ``Workflow`` (or ``None`` if it could never be
    fetched). This is the single shared "poll a workflow to terminal" primitive
    for the integration suites — callers wrap it to preserve their own return
    shape / side effects.

    Args:
        client: anything exposing ``get_workflow(workflow_id, include_tasks=...)``
            (both ``OrkesWorkflowClient`` and ``WorkflowExecutor`` qualify).
        timeout_seconds: relative budget; an internal ``time.monotonic()``
            deadline is derived from it. Ignored when ``deadline`` is given.
        deadline: absolute ``time.monotonic()`` value to stop at. When both this
            and ``timeout_seconds`` are ``None`` the workflow is polled exactly
            once (no wait).
        poll_interval: seconds between polls.
        include_tasks: passed through to ``get_workflow``.
        terminal_states: statuses considered terminal (default
            ``TERMINAL_WORKFLOW_STATES``); used by the default predicate.
        is_terminal: optional ``predicate(workflow) -> bool`` overriding the
            default "status in terminal_states" check (e.g. to also gate on an
            expected task count).
        swallow: error policy for a failing poll — ``'transient'`` swallows only
            transient blips (status 0/None) and re-raises real errors;
            ``'all'`` swallows every exception and keeps polling; ``'none'`` lets
            any exception propagate.
        log: optional ``callable(str)`` for progress lines (e.g. ``logger.info``
            or ``print``). Defaults to ``logger.debug``.
        on_poll: optional ``callable(workflow)`` invoked after each successful
            poll, before the terminal check (e.g. to print per-task diagnostics).
        on_giveup: optional ``callable(workflow)`` invoked once when the budget
            is exhausted without reaching terminal (e.g. to dump diagnostics).
    """
    if log is None:
        log = logger.debug
    if is_terminal is None:
        def is_terminal(wf):
            return getattr(wf, 'status', None) in terminal_states
    if deadline is None and timeout_seconds is not None:
        deadline = time.monotonic() + timeout_seconds

    start = time.monotonic()
    workflow = None
    while True:
        try:
            workflow = client.get_workflow(
                workflow_id, include_tasks=include_tasks)
        except Exception as e:
            if swallow == 'none':
                raise
            if swallow == 'transient' and not is_transient(e):
                raise
            log('error polling workflow %s (%.0fs elapsed): %s' % (
                workflow_id, time.monotonic() - start, e))
        else:
            if on_poll is not None:
                on_poll(workflow)
            if is_terminal(workflow):
                log('workflow %s reached %s after %.0fs' % (
                    workflow_id, getattr(workflow, 'status', None),
                    time.monotonic() - start))
                return workflow
        if deadline is None or time.monotonic() >= deadline:
            log('workflow %s still %s after %.0fs; giving up wait' % (
                workflow_id, getattr(workflow, 'status', None),
                time.monotonic() - start))
            if on_giveup is not None:
                on_giveup(workflow)
            return workflow
        log('workflow %s still %s; waiting' % (
            workflow_id, getattr(workflow, 'status', None)))
        time.sleep(poll_interval)
