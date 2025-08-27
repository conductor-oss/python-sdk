import os
import time
import uuid

import pytest

from conductor.client.adapters.models.correlation_ids_search_request_adapter import \
    CorrelationIdsSearchRequestAdapter as CorrelationIdsSearchRequest
from conductor.client.adapters.models.rerun_workflow_request_adapter import \
    RerunWorkflowRequestAdapter as RerunWorkflowRequest
from conductor.client.adapters.models.skip_task_request_adapter import \
    SkipTaskRequestAdapter as SkipTaskRequest
from conductor.client.adapters.models.start_workflow_request_adapter import \
    StartWorkflowRequestAdapter as StartWorkflowRequest
from conductor.client.adapters.models.workflow_def_adapter import \
    WorkflowDefAdapter as WorkflowDef
from conductor.client.adapters.models.workflow_state_update_adapter import \
    WorkflowStateUpdateAdapter as WorkflowStateUpdate
from conductor.client.adapters.models.workflow_task_adapter import \
    WorkflowTaskAdapter as WorkflowTask
from conductor.client.adapters.models.workflow_test_request_adapter import \
    WorkflowTestRequestAdapter as WorkflowTestRequest
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.rest import ApiException
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient


class TestOrkesWorkflowClientIntegration:
    """
    Integration tests for OrkesWorkflowClient.

    Environment Variables:
    - CONDUCTOR_SERVER_URL: Base URL for Conductor server (default: http://localhost:8080/api)
    - CONDUCTOR_AUTH_KEY: Authentication key for Orkes
    - CONDUCTOR_AUTH_SECRET: Authentication secret for Orkes
    - CONDUCTOR_UI_SERVER_URL: UI server URL (optional)
    - CONDUCTOR_TEST_TIMEOUT: Test timeout in seconds (default: 30)
    - CONDUCTOR_TEST_CLEANUP: Whether to cleanup test resources (default: true)
    """

    @pytest.fixture(scope="class")
    def configuration(self) -> Configuration:
        config = Configuration()
        config.debug = os.getenv("CONDUCTOR_DEBUG", "false").lower() == "true"
        config.apply_logging_config()
        return config

    @pytest.fixture(scope="class")
    def workflow_client(self, configuration: Configuration) -> OrkesWorkflowClient:
        return OrkesWorkflowClient(configuration)

    @pytest.fixture(scope="class")
    def metadata_client(self, configuration: Configuration) -> OrkesMetadataClient:
        return OrkesMetadataClient(configuration)

    @pytest.fixture(scope="class")
    def test_suffix(self) -> str:
        return str(uuid.uuid4())[:8]

    @pytest.fixture(scope="class")
    def test_workflow_name(self, test_suffix: str) -> str:
        return f"test_workflow_{test_suffix}"

    @pytest.fixture(scope="class")
    def simple_workflow_task(self) -> WorkflowTask:
        return WorkflowTask(
            name="test_task",
            task_reference_name="test_task_ref",
            type="HTTP",
            input_parameters={
                "http_request": {
                    "uri": "http://httpbin.org/get",
                    "method": "GET",
                }
            },
        )

    @pytest.fixture(scope="class")
    def simple_workflow_def(
        self, test_workflow_name: str, simple_workflow_task: WorkflowTask
    ) -> WorkflowDef:
        return WorkflowDef(
            name=test_workflow_name,
            version=1,
            description="A simple test workflow for integration testing",
            tasks=[simple_workflow_task],
            timeout_seconds=60,
            timeout_policy="TIME_OUT_WF",
            restartable=True,
            owner_email="test@example.com",
        )

    @pytest.fixture(scope="class")
    def simple_workflow_input(self) -> dict:
        return {
            "param1": "value1",
            "param2": "value2",
            "number": 42,
            "boolean": True,
            "array": [1, 2, 3],
            "object": {"nested": "value"},
        }

    @pytest.fixture(scope="class")
    def complex_workflow_input(self) -> dict:
        return {
            "user_id": "user_12345",
            "order_data": {
                "order_id": "order_67890",
                "items": [
                    {"product_id": "prod_1", "quantity": 2, "price": 29.99},
                    {"product_id": "prod_2", "quantity": 1, "price": 49.99},
                ],
                "shipping_address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "zip": "12345",
                },
            },
            "preferences": {
                "notifications": True,
                "language": "en",
                "timezone": "UTC",
            },
            "metadata": {
                "source": "integration_test",
                "timestamp": int(time.time()),
                "version": "1.0",
            },
        }

    @pytest.fixture(scope="class")
    def simple_start_workflow_request(
        self, test_workflow_name: str, simple_workflow_input: dict
    ) -> StartWorkflowRequest:
        return StartWorkflowRequest(
            name=test_workflow_name,
            version=1,
            input=simple_workflow_input,
            correlation_id=f"test_correlation_{str(uuid.uuid4())[:8]}",
            priority=0,
        )

    @pytest.fixture(scope="class")
    def complex_start_workflow_request(
        self, test_workflow_name: str, complex_workflow_input: dict
    ) -> StartWorkflowRequest:
        return StartWorkflowRequest(
            name=test_workflow_name,
            version=1,
            input=complex_workflow_input,
            correlation_id=f"complex_correlation_{str(uuid.uuid4())[:8]}",
            priority=1,
            created_by="integration_test",
            idempotency_key=f"idempotency_{str(uuid.uuid4())[:8]}",
        )

    @pytest.fixture(scope="class", autouse=True)
    def setup_workflow_definition(
        self, metadata_client: OrkesMetadataClient, simple_workflow_def: WorkflowDef
    ):
        """Create workflow definition before running tests."""
        try:
            metadata_client.register_workflow_def(simple_workflow_def, overwrite=True)
            time.sleep(1)
            yield
        finally:
            try:
                metadata_client.unregister_workflow_def(
                    simple_workflow_def.name, simple_workflow_def.version
                )
            except Exception as e:
                print(
                    f"Warning: Failed to cleanup workflow definition {simple_workflow_def.name}: {str(e)}"
                )

    def test_workflow_start_by_name(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:

            workflow_id = workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input=simple_workflow_input,
                version=1,
                correlationId=f"start_by_name_{str(uuid.uuid4())[:8]}",
                priority=0,
            )

            assert workflow_id is not None
            assert isinstance(workflow_id, str)
            assert len(workflow_id) > 0

            workflow = workflow_client.get_workflow(workflow_id, include_tasks=True)
            assert workflow.workflow_id == workflow_id
            assert workflow.workflow_name == test_workflow_name
            assert workflow.workflow_version == 1

        except Exception as e:
            print(f"Exception in test_workflow_start_by_name: {str(e)}")
            raise
        finally:
            try:
                if workflow_id:
                    workflow_client.delete_workflow(workflow_id, archive_workflow=True)
            except Exception as e:
                print(f"Warning: Failed to cleanup workflow: {str(e)}")

    def test_workflow_start_with_request(
        self,
        workflow_client: OrkesWorkflowClient,
        simple_start_workflow_request: StartWorkflowRequest,
    ):
        try:
            workflow_id = workflow_client.start_workflow(simple_start_workflow_request)

            assert workflow_id is not None
            assert isinstance(workflow_id, str)
            assert len(workflow_id) > 0

            workflow = workflow_client.get_workflow(workflow_id, include_tasks=True)
            assert workflow.workflow_id == workflow_id
            assert workflow.workflow_name == simple_start_workflow_request.name
            assert workflow.workflow_version == simple_start_workflow_request.version

        except Exception as e:
            print(f"Exception in test_workflow_start_with_request: {str(e)}")
            raise
        finally:
            try:
                workflow_client.delete_workflow(workflow_id, archive_workflow=True)
            except Exception as e:
                print(f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}")

    def test_workflow_execute_sync(
        self,
        workflow_client: OrkesWorkflowClient,
        simple_start_workflow_request: StartWorkflowRequest,
    ):
        try:
            workflow_run = workflow_client.execute_workflow(
                start_workflow_request=simple_start_workflow_request,
                request_id=f"execute_sync_{str(uuid.uuid4())[:8]}",
                wait_for_seconds=30,
            )

            assert workflow_run is not None
            assert hasattr(workflow_run, "workflow_id")
            assert hasattr(workflow_run, "status")

        except Exception as e:
            print(f"Exception in test_workflow_execute_sync: {str(e)}")
            raise

    def test_workflow_execute_with_return_strategy(
        self,
        workflow_client: OrkesWorkflowClient,
        simple_start_workflow_request: StartWorkflowRequest,
    ):
        try:
            signal_response = workflow_client.execute_workflow_with_return_strategy(
                start_workflow_request=simple_start_workflow_request,
                request_id=f"execute_strategy_{str(uuid.uuid4())[:8]}",
                wait_for_seconds=30,
                consistency="DURABLE",
                return_strategy="TARGET_WORKFLOW",
            )

            assert signal_response is not None

        except Exception as e:
            print(f"Exception in test_workflow_execute_with_return_strategy: {str(e)}")
            raise

    def test_workflow_pause_resume(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input=simple_workflow_input,
                version=1,
            )

            workflow_client.pause_workflow(workflow_id)

            workflow_status = workflow_client.get_workflow_status(workflow_id)
            assert workflow_status.status in ["PAUSED", "RUNNING"]

            workflow_client.resume_workflow(workflow_id)

            workflow_status_after_resume = workflow_client.get_workflow_status(
                workflow_id
            )
            assert workflow_status_after_resume.status in ["RUNNING", "COMPLETED"]

        except Exception as e:
            print(f"Exception in test_workflow_pause_resume: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    workflow_client.delete_workflow(workflow_id, archive_workflow=True)
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    def test_workflow_restart(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input=simple_workflow_input,
                version=1,
            )
            workflow_client.terminate_workflow(
                workflow_id,
                reason="Integration test termination",
                trigger_failure_workflow=False,
            )
            workflow_status = workflow_client.get_workflow_status(workflow_id)
            assert workflow_status.status == "TERMINATED"

            workflow_client.restart_workflow(workflow_id, use_latest_def=False)

            workflow_status = workflow_client.get_workflow_status(workflow_id)
            assert workflow_status.status in ["RUNNING", "COMPLETED"]

        except Exception as e:
            print(f"Exception in test_workflow_restart: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    workflow_client.delete_workflow(workflow_id, archive_workflow=True)
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    def test_workflow_rerun(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        original_workflow_id = None
        rerun_workflow_id = None
        try:
            original_workflow_id = workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input=simple_workflow_input,
                version=1,
            )

            workflow_client.terminate_workflow(
                original_workflow_id,
                reason="Integration test termination",
                trigger_failure_workflow=False,
            )
            workflow_status = workflow_client.get_workflow_status(original_workflow_id)
            assert workflow_status.status == "TERMINATED"

            rerun_request = RerunWorkflowRequest(
                correlation_id=f"rerun_correlation_{str(uuid.uuid4())[:8]}",
                workflow_input={"rerun_param": "rerun_value"},
            )

            rerun_workflow_id = workflow_client.rerun_workflow(
                original_workflow_id, rerun_request
            )

            assert rerun_workflow_id is not None
            assert isinstance(rerun_workflow_id, str)
            assert rerun_workflow_id == original_workflow_id

            rerun_workflow = workflow_client.get_workflow(rerun_workflow_id)
            assert rerun_workflow.workflow_id == rerun_workflow_id

        except Exception as e:
            print(f"Exception in test_workflow_rerun: {str(e)}")
            raise
        finally:
            for wf_id in [original_workflow_id, rerun_workflow_id]:
                if wf_id:
                    try:
                        workflow_client.delete_workflow(wf_id, archive_workflow=True)
                    except Exception as e:
                        print(f"Warning: Failed to cleanup workflow {wf_id}: {str(e)}")

    def test_workflow_retry(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input=simple_workflow_input,
                version=1,
            )

            workflow_client.terminate_workflow(
                workflow_id,
                reason="Integration test termination",
                trigger_failure_workflow=False,
            )
            workflow_status = workflow_client.get_workflow_status(workflow_id)
            assert workflow_status.status == "TERMINATED"

            workflow_client.retry_workflow(workflow_id, resume_subworkflow_tasks=False)

            workflow_status = workflow_client.get_workflow_status(workflow_id)
            assert workflow_status.status in ["RUNNING", "COMPLETED"]

        except Exception as e:
            print(f"Exception in test_workflow_retry: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    workflow_client.delete_workflow(workflow_id, archive_workflow=True)
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    def test_workflow_terminate(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input=simple_workflow_input,
                version=1,
            )

            workflow_client.terminate_workflow(
                workflow_id,
                reason="Integration test termination",
                trigger_failure_workflow=False,
            )

            workflow_status = workflow_client.get_workflow_status(workflow_id)
            assert workflow_status.status == "TERMINATED"

        except Exception as e:
            print(f"Exception in test_workflow_terminate: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    workflow_client.delete_workflow(workflow_id, archive_workflow=True)
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    def test_workflow_get_with_tasks(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input=simple_workflow_input,
                version=1,
            )

            workflow_with_tasks = workflow_client.get_workflow(
                workflow_id, include_tasks=True
            )
            assert workflow_with_tasks.workflow_id == workflow_id
            assert hasattr(workflow_with_tasks, "tasks")

            workflow_without_tasks = workflow_client.get_workflow(
                workflow_id, include_tasks=False
            )
            assert workflow_without_tasks.workflow_id == workflow_id

        except Exception as e:
            print(f"Exception in test_workflow_get_with_tasks: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    workflow_client.delete_workflow(workflow_id, archive_workflow=True)
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    def test_workflow_status_with_options(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input=simple_workflow_input,
                version=1,
            )

            status_with_output = workflow_client.get_workflow_status(
                workflow_id, include_output=True, include_variables=True
            )
            assert status_with_output.workflow_id == workflow_id
            assert hasattr(status_with_output, "status")

            status_without_output = workflow_client.get_workflow_status(
                workflow_id, include_output=False, include_variables=False
            )
            assert status_without_output.workflow_id == workflow_id

        except Exception as e:
            print(f"Exception in test_workflow_status_with_options: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    workflow_client.delete_workflow(workflow_id, archive_workflow=True)
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    def test_workflow_test(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        try:
            test_request = WorkflowTestRequest(
                name=test_workflow_name,
                version=1,
                input=simple_workflow_input,
                correlation_id=f"test_correlation_{str(uuid.uuid4())[:8]}",
            )

            test_result = workflow_client.test_workflow(test_request)

            assert test_result is not None
            assert hasattr(test_result, "workflow_id")

        except Exception as e:
            print(f"Exception in test_workflow_test: {str(e)}")
            raise

    def test_workflow_search(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input=simple_workflow_input,
                version=1,
            )

            search_results = workflow_client.search(
                start=0,
                size=10,
                free_text="*",
                query=None,
            )

            assert search_results is not None
            assert hasattr(search_results, "total_hits")
            assert hasattr(search_results, "results")

            search_results_with_query = workflow_client.search(
                start=0,
                size=5,
                free_text="*",
                query=f"workflowType:{test_workflow_name}",
            )

            assert search_results_with_query is not None

        except Exception as e:
            print(f"Exception in test_workflow_search: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    workflow_client.delete_workflow(workflow_id, archive_workflow=True)
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    def test_workflow_correlation_ids_batch(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_ids = []
        correlation_ids = []
        try:
            for i in range(3):
                correlation_id = f"batch_correlation_{i}_{str(uuid.uuid4())[:8]}"
                workflow_id = workflow_client.start_workflow_by_name(
                    name=test_workflow_name,
                    input=simple_workflow_input,
                    version=1,
                    correlationId=correlation_id,
                )
                workflow_ids.append(workflow_id)
                correlation_ids.append(correlation_id)

            batch_request = CorrelationIdsSearchRequest(
                correlation_ids=correlation_ids,
                workflow_names=[test_workflow_name],
            )

            batch_results = workflow_client.get_by_correlation_ids_in_batch(
                batch_request=batch_request,
                include_completed=False,
                include_tasks=False,
            )

            assert batch_results is not None
            assert isinstance(batch_results, dict)

        except Exception as e:
            print(f"Exception in test_workflow_correlation_ids_batch: {str(e)}")
            raise
        finally:
            for workflow_id in workflow_ids:
                try:
                    workflow_client.delete_workflow(workflow_id, archive_workflow=True)
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    def test_workflow_correlation_ids_simple(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_ids = []
        correlation_ids = []
        try:
            for i in range(2):
                correlation_id = f"simple_correlation_{i}_{str(uuid.uuid4())[:8]}"
                workflow_id = workflow_client.start_workflow_by_name(
                    name=test_workflow_name,
                    input=simple_workflow_input,
                    version=1,
                    correlationId=correlation_id,
                )
                workflow_ids.append(workflow_id)
                correlation_ids.append(correlation_id)

            correlation_results = workflow_client.get_by_correlation_ids(
                workflow_name=test_workflow_name,
                correlation_ids=correlation_ids,
                include_completed=False,
                include_tasks=False,
            )

            assert correlation_results is not None
            assert isinstance(correlation_results, dict)

        except Exception as e:
            print(f"Exception in test_workflow_correlation_ids_simple: {str(e)}")
            raise
        finally:
            for workflow_id in workflow_ids:
                try:
                    workflow_client.delete_workflow(workflow_id, archive_workflow=True)
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    def test_workflow_update_variables(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input=simple_workflow_input,
                version=1,
            )

            updated_variables = {
                "updated_var1": "updated_value1",
                "updated_var2": "updated_value2",
                "number_var": 100,
                "boolean_var": False,
            }

            workflow_client.update_variables(workflow_id, updated_variables)

            workflow = workflow_client.get_workflow(workflow_id, include_tasks=True)
            assert workflow.workflow_id == workflow_id

        except Exception as e:
            print(f"Exception in test_workflow_update_variables: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    workflow_client.delete_workflow(workflow_id, archive_workflow=True)
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    def test_workflow_update_state(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input=simple_workflow_input,
                version=1,
            )

            state_update = WorkflowStateUpdate(
                task_reference_name="test_task_ref",
                variables={"state_var1": "state_value1", "state_var2": "state_value2"},
            )

            workflow_run = workflow_client.update_state(
                workflow_id=workflow_id,
                update_request=state_update,
                wait_until_task_ref_names=["test_task_ref"],
                wait_for_seconds=30,
            )

            assert workflow_run is not None

        except Exception as e:
            print(f"Exception in test_workflow_update_state: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    workflow_client.delete_workflow(workflow_id, archive_workflow=True)
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    def test_concurrent_workflow_operations(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        try:
            import threading
            import time

            results = []
            errors = []
            created_workflows = []
            cleanup_lock = threading.Lock()

            def create_and_manage_workflow(workflow_suffix: str):
                workflow_id = None
                try:
                    workflow_id = workflow_client.start_workflow_by_name(
                        name=test_workflow_name,
                        input=simple_workflow_input,
                        version=1,
                        correlationId=f"concurrent_{workflow_suffix}",
                    )

                    with cleanup_lock:
                        created_workflows.append(workflow_id)

                    time.sleep(0.1)

                    workflow = workflow_client.get_workflow(workflow_id)
                    assert workflow.workflow_id == workflow_id

                    workflow_status = workflow_client.get_workflow_status(workflow_id)
                    assert workflow_status.workflow_id == workflow_id

                    if os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true":
                        try:
                            workflow_client.delete_workflow(
                                workflow_id, archive_workflow=True
                            )
                            with cleanup_lock:
                                if workflow_id in created_workflows:
                                    created_workflows.remove(workflow_id)
                        except Exception as cleanup_error:
                            print(
                                f"Warning: Failed to cleanup workflow {workflow_id} in thread: {str(cleanup_error)}"
                            )

                    results.append(f"workflow_{workflow_suffix}_success")
                except Exception as e:
                    errors.append(f"workflow_{workflow_suffix}_error: {str(e)}")
                    if workflow_id and workflow_id not in created_workflows:
                        with cleanup_lock:
                            created_workflows.append(workflow_id)

            threads = []
            for i in range(3):
                thread = threading.Thread(
                    target=create_and_manage_workflow, args=(f"{i}",)
                )
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            assert (
                len(results) == 3
            ), f"Expected 3 successful operations, got {len(results)}. Errors: {errors}"
            assert len(errors) == 0, f"Unexpected errors: {errors}"

        except Exception as e:
            print(f"Exception in test_concurrent_workflow_operations: {str(e)}")
            raise
        finally:
            for workflow_id in created_workflows:
                try:
                    workflow_client.delete_workflow(workflow_id, archive_workflow=True)
                except Exception as e:
                    print(f"Warning: Failed to delete workflow {workflow_id}: {str(e)}")

    def test_complex_workflow_management_flow(
        self,
        workflow_client: OrkesWorkflowClient,
        metadata_client: OrkesMetadataClient,
        test_suffix: str,
        simple_workflow_task: WorkflowTask,
    ):
        created_resources = {"workflows": [], "workflow_defs": []}

        try:
            workflow_types = {
                "simple": {"param1": "value1", "param2": "value2"},
                "complex": {
                    "user_data": {"id": "user_123", "name": "Test User"},
                    "order_data": {"items": [{"id": "item_1", "quantity": 2}]},
                },
                "batch": {
                    "batch_id": "batch_456",
                    "items": [
                        {"id": f"item_{i}", "data": f"data_{i}"} for i in range(5)
                    ],
                },
            }

            for workflow_type, input_data in workflow_types.items():
                workflow_name = f"complex_workflow_{workflow_type}_{test_suffix}"

                workflow_def = WorkflowDef(
                    name=workflow_name,
                    version=1,
                    description=f"Complex {workflow_type} workflow for testing",
                    tasks=[simple_workflow_task],
                    timeout_seconds=60,
                    timeout_policy="TIME_OUT_WF",
                    restartable=True,
                    owner_email="test@example.com",
                )

                metadata_client.register_workflow_def(workflow_def, overwrite=True)
                created_resources["workflow_defs"].append((workflow_name, 1))

                time.sleep(1)

                try:
                    retrieved_def = metadata_client.get_workflow_def(workflow_name)
                    assert retrieved_def.name == workflow_name
                    assert retrieved_def.version == 1
                except Exception as e:
                    print(
                        f"Warning: Could not verify workflow definition {workflow_name}: {str(e)}"
                    )

                correlation_id = f"complex_{workflow_type}_{test_suffix}"
                workflow_id = workflow_client.start_workflow_by_name(
                    name=workflow_name,
                    input=input_data,
                    version=1,
                    correlationId=correlation_id,
                    priority=0,
                )
                created_resources["workflows"].append(workflow_id)

                workflow = workflow_client.get_workflow(workflow_id, include_tasks=True)
                assert workflow.workflow_id == workflow_id
                assert workflow.workflow_name == workflow_name

                workflow_status = workflow_client.get_workflow_status(
                    workflow_id, include_output=True, include_variables=True
                )
                assert workflow_status.workflow_id == workflow_id

            search_results = workflow_client.search(
                start=0,
                size=20,
                free_text="*",
                query=f"correlationId:*{test_suffix}*",
            )

            assert search_results is not None
            assert hasattr(search_results, "total_hits")
            assert hasattr(search_results, "results")

            correlation_ids = [
                f"complex_{workflow_type}_{test_suffix}"
                for workflow_type in workflow_types.keys()
            ]

            batch_request = CorrelationIdsSearchRequest(
                correlation_ids=correlation_ids,
                workflow_names=[
                    f"complex_workflow_simple_{test_suffix}",
                    f"complex_workflow_complex_{test_suffix}",
                    f"complex_workflow_batch_{test_suffix}",
                ],
            )

            batch_results = workflow_client.get_by_correlation_ids_in_batch(
                batch_request=batch_request,
                include_completed=False,
                include_tasks=False,
            )

            assert batch_results is not None
            assert isinstance(batch_results, dict)

            for workflow_type in workflow_types.keys():
                workflow_name = f"complex_workflow_{workflow_type}_{test_suffix}"
                correlation_id = f"complex_{workflow_type}_{test_suffix}"
                correlation_results = workflow_client.get_by_correlation_ids(
                    workflow_name=workflow_name,
                    correlation_ids=[correlation_id],
                    include_completed=False,
                    include_tasks=False,
                )

                assert correlation_results is not None
                assert isinstance(correlation_results, dict)

        except Exception as e:
            print(f"Exception in test_complex_workflow_management_flow: {str(e)}")
            raise
        finally:
            self._perform_comprehensive_cleanup(
                workflow_client, metadata_client, created_resources, test_suffix
            )

    def _perform_comprehensive_cleanup(
        self,
        workflow_client: OrkesWorkflowClient,
        metadata_client: OrkesMetadataClient,
        created_resources: dict,
        test_suffix: str,
    ):
        cleanup_enabled = os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true"
        if not cleanup_enabled:
            return

        for workflow_id in created_resources["workflows"]:
            try:
                workflow_client.delete_workflow(workflow_id, archive_workflow=True)
            except Exception as e:
                print(f"Warning: Failed to delete workflow {workflow_id}: {str(e)}")

        for workflow_name, version in created_resources.get("workflow_defs", []):
            try:
                metadata_client.unregister_workflow_def(workflow_name, version)
            except Exception as e:
                print(
                    f"Warning: Failed to delete workflow definition {workflow_name}: {str(e)}"
                )

        remaining_workflows = []
        for workflow_id in created_resources["workflows"]:
            try:
                workflow_client.get_workflow(workflow_id)
                remaining_workflows.append(workflow_id)
            except ApiException as e:
                if e.code == 404:
                    pass
                else:
                    remaining_workflows.append(workflow_id)
            except Exception:
                remaining_workflows.append(workflow_id)

        if remaining_workflows:
            print(
                f"Warning: {len(remaining_workflows)} workflows could not be verified as deleted: {remaining_workflows}"
            )
