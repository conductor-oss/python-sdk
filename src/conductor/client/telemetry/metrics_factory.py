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


_CANONICAL_SUBDIR = "canonical"


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name, "")
    if not value:
        return default
    return value.strip().lower() in ("true", "1", "yes")


_cleaned_directories: set = set()


def resolve_metrics_type(settings: MetricsSettings) -> None:
    """Read ``WORKER_CANONICAL_METRICS`` once and store the result on *settings*.

    Idempotent -- subsequent calls are no-ops.  Must be called before
    ``settings.metrics_directory`` is read so that the subdirectory is
    resolved in the main process before any child processes are forked.

    Both ``TaskHandler.__init__`` and ``create_metrics_collector`` call this.
    """
    if settings._subdir is not None:
        return
    if _env_bool("WORKER_CANONICAL_METRICS", default=False):
        settings._subdir = _CANONICAL_SUBDIR
    else:
        settings._subdir = ""


def create_metrics_collector(settings: MetricsSettings) -> MetricsCollectorBase:
    """
    Create the metrics collector selected by environment variables.

    Calls ``resolve_metrics_type`` to ensure ``settings.metrics_directory``
    returns the correct path, then instantiates the appropriate collector.

    Returns a fully-initialised collector (legacy or canonical) that satisfies
    the MetricsCollector Protocol and can be registered as an event listener.
    """
    resolve_metrics_type(settings)

    metrics_dir = settings.metrics_directory
    os.makedirs(metrics_dir, exist_ok=True)

    if metrics_dir not in _cleaned_directories:
        _cleaned_directories.add(metrics_dir)
        if settings.clean_directory:
            settings._clean_stale_db_files()
        if settings.clean_dead_pids:
            settings._clean_dead_pid_files()

    if settings._subdir == _CANONICAL_SUBDIR:
        from conductor.client.telemetry.canonical_metrics_collector import CanonicalMetricsCollector
        logger.info("WORKER_CANONICAL_METRICS is true — using CanonicalMetricsCollector (dir=%s)", metrics_dir)
        return CanonicalMetricsCollector(settings)

    from conductor.client.telemetry.legacy_metrics_collector import LegacyMetricsCollector
    logger.info("Using LegacyMetricsCollector (dir=%s; set WORKER_CANONICAL_METRICS=true for canonical)", metrics_dir)
    return LegacyMetricsCollector(settings)
