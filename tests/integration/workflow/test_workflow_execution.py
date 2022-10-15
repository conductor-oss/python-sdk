from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import RerunWorkflowRequest
from conductor.client.http.models import StartWorkflowRequest
from conductor.client.http.models import TaskDef
from conductor.client.worker.worker import ExecuteTaskFunction
from conductor.client.worker.worker import Worker
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from conductor.client.workflow.task.simple_task import SimpleTask
from resources.worker.python.python_worker import ClassWorker
from resources.worker.python.python_worker import ClassWorkerWithDomain
from resources.worker.python.python_worker import worker_with_generic_input_and_generic_output
from resources.worker.python.python_worker import worker_with_generic_input_and_task_result_output
from resources.worker.python.python_worker import worker_with_task_input_and_generic_output
from resources.worker.python.python_worker import worker_with_task_input_and_task_result_output
from time import sleep

WORKFLOW_NAME = "python_integration_test_workflow"
TASK_NAME = "python_integration_test_task"
WORKFLOW_VERSION = 1234
WORKFLOW_OWNER_EMAIL = "test@test"


def run_workflow_execution_tests(configuration: Configuration, workflow_executor: WorkflowExecutor):
    task_handler = TaskHandler(
        workers=[
            ClassWorker(TASK_NAME),
            ClassWorkerWithDomain(TASK_NAME),
            generate_worker(worker_with_generic_input_and_generic_output),
            generate_worker(worker_with_generic_input_and_task_result_output),
            generate_worker(worker_with_task_input_and_generic_output),
            generate_worker(worker_with_task_input_and_task_result_output),
        ],
        configuration=configuration
    )
    task_handler.start_processes()
    test_get_workflow_by_correlation_ids(workflow_executor)
    test_workflow_registration(workflow_executor)
    test_workflow_execution(
        workflow_quantity=10,
        workflow_name=WORKFLOW_NAME,
        workflow_executor=workflow_executor,
        workflow_completion_timeout=7
    )
    test_workflow_methods(
        workflow_executor,
        workflow_quantity=10,
    )
    task_handler.stop_processes()


def generate_tasks_defs():
    python_simple_task_from_code = TaskDef(
        description="desc python_simple_task_from_code",
        owner_app="python_integration_test_app",
        timeout_seconds=3,
        response_timeout_seconds=2,
        created_by=WORKFLOW_OWNER_EMAIL,
        name=TASK_NAME,
        input_keys=["input1"],
        output_keys=[],
        owner_email=WORKFLOW_OWNER_EMAIL,
    )
    return [python_simple_task_from_code]


def test_get_workflow_by_correlation_ids(workflow_executor: WorkflowExecutor):
    ids = workflow_executor.get_by_correlation_ids(
        workflow_name=WORKFLOW_NAME,
        correlation_ids=[
            '2', '5', '33', '4', '32', '7', '34', '1', '3', '6', '1440'
        ]
    )
    assert ids != None


def test_workflow_methods(
    workflow_executor: WorkflowExecutor,
    workflow_quantity: int,
) -> None:
    task = SimpleTask(
        'python_integration_test_abc1asjdkajskdjsad',
        'python_integration_test_abc1asjdkajskdjsad'
    )
    workflow_executor.metadata_client.register_task_def(
        [task.to_workflow_task()]
    )
    workflow_name = 'python_integration_test_abc1asjdk'
    workflow = ConductorWorkflow(
        executor=workflow_executor,
        name=workflow_name,
        description='Python workflow example from code',
        version=1234,
    ).add(
        task
    )
    workflow_executor.register_workflow(
        workflow.to_workflow_def(),
        overwrite=True,
    )
    start_workflow_requests = [''] * workflow_quantity
    for i in range(workflow_quantity):
        start_workflow_requests[i] = StartWorkflowRequest(name=workflow_name)
    workflow_ids = workflow_executor.start_workflows(
        *start_workflow_requests
    )
    for workflow_id in workflow_ids:
        _pause_workflow(workflow_executor, workflow_id)
        _resume_workflow(workflow_executor, workflow_id)
        _terminate_workflow(workflow_executor, workflow_id)
        _restart_workflow(workflow_executor, workflow_id)
        _terminate_workflow(workflow_executor, workflow_id)
        _retry_workflow(workflow_executor, workflow_id)
        _pause_workflow(workflow_executor, workflow_id)
        _terminate_workflow(workflow_executor, workflow_id)
        workflow_executor.rerun(
            RerunWorkflowRequest(),
            workflow_id
        )
        workflow_executor.remove_workflow(
            workflow_id, archive_workflow=False
        )


def test_workflow_registration(workflow_executor: WorkflowExecutor):
    workflow = generate_workflow(workflow_executor)
    try:
        workflow_executor.metadata_client.unregister_workflow_def_with_http_info(
            workflow.name, workflow.version
        )
    except:
        pass
    assert workflow.register(overwrite=True) == None
    assert workflow_executor.register_workflow(
        workflow.to_workflow_def(), overwrite=True
    ) == None


def test_workflow_execution(
    workflow_quantity: int,
    workflow_name: str,
    workflow_executor: WorkflowExecutor,
    workflow_completion_timeout: float,
) -> None:
    start_workflow_requests = [''] * workflow_quantity
    for i in range(workflow_quantity):
        start_workflow_requests[i] = StartWorkflowRequest(name=workflow_name)
    workflow_ids = workflow_executor.start_workflows(*start_workflow_requests)
    sleep(workflow_completion_timeout)
    for workflow_id in workflow_ids:
        validate_workflow_status(workflow_id, workflow_executor)


def generate_workflow(workflow_executor: WorkflowExecutor) -> ConductorWorkflow:
    return ConductorWorkflow(
        executor=workflow_executor,
        name=WORKFLOW_NAME,
        version=WORKFLOW_VERSION,
    ).owner_email(
        WORKFLOW_OWNER_EMAIL
    ).add(
        SimpleTask(
            task_def_name=TASK_NAME,
            task_reference_name=TASK_NAME,
        )
    )


def validate_workflow_status(workflow_id: str, workflow_executor: WorkflowExecutor) -> None:
    workflow = workflow_executor.get_workflow(
        workflow_id=workflow_id,
        include_tasks=False,
    )
    assert workflow.status == 'COMPLETED'
    workflow_status = workflow_executor.get_workflow_status(
        workflow_id=workflow_id,
        include_output=False,
        include_variables=False,
    )
    assert workflow_status.status == 'COMPLETED'


def generate_worker(execute_function: ExecuteTaskFunction) -> Worker:
    return Worker(
        task_definition_name=TASK_NAME,
        execute_function=execute_function,
        poll_interval=0.05
    )


def _pause_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    workflow_executor.pause(workflow_id)
    workflow_status = workflow_executor.get_workflow_status(
        workflow_id,
        include_output=True,
        include_variables=False,
    )
    assert workflow_status.status == 'PAUSED'


def _resume_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    workflow_executor.resume(workflow_id)
    workflow_status = workflow_executor.get_workflow_status(
        workflow_id,
        include_output=True,
        include_variables=False,
    )
    assert workflow_status.status == 'RUNNING'


def _terminate_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    workflow_executor.terminate(workflow_id)
    workflow_status = workflow_executor.get_workflow_status(
        workflow_id,
        include_output=True,
        include_variables=False,
    )
    assert workflow_status.status == 'TERMINATED'


def _restart_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    workflow_executor.restart(workflow_id)
    workflow_status = workflow_executor.get_workflow_status(
        workflow_id,
        include_output=True,
        include_variables=False,
    )
    assert workflow_status.status == 'RUNNING'


def _retry_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    workflow_executor.retry(workflow_id)
    workflow_status = workflow_executor.get_workflow_status(
        workflow_id,
        include_output=True,
        include_variables=False,
    )
    assert workflow_status.status == 'RUNNING'
