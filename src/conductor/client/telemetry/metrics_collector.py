"""
Backward-compatibility shim.

Existing code that does::

    from conductor.client.telemetry.metrics_collector import MetricsCollector

will continue to work -- ``MetricsCollector`` is the legacy implementation.

``task_handler.py`` accesses ``mc._ensure_prometheus_imported()``,
``mc.Counter``, ``mc.CollectorRegistry`` etc. via
``from conductor.client.telemetry import metrics_collector as mc``.
These are lazily-initialised module-level globals in the base module,
so we use ``__getattr__`` to forward attribute lookups dynamically
(a plain ``from … import Counter`` would capture ``None`` at import time).
"""

# Re-export the legacy implementation under its original name.
from conductor.client.telemetry.legacy_metrics_collector import LegacyMetricsCollector as MetricsCollector  # noqa: F401

from conductor.client.telemetry import metrics_collector_base as _base  # noqa: F401

_FORWARDED = {
    "_ensure_prometheus_imported",
    "CollectorRegistry",
    "Counter",
    "Gauge",
    "Histogram",
    "Summary",
    "write_to_textfile",
    "MultiProcessCollector",
}


def __getattr__(name):
    if name in _FORWARDED:
        return getattr(_base, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
