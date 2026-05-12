"""
Factory that selects the correct MetricsCollector implementation based on
environment variables.

  WORKER_CANONICAL_METRICS=true  ->  CanonicalMetricsCollector
  WORKER_LEGACY_METRICS=true     ->  LegacyMetricsCollector  (default during deprecation)

If WORKER_CANONICAL_METRICS is true it takes priority regardless of the value
of WORKER_LEGACY_METRICS.
"""

import logging
import os

from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.telemetry.metrics_collector_base import MetricsCollectorBase

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(__name__)
)


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name, "")
    if not value:
        return default
    return value.strip().lower() in ("true", "1", "yes")


def create_metrics_collector(settings: MetricsSettings) -> MetricsCollectorBase:
    """
    Create the metrics collector selected by environment variables.

    Sets ``settings.collector_subdir`` to ``"legacy"`` or ``"canonical"`` so
    that ``settings.metrics_directory`` resolves to a type-specific
    subdirectory.  This is idempotent: calling the factory more than once on
    the same *settings* object (e.g. once in the main process and again in
    each forked worker) always produces the same directory.

    Returns a fully-initialised collector (legacy or canonical) that satisfies
    the MetricsCollector Protocol and can be registered as an event listener.
    """
    collector_type = "canonical" if _env_bool("WORKER_CANONICAL_METRICS", default=False) else "legacy"

    settings.collector_subdir = collector_type
    os.makedirs(settings.metrics_directory, exist_ok=True)

    is_owner = settings._owner_pid is None or os.getpid() == settings._owner_pid
    if is_owner:
        settings._owner_pid = os.getpid()
        if settings.clean_directory:
            settings._clean_stale_db_files()
        if settings.clean_dead_pids:
            settings._clean_dead_pid_files()

    if collector_type == "canonical":
        from conductor.client.telemetry.canonical_metrics_collector import CanonicalMetricsCollector
        logger.info("WORKER_CANONICAL_METRICS is true — using CanonicalMetricsCollector (dir=%s)", settings.metrics_directory)
        return CanonicalMetricsCollector(settings)

    from conductor.client.telemetry.legacy_metrics_collector import LegacyMetricsCollector
    logger.info("Using LegacyMetricsCollector (dir=%s; set WORKER_CANONICAL_METRICS=true for canonical)", settings.metrics_directory)
    return LegacyMetricsCollector(settings)
