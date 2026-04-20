from __future__ import annotations

import os
import signal
import sys

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.http.models.task_def import TaskDef
from conductor.client.orkes_clients import OrkesClients
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.simple_task import SimpleTask

from simulated_task_worker import SimulatedTaskWorker
from workflow_governor import WorkflowGovernor

WORKFLOW_NAME = "python_simulated_tasks_workflow"

SIMULATED_WORKERS = [
    ("python_worker_0", "quickpulse", 1),
    ("python_worker_1", "whisperlink", 2),
    ("python_worker_2", "shadowfetch", 3),
    ("python_worker_3", "ironforge", 4),
    ("python_worker_4", "deepcrawl", 5),
]


def env_int_or_default(key: str, default: int) -> int:
    s = os.environ.get(key, "")
    if not s:
        return default
    try:
        return int(s)
    except ValueError:
        return default


def register_metadata(clients: OrkesClients) -> None:
    metadata_client = clients.get_metadata_client()
    workflow_executor = clients.get_workflow_executor()

    for task_name, codename, sleep_seconds in SIMULATED_WORKERS:
        task_def = TaskDef(
            name=task_name,
            description=f"Python SDK harness simulated task ({codename}, default delay {sleep_seconds}s)",
            retry_count=1,
            timeout_seconds=300,
            response_timeout_seconds=300,
        )
        metadata_client.register_task_def(task_def)

    wf = ConductorWorkflow(
        executor=workflow_executor,
        name=WORKFLOW_NAME,
        version=1,
        description="Python SDK harness simulated task workflow",
    )
    wf.owner_email("python-sdk-harness@conductor.io")

    for task_name, codename, _ in SIMULATED_WORKERS:
        wf.add(SimpleTask(task_def_name=task_name, task_reference_name=codename))

    wf.register(overwrite=True)
    print(f"Registered workflow {WORKFLOW_NAME} with {len(SIMULATED_WORKERS)} tasks")


def main() -> None:
    configuration = Configuration()
    clients = OrkesClients(configuration)

    register_metadata(clients)

    workflows_per_sec = env_int_or_default("HARNESS_WORKFLOWS_PER_SEC", 2)
    batch_size = env_int_or_default("HARNESS_BATCH_SIZE", 20)
    poll_interval_ms = env_int_or_default("HARNESS_POLL_INTERVAL_MS", 100)

    workers = []
    for task_name, codename, sleep_seconds in SIMULATED_WORKERS:
        worker = SimulatedTaskWorker(task_name, codename, sleep_seconds, batch_size, poll_interval_ms)
        workers.append(worker)

    metrics_port = env_int_or_default("HARNESS_METRICS_PORT", 9991)
    metrics_settings = MetricsSettings(http_port=metrics_port)
    print(f"Prometheus metrics will be served on port {metrics_port}")

    task_handler = TaskHandler(
        workers=workers,
        configuration=configuration,
        scan_for_annotated_workers=False,
        metrics_settings=metrics_settings,
    )

    workflow_executor = clients.get_workflow_executor()
    governor = WorkflowGovernor(workflow_executor, WORKFLOW_NAME, workflows_per_sec)
    governor.start()

    main_pid = os.getpid()
    shutting_down = False

    def shutdown(signum, frame):
        nonlocal shutting_down
        if os.getpid() != main_pid or shutting_down:
            return
        shutting_down = True
        print("Shutting down...")
        governor.stop()
        task_handler.stop_processes()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    task_handler.start_processes()
    task_handler.join_processes()


if __name__ == "__main__":
    main()
