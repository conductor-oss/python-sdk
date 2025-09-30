import os
import time
import uuid

import pytest
import pytest_asyncio

from conductor.asyncio_client.adapters.api_client_adapter import \
    ApiClientAdapter as ApiClient
from conductor.asyncio_client.adapters.models.correlation_ids_search_request_adapter import \
    CorrelationIdsSearchRequestAdapter as CorrelationIdsSearchRequest
from conductor.asyncio_client.adapters.models.extended_workflow_def_adapter import \
    ExtendedWorkflowDefAdapter as WorkflowDef
from conductor.asyncio_client.adapters.models.rerun_workflow_request_adapter import \
    RerunWorkflowRequestAdapter as RerunWorkflowRequest
from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import \
    StartWorkflowRequestAdapter as StartWorkflowRequest
from conductor.asyncio_client.adapters.models.workflow_state_update_adapter import \
    WorkflowStateUpdateAdapter as WorkflowStateUpdate
from conductor.asyncio_client.adapters.models.workflow_task_adapter import \
    WorkflowTaskAdapter as WorkflowTask
from conductor.asyncio_client.adapters.models.workflow_test_request_adapter import \
    WorkflowTestRequestAdapter as WorkflowTestRequest
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_metadata_client import \
    OrkesMetadataClient
from conductor.asyncio_client.orkes.orkes_workflow_client import \
    OrkesWorkflowClient


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

    @pytest_asyncio.fixture(scope="function")
    async def workflow_client(
        self, configuration: Configuration
    ) -> OrkesWorkflowClient:
        async with ApiClient(configuration) as api_client:
            return OrkesWorkflowClient(configuration, api_client=api_client)

    @pytest_asyncio.fixture(scope="function")
    async def metadata_client(
        self, configuration: Configuration
    ) -> OrkesMetadataClient:
        async with ApiClient(configuration) as api_client:
            return OrkesMetadataClient(configuration, api_client=api_client)

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
            type="HTTP_POLL",
            input_parameters={
                "http_request": {
                    "uri": "http://httpbin.org/get",
                    "method": "GET",
                    "terminationCondition": "(function(){ return $.output.response.body.randomInt > 10;})();",
                    "pollingInterval": "5",
                    "pollingStrategy": "FIXED",
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

    @pytest_asyncio.fixture(scope="function", autouse=True)
    async def setup_workflow_definition(
        self, metadata_client: OrkesMetadataClient, simple_workflow_def: WorkflowDef
    ):
        """Create workflow definition before running tests."""
        try:
            await metadata_client.register_workflow_def(
                simple_workflow_def, overwrite=True
            )
            time.sleep(1)
            yield
        finally:
            try:
                await metadata_client.unregister_workflow_def(
                    simple_workflow_def.name, simple_workflow_def.version
                )
            except Exception as e:
                print(
                    f"Warning: Failed to cleanup workflow definition {simple_workflow_def.name}: {str(e)}"
                )

    @pytest.mark.v3_21_16
    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_start_by_name(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:

            workflow_id = await workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input_data=simple_workflow_input,
                version=1,
                correlation_id=f"start_by_name_{str(uuid.uuid4())[:8]}",
                priority=0,
            )

            assert workflow_id is not None
            assert isinstance(workflow_id, str)
            assert len(workflow_id) > 0

            workflow = await workflow_client.get_workflow(
                workflow_id, include_tasks=True
            )
            assert workflow.workflow_id == workflow_id
            assert workflow.workflow_name == test_workflow_name
            assert workflow.workflow_version == 1

        except Exception as e:
            print(f"Exception in test_workflow_start_by_name: {str(e)}")
            raise
        finally:
            try:
                if workflow_id:
                    await workflow_client.delete_workflow(
                        workflow_id, archive_workflow=True
                    )
            except Exception as e:
                print(f"Warning: Failed to cleanup workflow: {str(e)}")

    @pytest.mark.v3_21_16
    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_start_with_request(
        self,
        workflow_client: OrkesWorkflowClient,
        simple_start_workflow_request: StartWorkflowRequest,
    ):
        try:
            workflow_id = await workflow_client.start_workflow(
                simple_start_workflow_request
            )

            assert workflow_id is not None
            assert isinstance(workflow_id, str)
            assert len(workflow_id) > 0

            workflow = await workflow_client.get_workflow(
                workflow_id, include_tasks=True
            )
            assert workflow.workflow_id == workflow_id
            assert workflow.workflow_name == simple_start_workflow_request.name
            assert workflow.workflow_version == simple_start_workflow_request.version

        except Exception as e:
            print(f"Exception in test_workflow_start_with_request: {str(e)}")
            raise
        finally:
            try:
                await workflow_client.delete_workflow(
                    workflow_id, archive_workflow=True
                )
            except Exception as e:
                print(f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_execute_sync(
        self,
        workflow_client: OrkesWorkflowClient,
        simple_start_workflow_request: StartWorkflowRequest,
    ):
        try:
            workflow_run = await workflow_client.execute_workflow(
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

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_execute_with_return_strategy(
        self,
        workflow_client: OrkesWorkflowClient,
        simple_start_workflow_request: StartWorkflowRequest,
    ):
        try:
            signal_response = (
                await workflow_client.execute_workflow_with_return_strategy(
                    start_workflow_request=simple_start_workflow_request,
                    request_id=f"execute_strategy_{str(uuid.uuid4())[:8]}",
                    wait_for_seconds=30,
                )
            )

            assert signal_response is not None

        except Exception as e:
            print(f"Exception in test_workflow_execute_with_return_strategy: {str(e)}")
            raise

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_pause_resume(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = await workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input_data=simple_workflow_input,
                version=1,
            )

            await workflow_client.pause_workflow(workflow_id)

            workflow_status = await workflow_client.get_workflow_status(workflow_id)
            assert workflow_status.status in ["PAUSED", "RUNNING"]

            await workflow_client.resume_workflow(workflow_id)

            workflow_status_after_resume = await workflow_client.get_workflow_status(
                workflow_id
            )
            assert workflow_status_after_resume.status in ["RUNNING", "COMPLETED"]

        except Exception as e:
            print(f"Exception in test_workflow_pause_resume: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    await workflow_client.delete_workflow(
                        workflow_id, archive_workflow=True
                    )
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_restart(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = await workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input_data=simple_workflow_input,
                version=1,
            )
            await workflow_client.terminate_workflow(
                workflow_id,
                reason="Integration test termination",
                trigger_failure_workflow=False,
            )
            workflow_status = await workflow_client.get_workflow_status(workflow_id)
            assert workflow_status.status == "TERMINATED"

            await workflow_client.restart_workflow(
                workflow_id, use_latest_definitions=False
            )

            workflow_status = await workflow_client.get_workflow_status(workflow_id)
            assert workflow_status.status in ["RUNNING", "COMPLETED"]

        except Exception as e:
            print(f"Exception in test_workflow_restart: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    await workflow_client.delete_workflow(
                        workflow_id, archive_workflow=True
                    )
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_rerun(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        original_workflow_id = None
        rerun_workflow_id = None
        try:
            original_workflow_id = await workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input_data=simple_workflow_input,
                version=1,
            )

            await workflow_client.terminate_workflow(
                original_workflow_id,
                reason="Integration test termination",
                trigger_failure_workflow=False,
            )
            workflow_status = await workflow_client.get_workflow_status(
                original_workflow_id
            )
            assert workflow_status.status == "TERMINATED"

            rerun_request = RerunWorkflowRequest(
                correlation_id=f"rerun_correlation_{str(uuid.uuid4())[:8]}",
                workflow_input={"rerun_param": "rerun_value"},
            )

            rerun_workflow_id = await workflow_client.rerun_workflow(
                original_workflow_id, rerun_request
            )

            assert rerun_workflow_id is not None
            assert isinstance(rerun_workflow_id, str)
            assert rerun_workflow_id == original_workflow_id

            rerun_workflow = await workflow_client.get_workflow(rerun_workflow_id)
            assert rerun_workflow.workflow_id == rerun_workflow_id

        except Exception as e:
            print(f"Exception in test_workflow_rerun: {str(e)}")
            raise
        finally:
            for wf_id in [original_workflow_id, rerun_workflow_id]:
                if wf_id:
                    try:
                        await workflow_client.delete_workflow(
                            wf_id, archive_workflow=True
                        )
                    except Exception as e:
                        print(f"Warning: Failed to cleanup workflow {wf_id}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_retry(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = await workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input_data=simple_workflow_input,
                version=1,
            )

            await workflow_client.terminate_workflow(
                workflow_id,
                reason="Integration test termination",
                trigger_failure_workflow=False,
            )
            workflow_status = await workflow_client.get_workflow_status(workflow_id)
            assert workflow_status.status == "TERMINATED"

            await workflow_client.retry_workflow(
                workflow_id, resume_subworkflow_tasks=False
            )

            workflow_status = await workflow_client.get_workflow_status(workflow_id)
            assert workflow_status.status in ["RUNNING", "COMPLETED"]

        except Exception as e:
            print(f"Exception in test_workflow_retry: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    await workflow_client.delete_workflow(
                        workflow_id, archive_workflow=True
                    )
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_terminate(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = await workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input_data=simple_workflow_input,
                version=1,
            )

            await workflow_client.terminate_workflow(
                workflow_id,
                reason="Integration test termination",
                trigger_failure_workflow=False,
            )

            workflow_status = await workflow_client.get_workflow_status(workflow_id)
            assert workflow_status.status == "TERMINATED"

        except Exception as e:
            print(f"Exception in test_workflow_terminate: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    await workflow_client.delete_workflow(
                        workflow_id, archive_workflow=True
                    )
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_get_with_tasks(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = await workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input_data=simple_workflow_input,
                version=1,
            )

            workflow_with_tasks = await workflow_client.get_workflow(
                workflow_id, include_tasks=True
            )
            assert workflow_with_tasks.workflow_id == workflow_id
            assert hasattr(workflow_with_tasks, "tasks")

            workflow_without_tasks = await workflow_client.get_workflow(
                workflow_id, include_tasks=False
            )
            assert workflow_without_tasks.workflow_id == workflow_id

        except Exception as e:
            print(f"Exception in test_workflow_get_with_tasks: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    await workflow_client.delete_workflow(
                        workflow_id, archive_workflow=True
                    )
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_status_with_options(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = await workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input_data=simple_workflow_input,
                version=1,
            )

            status_with_output = await workflow_client.get_workflow_status(
                workflow_id, include_output=True, include_variables=True
            )
            assert status_with_output.workflow_id == workflow_id
            assert hasattr(status_with_output, "status")

            status_without_output = await workflow_client.get_workflow_status(
                workflow_id, include_output=False, include_variables=False
            )
            assert status_without_output.workflow_id == workflow_id

        except Exception as e:
            print(f"Exception in test_workflow_status_with_options: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    await workflow_client.delete_workflow(
                        workflow_id, archive_workflow=True
                    )
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_test(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        try:
            test_request = WorkflowTestRequest(
                name=test_workflow_name,
                version=1,
                input_data=simple_workflow_input,
                correlation_id=f"test_correlation_{str(uuid.uuid4())[:8]}",
            )

            test_result = await workflow_client.test_workflow(test_request)

            assert test_result is not None
            assert hasattr(test_result, "workflow_id")

        except Exception as e:
            print(f"Exception in test_workflow_test: {str(e)}")
            raise

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_search(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = await workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input_data=simple_workflow_input,
                version=1,
            )

            search_results = await workflow_client.search(
                start=0,
                size=10,
                free_text="*",
                query=None,
            )

            assert search_results is not None
            assert hasattr(search_results, "total_hits")
            assert hasattr(search_results, "results")

            search_results_with_query = await workflow_client.search(
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
                    await workflow_client.delete_workflow(
                        workflow_id, archive_workflow=True
                    )
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_correlation_ids_batch(
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
                workflow_id = await workflow_client.start_workflow_by_name(
                    name=test_workflow_name,
                    input_data=simple_workflow_input,
                    version=1,
                    correlation_id=correlation_id,
                )
                workflow_ids.append(workflow_id)
                correlation_ids.append(correlation_id)

            batch_request = CorrelationIdsSearchRequest(
                correlation_ids=correlation_ids,
                workflow_names=[test_workflow_name],
            )

            batch_results = await workflow_client.get_by_correlation_ids_in_batch(
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
                    await workflow_client.delete_workflow(
                        workflow_id, archive_workflow=True
                    )
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_correlation_ids_simple(
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
                workflow_id = await workflow_client.start_workflow_by_name(
                    name=test_workflow_name,
                    input_data=simple_workflow_input,
                    version=1,
                    correlation_id=correlation_id,
                )
                workflow_ids.append(workflow_id)
                correlation_ids.append(correlation_id)

            correlation_results = await workflow_client.get_by_correlation_ids(
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
                    await workflow_client.delete_workflow(
                        workflow_id, archive_workflow=True
                    )
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_update_variables(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = await workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input_data=simple_workflow_input,
                version=1,
            )

            updated_variables = {
                "updated_var1": "updated_value1",
                "updated_var2": "updated_value2",
                "number_var": 100,
                "boolean_var": False,
            }

            await workflow_client.update_variables(workflow_id, updated_variables)

            workflow = await workflow_client.get_workflow(
                workflow_id, include_tasks=True
            )
            assert workflow.workflow_id == workflow_id

        except Exception as e:
            print(f"Exception in test_workflow_update_variables: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    await workflow_client.delete_workflow(
                        workflow_id, archive_workflow=True
                    )
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_workflow_update_state(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        workflow_id = None
        try:
            workflow_id = await workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input_data=simple_workflow_input,
                version=1,
            )

            state_update = WorkflowStateUpdate(
                task_reference_name="test_task_ref",
                variables={"state_var1": "state_value1", "state_var2": "state_value2"},
            )

            workflow_run = await workflow_client.update_workflow_and_task_state(
                workflow_id=workflow_id,
                workflow_state_update=state_update,
                wait_until_task_ref_name="test_task_ref",
                wait_for_seconds=30,
            )

            assert workflow_run is not None

        except Exception as e:
            print(f"Exception in test_workflow_update_state: {str(e)}")
            raise
        finally:
            if workflow_id:
                try:
                    await workflow_client.delete_workflow(
                        workflow_id, archive_workflow=True
                    )
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )
