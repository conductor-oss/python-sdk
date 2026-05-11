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

    Appends a collector-type subdirectory (``legacy/`` or ``canonical/``) to
    ``settings.directory`` so that switching implementations never produces
    stale metric names from the previous type.  Cleanup flags on *settings*
    (``clean_directory``, ``clean_dead_pids``) are executed against the final
    subdirectory before the collector is constructed.

    Returns a fully-initialised collector (legacy or canonical) that satisfies
    the MetricsCollector Protocol and can be registered as an event listener.
    """
    collector_type = "canonical" if _env_bool("WORKER_CANONICAL_METRICS", default=False) else "legacy"

    partitioned_dir = os.path.join(settings.directory, collector_type)
    os.makedirs(partitioned_dir, exist_ok=True)
    settings.directory = partitioned_dir

    if settings.clean_directory:
        settings._clean_stale_db_files()
    if settings.clean_dead_pids:
        settings._clean_dead_pid_files()

    if collector_type == "canonical":
        from conductor.client.telemetry.canonical_metrics_collector import CanonicalMetricsCollector
        logger.info("WORKER_CANONICAL_METRICS is true — using CanonicalMetricsCollector (dir=%s)", partitioned_dir)
        return CanonicalMetricsCollector(settings)

    from conductor.client.telemetry.legacy_metrics_collector import LegacyMetricsCollector
    logger.info("Using LegacyMetricsCollector (dir=%s; set WORKER_CANONICAL_METRICS=true for canonical)", partitioned_dir)
    return LegacyMetricsCollector(settings)
