from __future__ import annotations

import os
import signal
import sys

from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.orkes_clients import OrkesClients
from conductor.client.telemetry.metrics_factory import create_metrics_collector_for_parent

from agentic import AgenticTesting
from harness_env import env_bool_or_default, env_int_or_default
from sdk_testing import SDKTesting


def main() -> None:
    configuration = Configuration()

    metrics_port = env_int_or_default("HARNESS_METRICS_PORT", 9991)
    metrics_settings = MetricsSettings(
        http_port=metrics_port,
        clean_directory=True,
        clean_dead_pids=True,
    )

    # The parent collects metrics too (task/workflow registration below and the
    # WorkflowGovernor), so use the parent factory: it cleans the directory up
    # front -- before the collector's first write -- then creates the collector,
    # avoiding orphaning the parent's own .db files. clean_metrics_directory() is
    # idempotent per process, so TaskHandler's later call is a no-op.
    metrics_collector = create_metrics_collector_for_parent(metrics_settings)
    print(f"Prometheus metrics server started on port {metrics_port} ({metrics_collector.collector_name()} metrics)")
    clients = OrkesClients(configuration, metrics_collector=metrics_collector)

    sdk_testing = None
    if env_bool_or_default("HARNESS_SDK_TESTING_ENABLED", True):
        sdk_testing = SDKTesting(configuration, clients, metrics_settings)

    agentic_testing = None
    if env_bool_or_default("HARNESS_AGENTIC_TESTING_ENABLED", False):
        agentic_testing = AgenticTesting(configuration)

    if sdk_testing is None and agentic_testing is None:
        print("Nothing to run: HARNESS_SDK_TESTING_ENABLED and HARNESS_AGENTIC_TESTING_ENABLED are both off")
        sys.exit(1)

    main_pid = os.getpid()
    shutting_down = False

    def shutdown(signum, frame):
        nonlocal shutting_down
        if os.getpid() != main_pid or shutting_down:
            return
        shutting_down = True
        print("Shutting down...")
        if agentic_testing is not None:
            agentic_testing.stop()
        if sdk_testing is not None:
            sdk_testing.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Fork every module's worker processes BEFORE starting any module's threads.
    # The parent's MetricsCollector uses prometheus_client's multiprocess mode,
    # which guards its mmapped value files with a threading.Lock. If a governor
    # thread is already running at fork() time, a child can inherit that lock in
    # a held state and deadlock on its first metric write.
    if sdk_testing is not None:
        sdk_testing.prepare()
    if agentic_testing is not None:
        agentic_testing.prepare()

    if sdk_testing is not None:
        sdk_testing.start()
    if agentic_testing is not None:
        agentic_testing.start()

    if sdk_testing is not None:
        sdk_testing.wait()
    else:
        agentic_testing.wait()


if __name__ == "__main__":
    main()
