"""
Factory that selects the correct MetricsCollector implementation based on
environment variables.

  WORKER_CANONICAL_METRICS=true  ->  CanonicalMetricsCollector
  (unset / any other value)      ->  LegacyMetricsCollector  (default during deprecation)

WORKER_LEGACY_METRICS is reserved for future use.  After the deprecation
period ends and canonical becomes the default, setting WORKER_LEGACY_METRICS=true
will allow opting back into legacy metrics.  It is not currently read.
"""

import logging
import os

from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.telemetry.metrics_collector_base import MetricsCollectorBase

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(__name__)
)


def create_metrics_collector(settings: MetricsSettings) -> MetricsCollectorBase:
    """
    Create the metrics collector indicated by ``settings.is_canonical``.

    ``MetricsSettings`` reads ``WORKER_CANONICAL_METRICS`` at construction
    time, so the directory and collector type are already determined.

    Returns a fully-initialised collector (legacy or canonical) that satisfies
    the MetricsCollector Protocol and can be registered as an event listener.

    This is non-destructive: it only ensures the directory exists.  It never
    deletes ``.db`` files, because it runs in every spawned worker and a worker
    must not wipe metrics belonging to live sibling processes.  Directory
    cleanup is owned by the parent via
    ``MetricsSettings.clean_metrics_directory()`` (invoked once by
    ``TaskHandler`` before workers spawn).
    """
    metrics_dir = settings.metrics_directory
    os.makedirs(metrics_dir, exist_ok=True)

    if settings.is_canonical:
        from conductor.client.telemetry.canonical_metrics_collector import CanonicalMetricsCollector
        logger.info("WORKER_CANONICAL_METRICS is true — using CanonicalMetricsCollector (dir=%s)", metrics_dir)
        return CanonicalMetricsCollector(settings)

    from conductor.client.telemetry.legacy_metrics_collector import LegacyMetricsCollector
    logger.info("Using LegacyMetricsCollector (dir=%s; set WORKER_CANONICAL_METRICS=true for canonical)", metrics_dir)
    return LegacyMetricsCollector(settings)


def create_metrics_collector_for_parent(settings: MetricsSettings) -> MetricsCollectorBase:
    """Owner/parent entrypoint: prepare the shared metrics directory, then build
    the collector.

    Use this from the process that owns the metrics lifecycle (the one that
    spawns workers, and that may itself collect metrics before spawning). It
    cleans the directory up front -- honoring ``settings.clean_directory`` /
    ``settings.clean_dead_pids`` -- so the parent's own first write is not
    orphaned, then delegates to ``create_metrics_collector``.

    Do NOT call this from a spawned worker: workers must use
    ``create_metrics_collector`` (non-destructive) so they can never wipe ``.db``
    files belonging to live sibling processes. ``clean_metrics_directory()`` is
    idempotent per process, so a later ``TaskHandler`` call is a no-op.
    """
    settings.clean_metrics_directory()
    return create_metrics_collector(settings)
