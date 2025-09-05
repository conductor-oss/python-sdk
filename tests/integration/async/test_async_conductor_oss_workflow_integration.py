import asyncio
import os
import time
import uuid

import pytest
import pytest_asyncio

from conductor.asyncio_client.adapters.api_client_adapter import \
    ApiClientAdapter as ApiClient
from conductor.asyncio_client.adapters.models.extended_task_def_adapter import \
    ExtendedTaskDefAdapter as ExtendedTaskDef
from conductor.asyncio_client.adapters.models.extended_workflow_def_adapter import \
    ExtendedWorkflowDefAdapter as ExtendedWorkflowDef
from conductor.asyncio_client.adapters.models.rerun_workflow_request_adapter import \
    RerunWorkflowRequestAdapter as RerunWorkflowRequest
from conductor.asyncio_client.adapters.models.start_workflow_request_adapter import \
    StartWorkflowRequestAdapter as StartWorkflowRequest
from conductor.asyncio_client.adapters.models.workflow_task_adapter import \
    WorkflowTaskAdapter as WorkflowTask
from conductor.asyncio_client.adapters.models.workflow_test_request_adapter import \
    WorkflowTestRequestAdapter as WorkflowTestRequest
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_metadata_client import \
    OrkesMetadataClient
from conductor.asyncio_client.orkes.orkes_workflow_client import \
    OrkesWorkflowClient


@pytest.mark.v3_21_16
class TestConductorOssWorkflowIntegration:
    """
    Integration tests for Conductor OSS WorkflowClient running on localhost:8080.

    Environment Variables:
    - CONDUCTOR_SERVER_URL: Base URL for Conductor server (default: http://localhost:8080/api)
    - CONDUCTOR_TEST_TIMEOUT: Test timeout in seconds (default: 30)
    - CONDUCTOR_TEST_CLEANUP: Whether to cleanup test resources (default: true)
    - CONDUCTOR_DEBUG: Enable debug logging (default: false)
    """

    @pytest.fixture(scope="class")
    def configuration(self) -> Configuration:
        """Create configuration for Conductor OSS."""
        config = Configuration()
        config.debug = os.getenv("CONDUCTOR_DEBUG", "false").lower() == "true"
        config.apply_logging_config()
        return config

    @pytest_asyncio.fixture(scope="function")
    async def workflow_client(
        self, configuration: Configuration
    ) -> OrkesWorkflowClient:
        """Create workflow client for Conductor OSS."""
        async with ApiClient(configuration) as api_client:
            return OrkesWorkflowClient(configuration, api_client=api_client)

    @pytest_asyncio.fixture(scope="function")
    async def metadata_client(
        self, configuration: Configuration
    ) -> OrkesMetadataClient:
        """Create metadata client for Conductor OSS."""
        async with ApiClient(configuration) as api_client:
            return OrkesMetadataClient(configuration, api_client=api_client)

    @pytest.fixture(scope="class")
    def test_suffix(self) -> str:
        """Generate unique suffix for test resources."""
        return str(uuid.uuid4())[:8]

    @pytest.fixture(scope="class")
    def test_workflow_name(self, test_suffix: str) -> str:
        """Generate test workflow name."""
        return f"test_workflow_{test_suffix}"

    @pytest.fixture(scope="class")
    def test_task_name(self, test_suffix: str) -> str:
        """Generate test task name."""
        return f"test_task_{test_suffix}"

    @pytest.fixture(scope="class")
    def simple_task_def(self, test_task_name: str) -> ExtendedTaskDef:
        """Create a simple task definition."""
        return ExtendedTaskDef(
            name=test_task_name,
            description="A simple test task for integration testing",
            retry_count=3,
            retry_logic="FIXED",
            retry_delay_seconds=1,
            timeout_seconds=60,
            poll_timeout_seconds=60,
            response_timeout_seconds=60,
            concurrent_exec_limit=1,
            input_keys=["input_param"],
            output_keys=["output_param"],
            owner_email="test@example.com",
        )

    @pytest.fixture(scope="class")
    def simple_workflow_task(self, test_task_name: str) -> WorkflowTask:
        """Create a simple workflow task."""
        return WorkflowTask(
            name=test_task_name,
            task_reference_name="test_task_ref",
            type="SIMPLE",
            input_parameters={"input_param": "${workflow.input.input_param}"},
        )

    @pytest.fixture(scope="class")
    def http_poll_workflow_task(self) -> WorkflowTask:
        """Create an HTTP poll workflow task for testing."""
        return WorkflowTask(
            name="http_poll_task",
            task_reference_name="http_poll_task_ref",
            type="HTTP_POLL",
            input_parameters={
                "http_request": {
                    "uri": "http://httpbin.org/get",
                    "method": "GET",
                    "terminationCondition": "(function(){ return $.output.response.body.randomInt > 10;})();",
                    "pollingInterval": "20",
                    "pollingStrategy": "FIXED",
                }
            },
        )

    @pytest.fixture(scope="class")
    def simple_workflow_def(
        self, test_workflow_name: str, simple_workflow_task: WorkflowTask
    ) -> ExtendedWorkflowDef:
        """Create a simple workflow definition."""
        return ExtendedWorkflowDef(
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
    def http_poll_workflow_def(
        self, test_workflow_name: str, http_poll_workflow_task: WorkflowTask
    ) -> ExtendedWorkflowDef:
        """Create an HTTP poll workflow definition."""
        return ExtendedWorkflowDef(
            name=f"{test_workflow_name}_http_poll",
            version=1,
            description="An HTTP poll test workflow for integration testing",
            tasks=[http_poll_workflow_task],
            timeout_seconds=120,
            timeout_policy="TIME_OUT_WF",
            restartable=True,
            owner_email="test@example.com",
        )

    @pytest.fixture(scope="class")
    def simple_workflow_input(self) -> dict:
        """Create simple workflow input."""
        return {
            "input_param": "test_value",
            "param1": "value1",
            "param2": "value2",
            "number": 42,
            "boolean": True,
            "array": [1, 2, 3],
            "object": {"nested": "value"},
        }

    @pytest.fixture(scope="class")
    def complex_workflow_input(self) -> dict:
        """Create complex workflow input."""
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
        """Create simple start workflow request."""
        return StartWorkflowRequest(
            name=test_workflow_name,
            version=1,
            input_data=simple_workflow_input,
            correlation_id=f"test_correlation_{str(uuid.uuid4())[:8]}",
            priority=0,
        )

    @pytest.fixture(scope="class")
    def complex_start_workflow_request(
        self, test_workflow_name: str, complex_workflow_input: dict
    ) -> StartWorkflowRequest:
        """Create complex start workflow request."""
        return StartWorkflowRequest(
            name=test_workflow_name,
            version=1,
            input_data=complex_workflow_input,
            correlation_id=f"complex_correlation_{str(uuid.uuid4())[:8]}",
            priority=1,
            created_by="integration_test",
            idempotency_key=f"idempotency_{str(uuid.uuid4())[:8]}",
        )

    @pytest_asyncio.fixture(scope="function", autouse=True)
    async def setup_test_resources(
        self,
        metadata_client: OrkesMetadataClient,
        simple_task_def: ExtendedTaskDef,
        simple_workflow_def: ExtendedWorkflowDef,
        http_poll_workflow_def: ExtendedWorkflowDef,
    ):
        """Setup test resources before running tests."""
        created_resources = {"task_defs": [], "workflow_defs": []}

        try:
            await metadata_client.register_task_def(simple_task_def)
            created_resources["task_defs"].append(simple_task_def.name)

            await metadata_client.register_workflow_def(
                simple_workflow_def, overwrite=True
            )
            created_resources["workflow_defs"].append(
                (simple_workflow_def.name, simple_workflow_def.version)
            )

            await metadata_client.register_workflow_def(
                http_poll_workflow_def, overwrite=True
            )
            created_resources["workflow_defs"].append(
                (http_poll_workflow_def.name, http_poll_workflow_def.version)
            )

            await asyncio.sleep(2)
            yield
        finally:
            cleanup_enabled = (
                os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true"
            )
            if cleanup_enabled:
                for task_name in created_resources["task_defs"]:
                    try:
                        await metadata_client.unregister_task_def(task_name)
                    except Exception as e:
                        print(
                            f"Warning: Failed to cleanup task definition {task_name}: {str(e)}"
                        )

                for workflow_name, version in created_resources["workflow_defs"]:
                    try:
                        await metadata_client.unregister_workflow_def(
                            workflow_name, version
                        )
                    except Exception as e:
                        print(
                            f"Warning: Failed to cleanup workflow definition {workflow_name}: {str(e)}"
                        )

    @pytest.mark.asyncio
    async def test_workflow_start_by_name(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        """Test starting a workflow by name."""
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
            if workflow_id:
                try:
                    await workflow_client.delete_workflow(
                        workflow_id, archive_workflow=True
                    )
                except Exception as e:
                    print(f"Warning: Failed to cleanup workflow: {str(e)}")

    @pytest.mark.asyncio
    async def test_workflow_start_with_request(
        self,
        workflow_client: OrkesWorkflowClient,
        simple_start_workflow_request: StartWorkflowRequest,
    ):
        """Test starting a workflow with StartWorkflowRequest."""
        workflow_id = None
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
            if workflow_id:
                try:
                    await workflow_client.delete_workflow(
                        workflow_id, archive_workflow=True
                    )
                except Exception as e:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {str(e)}"
                    )

    @pytest.mark.asyncio
    async def test_workflow_pause_resume(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        """Test pausing and resuming a workflow."""
        workflow_id = None
        try:
            workflow_id = await workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                input_data=simple_workflow_input,
                version=1,
            )

            await workflow_client.pause_workflow(workflow_id)

            workflow = await workflow_client.get_workflow(workflow_id)
            assert workflow.status in ["PAUSED", "RUNNING"]

            await workflow_client.resume_workflow(workflow_id)

            workflow_after_resume = await workflow_client.get_workflow(workflow_id)
            assert workflow_after_resume.status in ["RUNNING", "COMPLETED"]

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

    @pytest.mark.asyncio
    async def test_workflow_restart(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        """Test restarting a workflow."""
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
            workflow = await workflow_client.get_workflow(workflow_id)
            assert workflow.status == "TERMINATED"

            await workflow_client.restart_workflow(
                workflow_id, use_latest_definitions=False
            )

            workflow = await workflow_client.get_workflow(workflow_id)
            assert workflow.status in ["RUNNING", "COMPLETED"]

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

    @pytest.mark.asyncio
    async def test_workflow_rerun(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        """Test rerunning a workflow."""
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
            workflow = await workflow_client.get_workflow(original_workflow_id)
            assert workflow.status == "TERMINATED"

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

    @pytest.mark.asyncio
    async def test_workflow_retry(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        """Test retrying a workflow."""
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
            workflow = await workflow_client.get_workflow(workflow_id)
            assert workflow.status == "TERMINATED"

            await workflow_client.retry_workflow(
                workflow_id, resume_subworkflow_tasks=False
            )

            workflow = await workflow_client.get_workflow(workflow_id)
            assert workflow.status in ["RUNNING", "COMPLETED"]

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

    @pytest.mark.asyncio
    async def test_workflow_terminate(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        """Test terminating a workflow."""
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

            workflow = await workflow_client.get_workflow(workflow_id)
            assert workflow.status == "TERMINATED"

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

    @pytest.mark.asyncio
    async def test_workflow_get_with_tasks(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        """Test getting workflow with and without tasks."""
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

    @pytest.mark.asyncio
    async def test_workflow_test(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        """Test workflow testing functionality."""
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

    @pytest.mark.asyncio
    async def test_workflow_correlation_ids_simple(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        """Test simple correlation IDs search."""
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

    @pytest.mark.asyncio
    async def test_http_poll_workflow(
        self,
        workflow_client: OrkesWorkflowClient,
        test_workflow_name: str,
        simple_workflow_input: dict,
    ):
        """Test HTTP poll workflow functionality."""
        workflow_id = None
        try:
            workflow_id = await workflow_client.start_workflow_by_name(
                name=f"{test_workflow_name}_http_poll",
                input_data=simple_workflow_input,
                version=1,
                correlation_id=f"http_poll_{str(uuid.uuid4())[:8]}",
            )

            assert workflow_id is not None
            assert isinstance(workflow_id, str)
            assert len(workflow_id) > 0

            await asyncio.sleep(5)

            workflow = await workflow_client.get_workflow(
                workflow_id, include_tasks=True
            )
            assert workflow.workflow_id == workflow_id
            assert workflow.workflow_name == f"{test_workflow_name}_http_poll"

        except Exception as e:
            print(f"Exception in test_http_poll_workflow: {str(e)}")
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
