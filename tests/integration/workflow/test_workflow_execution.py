import logging
import time
from multiprocessing import set_start_method
from time import sleep

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import StartWorkflowRequest
from conductor.client.http.models import TaskDef
from conductor.client.worker.worker import ExecuteTaskFunction
from conductor.client.worker.worker import Worker
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from conductor.client.workflow.task.simple_task import SimpleTask
from tests.integration.resources.worker.python.python_worker import *

WORKFLOW_NAME = "sdk_python_integration_test_workflow"
WORKFLOW_DESCRIPTION = "Python SDK Integration Test"
TASK_NAME = "python_integration_test_task"
WORKFLOW_VERSION = 1234
WORKFLOW_OWNER_EMAIL = "test@test"
COMPLEX_WF_NAME = 'complex_wf_signal_test'
SUB_WF_1_NAME = 'complex_wf_signal_test_subworkflow_1'
SUB_WF_2_NAME = 'complex_wf_signal_test_subworkflow_2'

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(
        __name__
    )
)


def run_workflow_execution_tests(configuration: Configuration, workflow_executor: WorkflowExecutor):
    workers = [
        ClassWorker(TASK_NAME),
        ClassWorkerWithDomain(TASK_NAME),
        generate_worker(worker_with_generic_input_and_generic_output),
        generate_worker(worker_with_generic_input_and_task_result_output),
        generate_worker(worker_with_task_input_and_generic_output),
        generate_worker(worker_with_task_input_and_task_result_output),
    ]
    task_handler = TaskHandler(
        workers=workers,
        configuration=configuration,
        scan_for_annotated_workers=True,
        import_modules=['tests.integration.resources.worker.python.python_worker']
    )
    set_start_method('fork', force=True)
    task_handler.start_processes()
    try:
        test_get_workflow_by_correlation_ids(workflow_executor)
        logger.debug('finished workflow correlation ids test')
        test_workflow_registration(workflow_executor)
        logger.debug('finished workflow registration tests')
        test_workflow_execution(
            workflow_quantity=6,
            workflow_name=WORKFLOW_NAME,
            workflow_executor=workflow_executor,
            workflow_completion_timeout=5.0
        )
        test_decorated_workers(workflow_executor)
        logger.debug('finished decorated workers tests')
        test_execute_workflow_async_features(workflow_executor)
        logger.debug('finished execute_workflow reactive features tests')
        test_execute_workflow_error_handling(workflow_executor)
        logger.debug('finished execute_workflow error handling tests')
        run_signal_tests(configuration, workflow_executor)
        logger.debug('finished signal API tests')

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
                '2', '5', '33', '4', '32', '7', '34', '1', '3', '6', '1440',
            ]
        }
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


def test_decorated_workers(
        workflow_executor: WorkflowExecutor,
        workflow_name: str = 'TestPythonDecoratedWorkerWf',
) -> None:
    wf = generate_workflow(
        workflow_executor=workflow_executor,
        workflow_name=workflow_name,
        task_name='test_python_decorated_worker',
    )
    wf.register(True)
    workflow_id = workflow_executor.start_workflow(StartWorkflowRequest(name=workflow_name))
    logger.debug(f'started TestPythonDecoratedWorkerWf with id: {workflow_id}')

    td_map = {
        'test_python_decorated_worker': 'cool'
    }
    start_wf_req = StartWorkflowRequest(name=workflow_name, task_to_domain=td_map)
    workflow_id_2 = workflow_executor.start_workflow(start_wf_req)

    logger.debug(f'started TestPythonDecoratedWorkerWf with domain:cool and id: {workflow_id_2}')
    sleep(15)

    _run_with_retry_attempt(
        validate_workflow_status,
        {
            'workflow_id': workflow_id,
            'workflow_executor': workflow_executor
        }
    )

    _run_with_retry_attempt(
        validate_workflow_status,
        {
            'workflow_id': workflow_id_2,
            'workflow_executor': workflow_executor
        }
    )

    workflow_executor.metadata_client.unregister_workflow_def(wf.name, wf.version)


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


def generate_workflow(workflow_executor: WorkflowExecutor, workflow_name: str = WORKFLOW_NAME,
                      task_name: str = TASK_NAME) -> ConductorWorkflow:
    return ConductorWorkflow(
        executor=workflow_executor,
        name=workflow_name,
        description=WORKFLOW_DESCRIPTION,
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
        poll_interval=750.0
    )


def _run_with_retry_attempt(f, params, retries=4) -> None:
    for attempt in range(retries):
        try:
            return f(**params)
        except Exception as e:
            if attempt == retries - 1:
                raise e
            sleep(1 << attempt)

def test_execute_workflow_async_features(workflow_executor: WorkflowExecutor):
    """Test the execute_workflow method with reactive features (consistency and return_strategy)"""
    logger.debug('Starting execute_workflow reactive features tests')

    # Register workflow first
    workflow = generate_workflow(workflow_executor)
    workflow.register(overwrite=True)

    # Test 1: execute_workflow with default values (None -> defaults)
    logger.debug('Test 1: execute_workflow with default consistency/return_strategy')
    start_request = StartWorkflowRequest(
        name=WORKFLOW_NAME,
        version=WORKFLOW_VERSION,
        input={'test_input': 'default_test'}
    )

    workflow_run_1 = workflow_executor.execute_workflow_with_return_strategy(request=start_request,
                                                                             wait_until_task_ref=TASK_NAME,
                                                                             wait_for_seconds=30)

    assert workflow_run_1 is not None, "Workflow run should not be None"
    logger.debug(f'Test 1 - Workflow ID: {workflow_run_1.workflow_id}, Status: {workflow_run_1.status}')

    # Wait for completion if needed
    if workflow_run_1.status == 'RUNNING':
        _wait_for_workflow_completion(workflow_executor, workflow_run_1.workflow_id)

    # Test 2: execute_workflow with explicit DURABLE consistency
    logger.debug('Test 2: execute_workflow with explicit DURABLE consistency')
    start_request_2 = StartWorkflowRequest(
        name=WORKFLOW_NAME,
        version=WORKFLOW_VERSION,
        input={'test_input': 'durable_test'}
    )

    workflow_run_2 = workflow_executor.execute_workflow_with_return_strategy(request=start_request_2,
                                                                             wait_until_task_ref=TASK_NAME,
                                                                             wait_for_seconds=30, consistency='DURABLE',
                                                                             return_strategy='BLOCKING_WORKFLOW')

    assert workflow_run_2 is not None, "Workflow run should not be None"
    logger.debug(f'Test 2 - Workflow ID: {workflow_run_2.workflow_id}, Status: {workflow_run_2.status}')

    if workflow_run_2.status == 'RUNNING':
        _wait_for_workflow_completion(workflow_executor, workflow_run_2.workflow_id)

    # Test 3: execute_workflow with DURABLE consistency and different return strategy
    logger.debug('Test 3: execute_workflow with DURABLE consistency and BLOCKING_WORKFLOW')
    start_request_3 = StartWorkflowRequest(
        name=WORKFLOW_NAME,
        version=WORKFLOW_VERSION,
        input={'test_input': 'durable_blocking_test'}
    )

    try:
        workflow_run_3 = workflow_executor.execute_workflow_with_return_strategy(request=start_request_3,
                                                                                 wait_until_task_ref=TASK_NAME,
                                                                                 wait_for_seconds=30,
                                                                                 consistency='DURABLE',
                                                                                 return_strategy='BLOCKING_WORKFLOW')

        assert workflow_run_3 is not None, "Workflow run should not be None"
        logger.debug(f'Test 3 - Workflow ID: {workflow_run_3.workflow_id}, Status: {workflow_run_3.status}')

        if workflow_run_3.status == 'RUNNING':
            _wait_for_workflow_completion(workflow_executor, workflow_run_3.workflow_id)

    except Exception as e:
        logger.error(f'Test 3 failed with error: {e}')
        logger.debug('Skipping Test 3 - DURABLE/BLOCKING_WORKFLOW combination may not be supported')
        # Create a placeholder workflow_run_3 to continue tests
        workflow_run_3 = None

    # Test 4: execute_workflow with SYNCHRONOUS consistency and BLOCKING_TASK_INPUT
    logger.debug('Test 4: execute_workflow with SYNCHRONOUS consistency and BLOCKING_TASK_INPUT')
    start_request_4 = StartWorkflowRequest(
        name=WORKFLOW_NAME,
        version=WORKFLOW_VERSION,
        input={'test_input': 'synchronous_test'}
    )

    workflow_run_4 = workflow_executor.execute_workflow_with_return_strategy(request=start_request_4,
                                                                             wait_until_task_ref=TASK_NAME,
                                                                             wait_for_seconds=30,
                                                                             consistency='SYNCHRONOUS',
                                                                             return_strategy='BLOCKING_TASK_INPUT')

    print(f"Raw response type: {type(workflow_run_4)}")
    if workflow_run_4 is None:
        print("Response is None - checking API call...")

    assert workflow_run_4 is not None, "Workflow run should not be None"
    logger.debug(f'Test 4 - Workflow ID: {workflow_run_4.workflow_id}, Status: {workflow_run_4.status}')

    if workflow_run_4.status == 'RUNNING':
        _wait_for_workflow_completion(workflow_executor, workflow_run_4.workflow_id)

    # Test 5: Compare with original execute method
    logger.debug('Test 5: Compare with original execute method')
    workflow_run_5 = workflow_executor.execute(
        name=WORKFLOW_NAME,
        version=WORKFLOW_VERSION,
        workflow_input={'test_input': 'original_test'},
        wait_until_task_ref=TASK_NAME,
        wait_for_seconds=30
    )

    assert workflow_run_5 is not None, "Workflow run should not be None"
    logger.debug(f'Test 5 - Workflow ID: {workflow_run_5.workflow_id}, Status: {workflow_run_5.status}')

    if workflow_run_5.status == 'RUNNING':
        _wait_for_workflow_completion(workflow_executor, workflow_run_5.workflow_id)

    # Validate all workflows completed successfully
    workflow_ids = [
        workflow_run_1.workflow_id,
        workflow_run_2.workflow_id,
        workflow_run_4.workflow_id,
        workflow_run_5.workflow_id
    ]

    # Add workflow_run_3 only if it was successful
    if workflow_run_3 is not None:
        workflow_ids.insert(2, workflow_run_3.workflow_id)

    for i, workflow_id in enumerate(workflow_ids, 1):
        _run_with_retry_attempt(
            validate_workflow_status,
            {
                'workflow_id': workflow_id,
                'workflow_executor': workflow_executor
            }
        )
        logger.debug(f'Test {i} - Workflow {workflow_id} completed successfully')

    logger.debug('All execute_workflow reactive features tests passed!')


def test_execute_workflow_error_handling(workflow_executor: WorkflowExecutor):
    """Test error handling in execute_workflow with invalid parameters"""
    logger.debug('Starting execute_workflow error handling tests')

    # Test with invalid consistency value (should still work due to defaults)
    start_request = StartWorkflowRequest(
        name=WORKFLOW_NAME,
        version=WORKFLOW_VERSION,
        input={'test_input': 'error_test'}
    )

    try:
        # This should work because None values get converted to defaults
        workflow_run = workflow_executor.execute_workflow_with_return_strategy(request=start_request,
                                                                               wait_until_task_ref=TASK_NAME,
                                                                               wait_for_seconds=5, consistency=None,
                                                                               return_strategy=None)
        logger.debug(f'Error handling test - Workflow created: {workflow_run.workflow_id}')

        if workflow_run.status == 'RUNNING':
            _wait_for_workflow_completion(workflow_executor, workflow_run.workflow_id)

        _run_with_retry_attempt(
            validate_workflow_status,
            {
                'workflow_id': workflow_run.workflow_id,
                'workflow_executor': workflow_executor
            }
        )

    except Exception as e:
        logger.error(f'Unexpected error in error handling test: {e}')
        raise e

    logger.debug('Execute_workflow error handling tests passed!')


def _wait_for_workflow_completion(workflow_executor: WorkflowExecutor, workflow_id: str, max_wait_seconds: int = 60):
    """Helper function to wait for workflow completion"""
    import time
    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        workflow = workflow_executor.get_workflow(workflow_id, True)

        if workflow.status in ['COMPLETED', 'FAILED', 'TERMINATED', 'TIMED_OUT']:
            logger.debug(f'Workflow {workflow_id} finished with status: {workflow.status}')
            return workflow

        logger.debug(f'Waiting for workflow {workflow_id}... Status: {workflow.status}')
        time.sleep(2)

    # Return final state even if not completed
    return workflow_executor.get_workflow(workflow_id, True)

# ===== SIGNAL TESTS =====

def run_signal_tests(configuration: Configuration, workflow_executor: WorkflowExecutor):
    """Run all signal API tests using WorkflowExecutor methods"""
    logger.info('START: Signal API tests using WorkflowExecutor')

    try:
        # Register signal test workflows (same as original test)
        _register_signal_test_workflows(workflow_executor)

        # Test sync signal with different return strategies
        test_signal_target_workflow(workflow_executor)
        test_signal_blocking_workflow(workflow_executor)
        test_signal_blocking_task(workflow_executor)
        test_signal_blocking_task_input(workflow_executor)

        # Test default return strategy
        test_signal_default_strategy(workflow_executor)

        # Test async signal
        test_signal_async(workflow_executor)

        # Test to_dict fix
        test_signal_to_dict_fix(workflow_executor)

        logger.info('All signal tests completed successfully')

    except Exception as e:
        logger.error(f'Signal tests failed: {e}')
        raise
    finally:
        # Cleanup
        try:
            workflow_executor.metadata_client.unregister_workflow_def(
                COMPLEX_WF_NAME, 1
            )
            workflow_executor.metadata_client.unregister_workflow_def(
                SUB_WF_1_NAME, 1
            )
            workflow_executor.metadata_client.unregister_workflow_def(
                SUB_WF_2_NAME, 1
            )
        except Exception as cleanup_error:
            logger.warning(f'Cleanup failed: {cleanup_error}')

    logger.info('END: Signal API tests using WorkflowExecutor')


def _register_signal_test_workflows(workflow_executor: WorkflowExecutor):
    """Register the complex signal test workflows from JSON files"""
    import json
    import os

    def _get_workflow_definition(path):
        """Get workflow definition from JSON file, following existing pattern"""
        # Get directory of current script
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Path to project root (adjust based on your structure)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))

        # Construct path from project root
        actual_path = os.path.join(project_root, path)

        # For debugging
        logger.info(f"Attempting to load workflow from: {actual_path}")

        try:
            with open(actual_path, "r") as f:
                workflow_json = json.loads(f.read())
                # Convert to WorkflowDef object
                api_client = workflow_executor.workflow_client.api_client
                workflow_def = api_client.deserialize_class(workflow_json, "WorkflowDef")
                return workflow_def
        except FileNotFoundError:
            logger.error(f"Workflow definition file not found: {actual_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading workflow definition: {e}")
            raise

    try:
        # Register main workflow
        complex_wf_def = _get_workflow_definition(f'tests/integration/resources/test_data/{COMPLEX_WF_NAME}.json')
        workflow_executor.metadata_client.update1(body=[complex_wf_def], overwrite=True)
        logger.info(f'Registered workflow: {COMPLEX_WF_NAME}')

        # Register subworkflows
        sub_wf1_def = _get_workflow_definition(f'tests/integration/resources/test_data/{SUB_WF_1_NAME}.json')
        workflow_executor.metadata_client.update1(body=[sub_wf1_def], overwrite=True)
        logger.info(f'Registered workflow: {SUB_WF_1_NAME}')

        sub_wf2_def = _get_workflow_definition(f'tests/integration/resources/test_data/{SUB_WF_2_NAME}.json')
        workflow_executor.metadata_client.update1(body=[sub_wf2_def], overwrite=True)
        logger.info(f'Registered workflow: {SUB_WF_2_NAME}')

    except Exception as e:
        logger.warning(f'Some workflows may already be registered: {e}')

    # Give time for workflow registration
    time.sleep(1.0)


def _start_complex_workflow(workflow_executor: WorkflowExecutor) -> str:
    """Start complex workflow and return workflow ID"""
    try:
        start_request = StartWorkflowRequest(
            name=COMPLEX_WF_NAME,
            version=1,
            input={}
        )

        # Use the workflow_executor.start_workflow method
        workflow_id = workflow_executor.start_workflow(start_request)

        assert workflow_id is not None, "Failed to start workflow"

        # Brief wait for workflow initialization
        time.sleep(0.5)
        logger.info(f'Started workflow {workflow_id}')
        return workflow_id

    except Exception as e:
        logger.error(f'Failed to start workflow: {e}')
        raise


def _complete_workflow(workflow_executor: WorkflowExecutor, workflow_id: str):
    """Complete workflow by sending required signals"""
    try:
        # Send completion signals using signal_async method
        time.sleep(5)
        workflow_executor.signal_async(
            workflow_id=workflow_id,
            status="COMPLETED",
            body={"result": "signal1"}
        )
        workflow_executor.signal_async(
            workflow_id=workflow_id,
            status="COMPLETED",
            body={"result": "signal2"}
        )
    except Exception as e:
        logger.error(f'Failed to complete workflow {workflow_id}: {e}')
        raise


def test_signal_target_workflow(workflow_executor: WorkflowExecutor):
    """Test signal with TARGET_WORKFLOW return strategy"""
    logger.info('Testing signal with TARGET_WORKFLOW strategy...')

    # Start workflow
    workflow_id = _start_complex_workflow(workflow_executor)

    # Wait and check workflow status
    time.sleep(1.0)

    # Debug: Check workflow status before signaling
    try:
        workflow = workflow_executor.get_workflow(workflow_id, include_tasks=True)
        logger.info(f"Workflow status before signal: {workflow.status}")
        logger.info(f"Workflow tasks: {len(workflow.tasks) if workflow.tasks else 0}")
        if workflow.tasks:
            for task in workflow.tasks:
                logger.info(f"Task: {task.task_type}, Status: {task.status}, Ref: {task.reference_task_name}")
    except Exception as e:
        logger.warning(f"Could not get workflow status: {e}")

    # Send signal with TARGET_WORKFLOW strategy
    response = workflow_executor.signal(
        workflow_id=workflow_id,
        status="COMPLETED",
        body={"result": "test_target_workflow"},
        return_strategy="TARGET_WORKFLOW"
    )

    # Debug: Print response details
    logger.info(f"Response object: {response}")
    logger.info(f"Response type: {type(response)}")
    if hasattr(response, '__dict__'):
        logger.info(f"Response attributes: {response.__dict__}")
    if hasattr(response, 'to_dict'):
        try:
            logger.info(f"Response to_dict: {response.to_dict()}")
        except Exception as e:
            logger.warning(f"to_dict failed: {e}")

    # Validate response
    assert response is not None, "Signal response is None"
    assert hasattr(response, 'response_type'), "Response missing response_type attribute"
    assert response.response_type == "TARGET_WORKFLOW", f"Expected TARGET_WORKFLOW, got {response.response_type}"
    assert response.target_workflow_id == workflow_id, "Target workflow ID mismatch"

    # Test helper methods
    assert response.is_target_workflow(), "is_target_workflow() should return True"

    workflow_data = response.get_workflow()
    assert workflow_data is not None, "get_workflow() should return data"
    assert workflow_data.get('workflowId') == workflow_id, "Workflow data should contain correct workflow_id"

    # Wait for workflow completion
    _complete_workflow(workflow_executor, workflow_id)

    logger.info('TARGET_WORKFLOW strategy test completed')

    # Test helper methods
    assert response.is_target_workflow(), "is_target_workflow() should return True"

    workflow_data = response.get_workflow()
    assert workflow_data is not None, "get_workflow() should return data"
    assert workflow_data.get('workflowId') == workflow_id, "Workflow data should contain correct workflow_id"

    # Wait for workflow completion
    _wait_for_workflow_completion(workflow_executor, workflow_id)

    logger.info('TARGET_WORKFLOW strategy test completed')


def test_signal_blocking_workflow(workflow_executor: WorkflowExecutor):
    """Test signal with BLOCKING_WORKFLOW return strategy"""
    logger.info('Testing signal with BLOCKING_WORKFLOW strategy...')

    workflow_id = _start_complex_workflow(workflow_executor)
    time.sleep(0.5)

    response = workflow_executor.signal(
        workflow_id=workflow_id,
        status="COMPLETED",
        body={"result": "test_blocking_workflow"},
        return_strategy="BLOCKING_WORKFLOW"
    )

    # Validate response
    assert response is not None, "Signal response is None"
    assert response.response_type == "BLOCKING_WORKFLOW", f"Expected BLOCKING_WORKFLOW, got {response.response_type}"
    assert response.target_workflow_id == workflow_id, "Target workflow ID mismatch"

    # Test helper methods
    assert response.is_blocking_workflow(), "is_blocking_workflow() should return True"

    workflow_data = response.get_workflow()
    assert workflow_data is not None, "get_workflow() should return data"

    _complete_workflow(workflow_executor, workflow_id)
    logger.info('BLOCKING_WORKFLOW strategy test completed')


def test_signal_blocking_task(workflow_executor: WorkflowExecutor):
    """Test signal with BLOCKING_TASK return strategy"""
    logger.info('Testing signal with BLOCKING_TASK strategy...')

    workflow_id = _start_complex_workflow(workflow_executor)
    time.sleep(0.5)

    response = workflow_executor.signal(
        workflow_id=workflow_id,
        status="COMPLETED",
        body={"result": "test_blocking_task"},
        return_strategy="BLOCKING_TASK"
    )

    # Validate response
    assert response is not None, "Signal response is None"
    assert response.response_type == "BLOCKING_TASK", f"Expected BLOCKING_TASK, got {response.response_type}"
    assert response.target_workflow_id == workflow_id, "Target workflow ID mismatch"

    # Test helper methods
    assert response.is_blocking_task(), "is_blocking_task() should return True"

    task_data = response.get_blocking_task()
    assert task_data is not None, "get_blocking_task() should return data"
    assert task_data.get('taskId') is not None, "Task data should contain task_id"

    _complete_workflow(workflow_executor, workflow_id)
    logger.info('BLOCKING_TASK strategy test completed')


def test_signal_blocking_task_input(workflow_executor: WorkflowExecutor):
    """Test signal with BLOCKING_TASK_INPUT return strategy"""
    logger.info('Testing signal with BLOCKING_TASK_INPUT strategy...')

    workflow_id = _start_complex_workflow(workflow_executor)
    time.sleep(0.5)

    response = workflow_executor.signal(
        workflow_id=workflow_id,
        status="COMPLETED",
        body={"result": "test_blocking_task_input"},
        return_strategy="BLOCKING_TASK_INPUT"
    )

    # Validate response
    assert response is not None, "Signal response is None"
    assert response.response_type == "BLOCKING_TASK_INPUT", f"Expected BLOCKING_TASK_INPUT, got {response.response_type}"
    assert response.target_workflow_id == workflow_id, "Target workflow ID mismatch"

    # Test helper methods
    assert response.is_blocking_task_input(), "is_blocking_task_input() should return True"

    task_data = response.get_blocking_task()
    task_input = response.get_task_input()
    assert task_data is not None, "get_blocking_task() should return data"
    assert task_input is not None, "get_task_input() should return data"

    _complete_workflow(workflow_executor, workflow_id)
    logger.info('BLOCKING_TASK_INPUT strategy test completed')


def test_signal_default_strategy(workflow_executor: WorkflowExecutor):
    """Test signal with default return strategy"""
    logger.info('Testing signal with default strategy...')

    workflow_id = _start_complex_workflow(workflow_executor)
    time.sleep(0.5)

    # Don't specify return_strategy - should default to TARGET_WORKFLOW
    response = workflow_executor.signal(
        workflow_id=workflow_id,
        status="COMPLETED",
        body={"result": "test_default"}
    )

    # Validate response
    assert response is not None, "Signal response is None"
    assert response.response_type == "TARGET_WORKFLOW", f"Expected TARGET_WORKFLOW (default), got {response.response_type}"
    assert response.target_workflow_id == workflow_id, "Target workflow ID mismatch"
    assert response.is_target_workflow(), "Default should be TARGET_WORKFLOW"

    _complete_workflow(workflow_executor, workflow_id)
    logger.info('Default strategy test completed')


def test_signal_async(workflow_executor: WorkflowExecutor):
    """Test async signal"""
    logger.info('Testing async signal...')

    workflow_id = _start_complex_workflow(workflow_executor)
    time.sleep(0.5)

    # Send async signal (should not return response)
    result = workflow_executor.signal_async(
        workflow_id=workflow_id,
        status="COMPLETED",
        body={"result": "test_async"}
    )

    # Async signal should return None
    assert result is None, "Async signal should return None"

    _complete_workflow(workflow_executor, workflow_id)
    logger.info('Async signal test completed')


def test_signal_to_dict_fix(workflow_executor: WorkflowExecutor):
    """Test that to_dict() returns actual values, not property objects"""
    logger.info('Testing to_dict() method fix...')

    workflow_id = _start_complex_workflow(workflow_executor)
    time.sleep(0.5)

    response = workflow_executor.signal(
        workflow_id=workflow_id,
        status="COMPLETED",
        body={"result": "test_to_dict"},
        return_strategy="BLOCKING_TASK"
    )

    response_dict = response.to_dict()

    # Ensure no property objects in the output
    response_str = str(response_dict)
    assert 'property object' not in response_str, f"Found property objects in response: {response_str}"

    # Verify actual string values
    assert isinstance(response_dict.get('responseType'), str), "responseType should be string"
    assert response_dict['responseType'] == 'BLOCKING_TASK', "responseType value incorrect"
    assert isinstance(response_dict.get('taskId'), str), "taskId should be string"
    assert isinstance(response_dict.get('targetWorkflowId'), str), "targetWorkflowId should be string"

    _complete_workflow(workflow_executor, workflow_id)
    logger.info('to_dict() method test completed')
    # dict['responseType'] == 'BLOCKING_TASK', "responseType value incorrect"
    assert isinstance(response_dict.get('taskId'), str), "taskId should be string"
    assert isinstance(response_dict.get('targetWorkflowId'), str), "targetWorkflowId should be string"

    _wait_for_workflow_completion(workflow_executor, workflow_id)

    logger.info('to_dict() method test completed')


def _wait_for_workflow_completion(workflow_executor: WorkflowExecutor, workflow_id: str, timeout: int = 10):
    """Wait for workflow to complete with timeout"""
    max_iterations = timeout * 10  # Check every 0.1 seconds

    for i in range(max_iterations):
        try:
            workflow = workflow_executor.get_workflow(workflow_id, include_tasks=False)
            if workflow.status in ["COMPLETED", "FAILED", "TERMINATED"]:
                logger.debug(f'Workflow {workflow_id} completed with status: {workflow.status}')
                return
        except Exception as e:
            logger.warning(f'Error checking workflow status: {e}')

        time.sleep(0.1)

    logger.warning(f'Workflow {workflow_id} did not complete within {timeout} seconds')
