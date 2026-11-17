from __future__ import annotations

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.metrics_settings import MetricsSettings
from conductor.client.http.models.task_def import TaskDef
from conductor.client.orkes_clients import OrkesClients
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.simple_task import SimpleTask

from harness_env import env_int_or_default
from simulated_task_worker import SimulatedTaskWorker
from workflow_governor import WorkflowGovernor
from workflow_status_probe import WorkflowStatusProbe

WORKFLOW_NAME = "python_simulated_tasks_workflow"

SIMULATED_WORKERS = [
    ("python_worker_0", "quickpulse", 1),
    ("python_worker_1", "whisperlink", 2),
    ("python_worker_2", "shadowfetch", 3),
    ("python_worker_3", "ironforge", 4),
    ("python_worker_4", "deepcrawl", 5),
]


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


class SDKTesting:
    """Exercises the core SDK: registers five simulated tasks and a workflow that
    chains them, serves those tasks from this process, and starts workflows at a
    fixed rate so the SDK is continuously both workflow starter and task worker."""

    def __init__(
        self,
        configuration: Configuration,
        clients: OrkesClients,
        metrics_settings: MetricsSettings,
    ) -> None:
        self._configuration = configuration
        self._clients = clients
        self._metrics_settings = metrics_settings
        self._task_handler: TaskHandler | None = None
        self._probe: WorkflowStatusProbe | None = None
        self._governor: WorkflowGovernor | None = None

    def prepare(self) -> None:
        """Register metadata and fork the worker processes. Starts no threads."""
        register_metadata(self._clients)

        workflows_per_sec = env_int_or_default("HARNESS_WORKFLOWS_PER_SEC", 2)
        batch_size = env_int_or_default("HARNESS_BATCH_SIZE", 20)
        poll_interval_ms = env_int_or_default("HARNESS_POLL_INTERVAL_MS", 100)

        workers = []
        for task_name, codename, sleep_seconds in SIMULATED_WORKERS:
            worker = SimulatedTaskWorker(task_name, codename, sleep_seconds, batch_size, poll_interval_ms)
            workers.append(worker)

        self._task_handler = TaskHandler(
            workers=workers,
            configuration=self._configuration,
            scan_for_annotated_workers=False,
            metrics_settings=self._metrics_settings,
        )

        workflow_executor = self._clients.get_workflow_executor()
        workflow_client = self._clients.get_workflow_client()

        probe_rate = env_int_or_default("HARNESS_PROBE_RATE_PER_SEC", 0)
        self._probe = WorkflowStatusProbe(workflow_client, probe_rate)

        self._governor = WorkflowGovernor(
            workflow_executor, WORKFLOW_NAME, workflows_per_sec,
            id_sink=self._probe.offer,
        )

        self._task_handler.start_processes()

    def start(self) -> None:
        """Start the probe and governor threads. Call only after every module's prepare()."""
        self._probe.start()
        self._governor.start()

    def stop(self) -> None:
        if self._probe is not None:
            self._probe.shutdown()
        if self._governor is not None:
            self._governor.stop()
        if self._task_handler is not None:
            self._task_handler.stop_processes()

    def wait(self) -> None:
        """Block until the worker processes exit."""
        self._task_handler.join_processes()
