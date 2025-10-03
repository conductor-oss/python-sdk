import os
import threading
import time
import uuid

import pytest
import httpx

from conductor.client.codegen.rest import ApiException
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import task
from conductor.client.http.models.start_workflow_request import \
    StartWorkflowRequestAdapter as StartWorkflowRequest
from conductor.client.http.models.task_def import TaskDefAdapter as TaskDef
from conductor.client.http.models.task_result import \
    TaskResultAdapter as TaskResult
from conductor.client.http.models.workflow import WorkflowAdapter as Workflow
from conductor.client.http.models.workflow_def import \
    WorkflowDefAdapter as WorkflowDef
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.client.orkes.orkes_task_client import OrkesTaskClient
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient
from conductor.shared.http.enums.task_result_status import TaskResultStatus


class TestOrkesTaskClientIntegration:
    """
    Integration tests for OrkesTaskClient.

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
        """Create configuration from environment variables."""
        config = Configuration()
        config.http_connection = httpx.Client(
            timeout=httpx.Timeout(600.0),
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=1, max_connections=1),
            http2=True
        )
        config.debug = os.getenv("CONDUCTOR_DEBUG", "false").lower() == "true"
        config.apply_logging_config()
        return config

    @pytest.fixture(scope="class")
    def task_client(self, configuration: Configuration) -> OrkesTaskClient:
        """Create OrkesTaskClient instance."""
        return OrkesTaskClient(configuration)

    @pytest.fixture(scope="class")
    def workflow_client(self, configuration: Configuration) -> OrkesWorkflowClient:
        """Create OrkesWorkflowClient instance."""
        return OrkesWorkflowClient(configuration)

    @pytest.fixture(scope="class")
    def metadata_client(self, configuration: Configuration) -> OrkesMetadataClient:
        """Create OrkesMetadataClient instance."""
        return OrkesMetadataClient(configuration)

    @pytest.fixture(scope="class")
    def test_suffix(self) -> str:
        """Generate unique suffix for test resources."""
        return str(uuid.uuid4())[:8]

    @pytest.fixture(scope="class")
    def test_task_type(self, test_suffix: str) -> str:
        """Generate test task type."""
        return f"test_task_{test_suffix}"

    @pytest.fixture(scope="class")
    def test_workflow_name(self, test_suffix: str) -> str:
        """Generate test workflow name."""
        return f"test_workflow_{test_suffix}"

    @pytest.fixture(scope="class")
    def test_worker_id(self, test_suffix: str) -> str:
        """Generate test worker ID."""
        return f"test_worker_{test_suffix}"

    @pytest.fixture(scope="class")
    def test_domain(self, test_suffix: str) -> str:
        """Generate test domain."""
        return f"test_domain_{test_suffix}"

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_task_definition_lifecycle(
        self, metadata_client: OrkesMetadataClient, test_task_type: str
    ):
        """Test complete task definition lifecycle: create, read, update, delete."""
        try:
            task_def = TaskDef(
                name=test_task_type,
                description="Test task for integration testing",
                owner_email="test@example.com",
                timeout_seconds=30,
                response_timeout_seconds=20,
                input_keys=["input1", "input2"],
                output_keys=["output1", "output2"],
            )

            metadata_client.register_task_def(task_def)

            retrieved_task_def = metadata_client.get_task_def(test_task_type)
            assert retrieved_task_def.get("name") == test_task_type
            assert (
                retrieved_task_def.get("description")
                == "Test task for integration testing"
            )

            task_defs = metadata_client.get_all_task_defs()
            task_names = [td.name for td in task_defs]
            assert test_task_type in task_names

            updated_task_def = TaskDef(
                name=test_task_type,
                description="Updated test task for integration testing",
                owner_email="test@example.com",
                timeout_seconds=60,
                response_timeout_seconds=40,
                input_keys=["input1", "input2", "input3"],
                output_keys=["output1", "output2", "output3"],
            )

            metadata_client.update_task_def(updated_task_def)

            retrieved_updated = metadata_client.get_task_def(test_task_type)
            assert (
                retrieved_updated.get("description")
                == "Updated test task for integration testing"
            )
            assert retrieved_updated.get("timeoutSeconds") == 60

        finally:
            try:
                metadata_client.unregister_task_def(test_task_type)
            except Exception:
                pass

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_workflow_definition_lifecycle(
        self,
        metadata_client: OrkesMetadataClient,
        test_workflow_name: str,
        test_task_type: str,
    ):
        """Test complete workflow definition lifecycle: create, read, update, delete."""
        try:
            workflow_def = WorkflowDef(
                name=test_workflow_name,
                description="Test workflow for integration testing",
                version=1,
                tasks=[
                    {
                        "name": test_task_type,
                        "taskReferenceName": "test_task_ref",
                        "type": "SIMPLE",
                    }
                ],
                input_parameters=[],
                output_parameters={},
                owner_email="test@example.com",
            )

            metadata_client.update_workflow_def(workflow_def)

            retrieved_workflow_def = metadata_client.get_workflow_def(
                test_workflow_name, 1
            )
            assert retrieved_workflow_def.name == test_workflow_name
            assert (
                retrieved_workflow_def.description
                == "Test workflow for integration testing"
            )

            workflow_defs = metadata_client.get_all_workflow_defs()
            workflow_names = [wd.name for wd in workflow_defs]
            assert test_workflow_name in workflow_names

        finally:
            try:
                metadata_client.unregister_workflow_def(test_workflow_name, 1)
            except Exception:
                pass

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_task_polling_lifecycle(
        self,
        task_client: OrkesTaskClient,
        workflow_client: OrkesWorkflowClient,
        metadata_client: OrkesMetadataClient,
        test_task_type: str,
        test_workflow_name: str,
        test_worker_id: str,
        test_domain: str,
    ):
        """Test complete task polling lifecycle: poll, batch poll, with different parameters."""
        try:
            task_def = TaskDef(
                name=test_task_type,
                description="Test task for polling",
                owner_email="test@example.com",
                timeout_seconds=30,
                response_timeout_seconds=20,
            )
            metadata_client.register_task_def(task_def)

            workflow_def = WorkflowDef(
                name=test_workflow_name,
                description="Test workflow for polling",
                version=1,
                tasks=[
                    {
                        "name": test_task_type,
                        "taskReferenceName": "test_task_ref",
                        "type": "SIMPLE",
                    }
                ],
                input_parameters=[],
                output_parameters={},
                owner_email="test@example.com",
            )
            metadata_client.update_workflow_def(workflow_def)

            polled_task = task_client.poll_task(test_task_type)
            assert polled_task.domain is None

            polled_task_with_worker = task_client.poll_task(
                test_task_type, worker_id=test_worker_id
            )
            assert polled_task_with_worker.domain is None

            polled_task_with_domain = task_client.poll_task(
                test_task_type, domain=test_domain
            )
            assert polled_task_with_domain.domain is None

            polled_task_with_both = task_client.poll_task(
                test_task_type, worker_id=test_worker_id, domain=test_domain
            )
            assert polled_task_with_both.domain is None

            batch_polled_tasks = task_client.batch_poll_tasks(test_task_type)
            assert isinstance(batch_polled_tasks, list)
            assert len(batch_polled_tasks) == 0

            batch_polled_tasks_with_count = task_client.batch_poll_tasks(
                test_task_type, count=5
            )
            assert isinstance(batch_polled_tasks_with_count, list)
            assert len(batch_polled_tasks_with_count) == 0

            batch_polled_tasks_with_timeout = task_client.batch_poll_tasks(
                test_task_type, timeout_in_millisecond=1000
            )
            assert isinstance(batch_polled_tasks_with_timeout, list)
            assert len(batch_polled_tasks_with_timeout) == 0

            batch_polled_tasks_with_all = task_client.batch_poll_tasks(
                test_task_type,
                worker_id=test_worker_id,
                count=3,
                timeout_in_millisecond=500,
                domain=test_domain,
            )
            assert isinstance(batch_polled_tasks_with_all, list)
            assert len(batch_polled_tasks_with_all) == 0

            queue_size = task_client.get_queue_size_for_task(test_task_type)
            assert isinstance(queue_size, int)
            assert queue_size >= 0

            poll_data = task_client.get_task_poll_data(test_task_type)
            assert isinstance(poll_data, list)

        finally:
            try:
                metadata_client.unregister_task_def(test_task_type)
                metadata_client.unregister_workflow_def(test_workflow_name, 1)
            except Exception:
                pass

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_task_execution_lifecycle(
        self,
        task_client: OrkesTaskClient,
        workflow_client: OrkesWorkflowClient,
        metadata_client: OrkesMetadataClient,
        test_task_type: str,
        test_workflow_name: str,
        test_worker_id: str,
    ):
        """Test complete task execution lifecycle: start workflow, poll task, update task, get task."""
        try:
            task_def = TaskDef(
                name=test_task_type,
                description="Test task for execution",
                owner_email="test@example.com",
                timeout_seconds=30,
                response_timeout_seconds=20,
            )
            metadata_client.register_task_def(task_def)

            workflow_def = WorkflowDef(
                name=test_workflow_name,
                description="Test workflow for execution",
                version=1,
                tasks=[
                    {
                        "name": test_task_type,
                        "taskReferenceName": "test_task_ref",
                        "type": "SIMPLE",
                    }
                ],
                input_parameters=[],
                output_parameters={},
                owner_email="test@example.com",
            )
            metadata_client.update_workflow_def(workflow_def)

            start_request = StartWorkflowRequest(
                name=test_workflow_name, version=1, input={"test_input": "test_value"}
            )
            workflow_id = workflow_client.start_workflow(start_request)
            assert workflow_id is not None

            time.sleep(2)

            polled_task = task_client.poll_task(
                test_task_type, worker_id=test_worker_id
            )

            if polled_task is not None:
                retrieved_task = task_client.get_task(polled_task.task_id)
                assert retrieved_task.task_id == polled_task.task_id
                assert retrieved_task.task_type == test_task_type

                log_message = f"Test log message from {test_worker_id}"
                task_client.add_task_log(polled_task.task_id, log_message)

                task_logs = task_client.get_task_logs(polled_task.task_id)
                assert isinstance(task_logs, list)
                assert len(task_logs) >= 1

                task_result = TaskResult(
                    workflow_instance_id=workflow_id,
                    task_id=polled_task.task_id,
                    status=TaskResultStatus.IN_PROGRESS,
                    output_data={"result": "task completed successfully"},
                )
                update_result = task_client.update_task(task_result)
                assert update_result is not None

                update_by_ref_result = task_client.update_task_by_ref_name(
                    workflow_id=workflow_id,
                    task_ref_name="test_task_ref",
                    status=TaskResultStatus.IN_PROGRESS,
                    output={"result": "updated by ref name"},
                    worker_id=test_worker_id,
                )
                assert update_by_ref_result is not None

                sync_result = task_client.update_task_sync(
                    workflow_id=workflow_id,
                    task_ref_name="test_task_ref",
                    status=TaskResultStatus.COMPLETED,
                    output={"result": "updated sync"},
                    worker_id=test_worker_id,
                )
                assert sync_result is not None
                assert isinstance(sync_result, Workflow)

            else:
                with pytest.raises(ApiException) as exc_info:
                    task_client.get_task("non_existent_task_id")
                assert exc_info.value.code == 404

        finally:
            try:
                metadata_client.unregister_task_def(test_task_type)
                metadata_client.unregister_workflow_def(test_workflow_name, 1)
            except Exception:
                pass

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_task_status_transitions(
        self,
        task_client: OrkesTaskClient,
        workflow_client: OrkesWorkflowClient,
        metadata_client: OrkesMetadataClient,
        test_task_type: str,
        test_workflow_name: str,
        test_worker_id: str,
    ):
        """Test task status transitions: IN_PROGRESS, COMPLETED, FAILED."""
        try:
            task_def = TaskDef(
                name=test_task_type,
                description="Test task for status transitions",
                owner_email="test@example.com",
                timeout_seconds=30,
                response_timeout_seconds=20,
            )
            metadata_client.register_task_def(task_def)

            workflow_def = WorkflowDef(
                name=test_workflow_name,
                description="Test workflow for status transitions",
                version=1,
                tasks=[
                    {
                        "name": test_task_type,
                        "taskReferenceName": "test_task_ref",
                        "type": "SIMPLE",
                    }
                ],
                input_parameters=[],
                output_parameters={},
                owner_email="test@example.com",
            )
            metadata_client.update_workflow_def(workflow_def)

            start_request = StartWorkflowRequest(
                name=test_workflow_name, version=1, input={"test_input": "status_test"}
            )
            workflow_id = workflow_client.start_workflow(start_request)

            time.sleep(2)

            polled_task = task_client.poll_task(
                test_task_type, worker_id=test_worker_id
            )

            if polled_task is not None:
                in_progress_result = TaskResult(
                    workflow_instance_id=workflow_id,
                    task_id=polled_task.task_id,
                    status=TaskResultStatus.IN_PROGRESS,
                    output_data={"status": "in_progress"},
                )
                task_client.update_task(in_progress_result)

                completed_result = TaskResult(
                    workflow_instance_id=workflow_id,
                    task_id=polled_task.task_id,
                    status=TaskResultStatus.COMPLETED,
                    output_data={"status": "completed", "result": "success"},
                )
                task_client.update_task(completed_result)

                failed_result = TaskResult(
                    workflow_instance_id=workflow_id,
                    task_id=polled_task.task_id,
                    status=TaskResultStatus.FAILED,
                    output_data={"status": "failed", "error": "test error"},
                )
                task_client.update_task(failed_result)

                terminal_error_result = TaskResult(
                    workflow_instance_id=workflow_id,
                    task_id=polled_task.task_id,
                    status=TaskResultStatus.FAILED_WITH_TERMINAL_ERROR,
                    output_data={"status": "terminal_error", "error": "terminal error"},
                )
                task_client.update_task(terminal_error_result)

        finally:
            try:
                metadata_client.unregister_task_def(test_task_type)
                metadata_client.unregister_workflow_def(test_workflow_name, 1)
            except Exception:
                pass

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_concurrent_task_operations(
        self,
        task_client: OrkesTaskClient,
        workflow_client: OrkesWorkflowClient,
        metadata_client: OrkesMetadataClient,
        test_suffix: str,
    ):
        """Test concurrent operations on multiple tasks."""
        try:
            task_types = []
            workflow_names = []
            workflow_ids = []

            for i in range(3):
                task_type = f"concurrent_task_{test_suffix}_{i}"
                workflow_name = f"concurrent_workflow_{test_suffix}_{i}"

                task_def = TaskDef(
                    name=task_type,
                    description=f"Concurrent test task {i}",
                    owner_email="test@example.com",
                    timeout_seconds=30,
                    response_timeout_seconds=20,
                )
                metadata_client.register_task_def(task_def)
                task_types.append(task_type)

                workflow_def = WorkflowDef(
                    name=workflow_name,
                    description=f"Concurrent test workflow {i}",
                    version=1,
                    tasks=[
                        {
                            "name": task_type,
                            "taskReferenceName": f"task_ref_{i}",
                            "type": "SIMPLE",
                        }
                    ],
                    input_parameters=[],
                    output_parameters={},
                    owner_email="test@example.com",
                )
                metadata_client.update_workflow_def(workflow_def)
                workflow_names.append(workflow_name)

                start_request = StartWorkflowRequest(
                    name=workflow_name,
                    version=1,
                    input={"test_input": "concurrent_test"},
                )
                workflow_id = workflow_client.start_workflow(start_request)
                workflow_ids.append(workflow_id)

            results = []
            errors = []

            def poll_and_update_task(task_type: str, worker_id: str):
                try:
                    task = task_client.poll_task(task_type, worker_id=worker_id)
                    if task is not None:
                        task_result = TaskResult(
                            workflow_instance_id=workflow_ids[i],
                            task_id=task.task_id,
                            status=TaskResultStatus.COMPLETED,
                            output_data={
                                "worker_id": worker_id,
                                "result": "concurrent_test",
                            },
                        )
                        update_result = task_client.update_task(task_result)
                        results.append(f"task_{task_type}_success")
                    else:
                        results.append(f"task_{task_type}_no_task")
                except Exception as e:
                    errors.append(f"task_{task_type}_error: {str(e)}")

            threads = []
            for i, task_type in enumerate(task_types):
                worker_id = f"concurrent_worker_{test_suffix}_{i}"
                thread = threading.Thread(
                    target=poll_and_update_task, args=(task_type, worker_id)
                )
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            assert (
                len(results) == 3
            ), f"Expected 3 operations, got {len(results)}. Errors: {errors}"
            assert len(errors) == 0, f"Unexpected errors: {errors}"

        finally:
            for task_type in task_types:
                try:
                    metadata_client.unregister_task_def(task_type)
                except Exception:
                    pass

            for workflow_name in workflow_names:
                try:
                    metadata_client.unregister_workflow_def(workflow_name, 1)
                except Exception:
                    pass

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_complex_task_workflow_scenario(
        self,
        task_client: OrkesTaskClient,
        workflow_client: OrkesWorkflowClient,
        metadata_client: OrkesMetadataClient,
        test_suffix: str,
    ):
        """
        Complex task workflow scenario demonstrating:
        - Multiple task types in a single workflow
        - Task dependencies and execution order
        - Task logging and monitoring
        - Error handling and recovery
        - Bulk operations
        """
        created_resources = {
            "task_defs": [],
            "workflow_defs": [],
            "workflows": [],
            "tasks": [],
        }

        try:
            task_types = ["data_processing", "validation", "notification", "cleanup"]
            task_defs = {}

            for task_type in task_types:
                full_task_type = f"{task_type}_task_{test_suffix}"
                task_def = TaskDef(
                    name=full_task_type,
                    description=f"Task for {task_type}",
                    owner_email="test@example.com",
                    timeout_seconds=60,
                    response_timeout_seconds=30,
                    input_keys=[f"{task_type}_input"],
                    output_keys=[f"{task_type}_output"],
                )

                created_task_def = metadata_client.register_task_def(task_def)
                task_defs[task_type] = created_task_def
                created_resources["task_defs"].append(full_task_type)

            workflow_name = f"complex_workflow_{test_suffix}"
            workflow_def = WorkflowDef(
                name=workflow_name,
                description="Complex workflow for integration testing",
                version=1,
                tasks=[
                    {
                        "name": f"data_processing_task_{test_suffix}",
                        "taskReferenceName": "data_processing",
                        "type": "SIMPLE",
                    },
                    {
                        "name": f"validation_task_{test_suffix}",
                        "taskReferenceName": "validation",
                        "type": "SIMPLE",
                        "inputParameters": {
                            "validation_input": "${data_processing.output.data_processing_output}"
                        },
                    },
                    {
                        "name": f"notification_task_{test_suffix}",
                        "taskReferenceName": "notification",
                        "type": "SIMPLE",
                        "inputParameters": {
                            "notification_input": "${validation.output.validation_output}"
                        },
                    },
                    {
                        "name": f"cleanup_task_{test_suffix}",
                        "taskReferenceName": "cleanup",
                        "type": "SIMPLE",
                    },
                ],
                input_parameters=["initial_data"],
                output_parameters={"final_result": "${cleanup.output.cleanup_output}"},
                owner_email="test@example.com",
            )

            created_workflow_def = metadata_client.update_workflow_def(workflow_def)
            created_resources["workflow_defs"].append((workflow_name, 1))

            workflow_instances = []
            for i in range(3):
                start_request = StartWorkflowRequest(
                    name=workflow_name,
                    version=1,
                    input={"initial_data": f"test_data_{i}"},
                )
                workflow_id = workflow_client.start_workflow(start_request)
                workflow_instances.append(workflow_id)
                created_resources["workflows"].append(workflow_id)

            for i, workflow_id in enumerate(workflow_instances):
                data_task = task_client.poll_task(
                    f"data_processing_task_{test_suffix}",
                    worker_id=f"worker_{test_suffix}_{i}",
                )
                if data_task:
                    task_client.add_task_log(
                        task_id=data_task.task_id,
                        log_message=f"Processing data for workflow {workflow_id}",
                    )

                    data_result = TaskResult(
                        workflow_instance_id=workflow_id,
                        task_id=data_task.task_id,
                        status=TaskResultStatus.COMPLETED,
                        output_data={"data_processing_output": f"processed_data_{i}"},
                    )
                    task_client.update_task(data_result)
                    created_resources["tasks"].append(data_task.task_id)

                # Wait for workflow to process data task completion and schedule validation task
                time.sleep(2)

                validation_task = task_client.poll_task(
                    f"validation_task_{test_suffix}",
                    worker_id=f"worker_{test_suffix}_{i}",
                )
                if validation_task:
                    task_client.add_task_log(
                        task_id=validation_task.task_id,
                        log_message=f"Validating data for workflow {workflow_id}",
                    )

                    validation_result = TaskResult(
                        workflow_instance_id=workflow_id,
                        task_id=validation_task.task_id,
                        status=TaskResultStatus.COMPLETED,
                        output_data={"validation_output": f"validated_data_{i}"},
                    )
                    task_client.update_task(validation_result)
                    created_resources["tasks"].append(validation_task.task_id)

                # Wait for workflow to process validation task completion and schedule notification task
                time.sleep(2)

                notification_task = task_client.poll_task(
                    f"notification_task_{test_suffix}",
                    worker_id=f"worker_{test_suffix}_{i}",
                )
                if notification_task:
                    task_client.add_task_log(
                        task_id=notification_task.task_id,
                        log_message=f"Sending notification for workflow {workflow_id}",
                    )

                    notification_result = TaskResult(
                        workflow_instance_id=workflow_id,
                        task_id=notification_task.task_id,
                        status=TaskResultStatus.COMPLETED,
                        output_data={"notification_output": f"notification_sent_{i}"},
                    )
                    task_client.update_task(notification_result)
                    created_resources["tasks"].append(notification_task.task_id)

                time.sleep(2)

                cleanup_task = task_client.poll_task(
                    f"cleanup_task_{test_suffix}", worker_id=f"worker_{test_suffix}_{i}"
                )
                if cleanup_task:
                    task_client.add_task_log(
                        task_id=cleanup_task.task_id,
                        log_message=f"Cleaning up for workflow {workflow_id}",
                    )
                    cleanup_result = TaskResult(
                        workflow_instance_id=workflow_id,
                        task_id=cleanup_task.task_id,
                        status=TaskResultStatus.COMPLETED,
                        output_data={"cleanup_output": f"cleanup_completed_{i}"},
                    )
                    task_client.update_task(cleanup_result)
                    created_resources["tasks"].append(cleanup_task.task_id)

            for task_id in created_resources["tasks"]:
                retrieved_task = task_client.get_task(task_id)
                assert retrieved_task.task_id == task_id

                task_logs = task_client.get_task_logs(task_id)
                assert len(task_logs) >= 1

                assert retrieved_task.status == "COMPLETED"

            for task_type in task_types:
                full_task_type = f"{task_type}_task_{test_suffix}"
                batch_tasks = task_client.batch_poll_tasks(
                    full_task_type, count=5, timeout_in_millisecond=1000
                )
                assert isinstance(batch_tasks, list)

                queue_size = task_client.get_queue_size_for_task(full_task_type)
                assert isinstance(queue_size, int)
                assert queue_size >= 0

                poll_data = task_client.get_task_poll_data(full_task_type)
                assert isinstance(poll_data, list)

            if created_resources["tasks"]:
                with pytest.raises(ValueError):
                    invalid_task_result = TaskResult(
                        task_id=created_resources["tasks"][0],
                        status="INVALID_STATUS",
                        output_data={"error": "test"},
                    )
                    try:
                        task_client.update_task(invalid_task_result)
                    except Exception as e:
                        print(f"Expected error with invalid status: {e}")

        except Exception as e:
            print(f"Error during complex scenario: {str(e)}")
            raise
        finally:
            self._perform_comprehensive_cleanup(metadata_client, created_resources)

    def _perform_comprehensive_cleanup(
        self, metadata_client: OrkesMetadataClient, created_resources: dict
    ):
        """
        Perform comprehensive cleanup of all created resources.
        Handles cleanup in the correct order to avoid dependency issues.
        """
        cleanup_enabled = os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true"
        if not cleanup_enabled:
            return

        for workflow_name, version in created_resources["workflow_defs"]:
            try:
                metadata_client.unregister_workflow_def(workflow_name, version)
            except Exception as e:
                print(
                    f"Warning: Failed to delete workflow definition {workflow_name}: {str(e)}"
                )

        for task_type in created_resources["task_defs"]:
            try:
                metadata_client.unregister_task_def(task_type)
            except Exception as e:
                print(
                    f"Warning: Failed to delete task definition {task_type}: {str(e)}"
                )
