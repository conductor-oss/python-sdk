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

    Returns a fully-initialised collector (legacy or canonical) that satisfies
    the MetricsCollector Protocol and can be registered as an event listener.
    """
    if _env_bool("WORKER_CANONICAL_METRICS", default=False):
        from conductor.client.telemetry.canonical_metrics_collector import CanonicalMetricsCollector
        logger.info("WORKER_CANONICAL_METRICS is true — using CanonicalMetricsCollector")
        return CanonicalMetricsCollector(settings)

    from conductor.client.telemetry.legacy_metrics_collector import LegacyMetricsCollector
    logger.info("Using LegacyMetricsCollector (set WORKER_CANONICAL_METRICS=true for canonical metrics)")
    return LegacyMetricsCollector(settings)
