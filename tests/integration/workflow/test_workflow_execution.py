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
import logging
import uuid

WORKFLOW_NAME = "sdk_python_integration_test_workflow"
TASK_NAME = "python_integration_test_task"
WORKFLOW_VERSION = 1234
WORKFLOW_OWNER_EMAIL = "test@test"

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(
        __name__
    )
)


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
        configuration=configuration,
        scan_for_annotated_workers=True,
    )
    task_handler.start_processes()
    try:
        test_get_workflow_by_correlation_ids(workflow_executor)
        logger.debug('finished workflow correlation ids test')
        test_workflow_registration(workflow_executor)
        logger.debug('finished workflow registration tests')
        test_workflow_execution(
            workflow_quantity=10,
            workflow_name=WORKFLOW_NAME,
            workflow_executor=workflow_executor,
            workflow_completion_timeout=7
        )
        logger.debug('finished workflow execution tests')
        test_workflow_methods(
            workflow_executor,
            workflow_quantity=2,
        )
        logger.debug('finished workflow methods tests')
        test_workflow_sync_execution(workflow_executor)
        logger.debug('finished workflow sync execution test')
        # test_decorated_worker(workflow_executor)
    except Exception as e:
        task_handler.stop_processes()
        raise Exception(f'failed integration tests, reason: {e}')
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
    _run_with_retry_attempt(
        workflow_executor.get_by_correlation_ids,
        {
            'workflow_name': WORKFLOW_NAME,
            'correlation_ids': [
                '2', '5', '33', '4', '32', '7', '34', '1', '3', '6', '1440'
            ]
        }
    )


def test_workflow_sync_execution(workflow_executor: WorkflowExecutor):
    _run_with_retry_attempt(
        workflow_executor.execute_workflow,
        {
            'request': StartWorkflowRequest(name=WORKFLOW_NAME, version=WORKFLOW_VERSION, correlation_id='sync_workflow_execution'),
            'wait_until_task_ref': '',
        }
    )


def test_workflow_methods(
    workflow_executor: WorkflowExecutor,
    workflow_quantity: int,
) -> None:
    if workflow_quantity < 1:
        return
    task_name = f'python_integration_test_task{uuid.uuid4()}'
    task = SimpleTask(task_name, task_name)
    workflow_executor.metadata_client.register_task_def(
        [task.to_workflow_task()])
    workflow_name = f'python_integration_test_wf_{uuid.uuid4()}'
    workflow = ConductorWorkflow(
        executor=workflow_executor,
        name=workflow_name,
        description='Python workflow example from code',
        version=1234,
    ).add(
        task
    ).failure_workflow(workflow_name)
    workflow_executor.register_workflow(
        workflow.to_workflow_def(),
        overwrite=True,
    )

    workflow_id_async = workflow_executor.start_workflow(
        StartWorkflowRequest(name=workflow_name))
    __update_task_by_ref_name(
        workflow_executor,
        workflow_id_async,
        task_name
    )

    workflow_id_sync = workflow_executor.start_workflow(
        StartWorkflowRequest(name=workflow_name))
    sleep(2)
    response = __update_task_by_ref_name_sync(
        workflow_executor,
        workflow_id_sync,
        task_name
    )

    start_workflow_requests = [''] * workflow_quantity
    for i in range(workflow_quantity):
        start_workflow_requests[i] = StartWorkflowRequest(name=workflow_name)
    workflow_ids = workflow_executor.start_workflows(
        *start_workflow_requests
    )
    for workflow_id in workflow_ids:
        __pause_workflow(workflow_executor, workflow_id)
        __resume_workflow(workflow_executor, workflow_id)
        __terminate_workflow(workflow_executor, workflow_id)
        __restart_workflow(workflow_executor, workflow_id)
        __terminate_workflow(workflow_executor, workflow_id)
        __retry_workflow(workflow_executor, workflow_id)
        failure_wf_id = __terminate_workflow_with_failure(
            workflow_executor, workflow_id, True)
        __terminate_workflow(workflow_executor, failure_wf_id)
        __rerun_workflow(workflow_executor, workflow_id)
        workflow_executor.remove_workflow(
            workflow_id, archive_workflow=False
        )
        workflow_executor.remove_workflow(
            failure_wf_id, archive_workflow=False
        )


def test_workflow_registration(workflow_executor: WorkflowExecutor):
    workflow = generate_workflow(workflow_executor)
    try:
        workflow_executor.metadata_client.unregister_workflow_def_with_http_info(
            workflow.name, workflow.version
        )
    except Exception as e:
        if '404' not in str(e):
            raise e
    workflow.register(overwrite=True) == None
    workflow_executor.register_workflow(
        workflow.to_workflow_def(), overwrite=True
    )


def test_decorated_worker(
        workflow_executor: WorkflowExecutor,
        workflow_name: str = 'TestPythonDecoratedWorkerWf',
) -> None:
    wf = generate_workflow(
        workflow_executor=workflow_executor,
        workflow_name=workflow_name,
        task_name='test_python_decorated_worker',
    )
    wf.register(True)
    workflow_id = workflow_executor.start_workflow(
        StartWorkflowRequest(name=workflow_name))
    logger.debug(f'started workflow with id: {workflow_id}')
    sleep(5)
    _run_with_retry_attempt(
        validate_workflow_status,
        {
            'workflow_id': workflow_id,
            'workflow_executor': workflow_executor
        }
    )


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
        _run_with_retry_attempt(
            validate_workflow_status,
            {
                'workflow_id': workflow_id,
                'workflow_executor': workflow_executor
            }
        )


def generate_workflow(workflow_executor: WorkflowExecutor, workflow_name: str = WORKFLOW_NAME, task_name: str = TASK_NAME) -> ConductorWorkflow:
    return ConductorWorkflow(
        executor=workflow_executor,
        name=workflow_name,
        version=WORKFLOW_VERSION,
    ).owner_email(
        WORKFLOW_OWNER_EMAIL
    ).add(
        SimpleTask(
            task_def_name=task_name,
            task_reference_name=task_name,
        )
    )


def validate_workflow_status(workflow_id: str, workflow_executor: WorkflowExecutor) -> None:
    workflow = workflow_executor.get_workflow(
        workflow_id=workflow_id,
        include_tasks=False,
    )
    if workflow.status != 'COMPLETED':
        raise Exception(
            f'workflow expected to be COMPLETED, but received {workflow.status}, workflow_id: {workflow_id}'
        )
    workflow_status = workflow_executor.get_workflow_status(
        workflow_id=workflow_id,
        include_output=False,
        include_variables=False,
    )
    if workflow_status.status != 'COMPLETED':
        raise Exception(
            f'workflow expected to be COMPLETED, but received {workflow_status.status}, workflow_id: {workflow_id}'
        )


def generate_worker(execute_function: ExecuteTaskFunction) -> Worker:
    return Worker(
        task_definition_name=TASK_NAME,
        execute_function=execute_function,
        poll_interval=0.75
    )


def __pause_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    _run_with_retry_attempt(
        __validate_pause_workflow,
        {
            "workflow_executor": workflow_executor,
            "workflow_id": workflow_id,
        }
    )


def __validate_pause_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    workflow_executor.pause(workflow_id)
    workflow_status = workflow_executor.get_workflow_status(
        workflow_id,
        include_output=True,
        include_variables=False,
    )
    if workflow_status.status != 'PAUSED':
        raise Exception(
            f'workflow expected to be PAUSED, but received {workflow_status.status}, workflow_id: {workflow_id}'
        )


def __resume_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    _run_with_retry_attempt(
        __validate_resume_workflow,
        {
            "workflow_executor": workflow_executor,
            "workflow_id": workflow_id,
        }
    )


def __validate_resume_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    workflow_executor.resume(workflow_id)
    workflow_status = workflow_executor.get_workflow_status(
        workflow_id,
        include_output=True,
        include_variables=False,
    )
    if workflow_status.status != 'RUNNING':
        raise Exception(
            f'workflow expected to be RUNNING, but received {workflow_status.status}, workflow_id: {workflow_id}'
        )


def __terminate_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    _run_with_retry_attempt(
        __validate_terminate_workflow,
        {
            "workflow_executor": workflow_executor,
            "workflow_id": workflow_id,
        }
    )


def __validate_terminate_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    workflow_executor.terminate(workflow_id)
    workflow_status = workflow_executor.get_workflow_status(
        workflow_id,
        include_output=True,
        include_variables=False,
    )
    if workflow_status.status != 'TERMINATED':
        raise Exception(
            f'workflow expected to be TERMINATED, but received {workflow_status.status}, workflow_id: {workflow_id}'
        )


def __terminate_workflow_with_failure(workflow_executor: WorkflowExecutor, workflow_id: str, trigger_failure_workflow: bool) -> str:
    workflow_executor.terminate(workflow_id, 'test', trigger_failure_workflow)
    workflow_status = workflow_executor.get_workflow_status(
        workflow_id,
        include_output=True,
        include_variables=False,
    )
    if workflow_status.status != 'TERMINATED':
        raise Exception(
            f'workflow expected to be TERMINATED, but received {workflow_status.status}, workflow_id: {workflow_id}'
        )
    return workflow_status.output.get('conductor.failure_workflow')


def __restart_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    _run_with_retry_attempt(
        __validate_restart_workflow,
        {
            "workflow_executor": workflow_executor,
            "workflow_id": workflow_id,
        }
    )


def __validate_restart_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    workflow_executor.restart(workflow_id)
    workflow_status = workflow_executor.get_workflow_status(
        workflow_id,
        include_output=True,
        include_variables=False,
    )
    if workflow_status.status != 'RUNNING':
        raise Exception(
            f'workflow expected to be RUNNING, but received {workflow_status.status}, workflow_id: {workflow_id}'
        )


def __retry_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    _run_with_retry_attempt(
        __validate_retry_workflow,
        {
            "workflow_executor": workflow_executor,
            "workflow_id": workflow_id,
        }
    )


def __validate_retry_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    workflow_executor.retry(workflow_id)
    workflow_status = workflow_executor.get_workflow_status(
        workflow_id,
        include_output=True,
        include_variables=False,
    )
    if workflow_status.status != 'RUNNING':
        raise Exception(
            f'workflow expected to be RUNNING, but received {workflow_status.status}, workflow_id: {workflow_id}'
        )


def __rerun_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    _run_with_retry_attempt(
        __validate_rerun_workflow,
        {
            "workflow_executor": workflow_executor,
            "workflow_id": workflow_id,
        }
    )


def __validate_rerun_workflow(workflow_executor: WorkflowExecutor, workflow_id: str) -> None:
    workflow_executor.rerun(RerunWorkflowRequest(), workflow_id)
    workflow_status = workflow_executor.get_workflow_status(
        workflow_id,
        include_output=True,
        include_variables=False,
    )
    if workflow_status.status != 'RUNNING':
        raise Exception(
            f'workflow expected to be RUNNING, but received {workflow_status.status}, workflow_id: {workflow_id}'
        )


def _run_with_retry_attempt(f, params, retries=4) -> None:
    for attempt in range(retries):
        try:
            return f(**params)
        except Exception as e:
            if attempt == retries - 1:
                raise e
            sleep(1 << attempt)


def __update_task_by_ref_name(workflow_executor: WorkflowExecutor, workflow_id: str, task_name: str):
    return _run_with_retry_attempt(
        workflow_executor.update_task_by_ref_name,
        params={
            'task_output': {},
            'workflow_id': workflow_id,
            'task_reference_name': task_name,
            'status': 'COMPLETED'
        }
    )


def __update_task_by_ref_name_sync(workflow_executor: WorkflowExecutor, workflow_id: str, task_name: str):
    return _run_with_retry_attempt(
        workflow_executor.update_task_by_ref_name_sync,
        params={
            'task_output': {},
            'workflow_id': workflow_id,
            'task_reference_name': task_name,
            'status': 'COMPLETED'
        }
    )
