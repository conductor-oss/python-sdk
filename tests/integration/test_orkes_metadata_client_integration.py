import os
import uuid

import pytest

from conductor.client.http.models.task_def import \
    TaskDefAdapter as TaskDef
from conductor.client.http.models.workflow_def import \
    WorkflowDefAdapter as WorkflowDef
from conductor.client.http.models.workflow_task import \
    WorkflowTaskAdapter as WorkflowTask
from conductor.client.configuration.configuration import Configuration
from conductor.client.codegen.rest import ApiException
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient


class TestOrkesMetadataClientIntegration:
    """
    Integration tests for OrkesMetadataClient.

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
    def metadata_client(self, configuration: Configuration) -> OrkesMetadataClient:
        return OrkesMetadataClient(configuration)

    @pytest.fixture(scope="class")
    def test_suffix(self) -> str:
        return str(uuid.uuid4())[:8]

    @pytest.fixture(scope="class")
    def test_workflow_name(self, test_suffix: str) -> str:
        return f"test_workflow_{test_suffix}"

    @pytest.fixture(scope="class")
    def test_task_type(self, test_suffix: str) -> str:
        return f"test_task_{test_suffix}"

    @pytest.fixture(scope="class")
    def simple_workflow_task(self) -> WorkflowTask:
        return WorkflowTask(
            name="simple_task",
            task_reference_name="simple_task_ref",
            type="SIMPLE",
            input_parameters={},
        )

    @pytest.fixture(scope="class")
    def simple_workflow_def(
        self, test_suffix: str, simple_workflow_task: WorkflowTask
    ) -> WorkflowDef:
        return WorkflowDef(
            name=f"test_workflow_{test_suffix}",
            version=1,
            description="A simple test workflow",
            tasks=[simple_workflow_task],
            timeout_seconds=60,
            timeout_policy="TIME_OUT_WF",
            restartable=True,
            owner_email="test@example.com",
        )

    @pytest.fixture(scope="class")
    def complex_workflow_def(self, test_suffix: str) -> WorkflowDef:
        task1 = WorkflowTask(
            name="task1",
            task_reference_name="task1_ref",
            type="SIMPLE",
            input_parameters={"param1": "${workflow.input.value1}"},
        )
        task2 = WorkflowTask(
            name="task2",
            task_reference_name="task2_ref",
            type="SIMPLE",
            input_parameters={"param2": "${task1_ref.output.result}"},
        )
        task2.start_delay = 0
        task2.optional = False

        return WorkflowDef(
            name=f"test_complex_workflow_{test_suffix}",
            version=1,
            description="A complex test workflow with multiple tasks",
            tasks=[task1, task2],
            timeout_seconds=120,
            timeout_policy="TIME_OUT_WF",
            restartable=True,
            owner_email="test@example.com",
            input_parameters=["value1", "value2"],
            output_parameters={"result": "${task2_ref.output.final_result}"},
        )

    @pytest.fixture(scope="class")
    def simple_task_def(self, test_suffix: str) -> TaskDef:
        return TaskDef(
            name=f"test_task_{test_suffix}",
            description="A simple test task",
            timeout_seconds=30,
            total_timeout_seconds=60,
            retry_count=3,
            retry_logic="FIXED",
            retry_delay_seconds=5,
            timeout_policy="TIME_OUT_WF",
            response_timeout_seconds=30,
            concurrent_exec_limit=1,
            input_keys=["input_param"],
            output_keys=["output_param"],
            owner_email="test@example.com",
        )

    @pytest.mark.v3_21_16
    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_workflow_lifecycle_simple(
        self,
        metadata_client: OrkesMetadataClient,
        simple_workflow_def: WorkflowDef,
    ):
        try:
            metadata_client.register_workflow_def(simple_workflow_def, overwrite=True)

            retrieved_workflow = metadata_client.get_workflow_def(
                simple_workflow_def.name
            )
            assert retrieved_workflow.name == simple_workflow_def.name
            assert retrieved_workflow.version == simple_workflow_def.version
            assert retrieved_workflow.description == simple_workflow_def.description

            all_workflows = metadata_client.get_all_workflow_defs()
            workflow_names = [wf.name for wf in all_workflows]
            assert simple_workflow_def.name in workflow_names

        except Exception as e:
            print(f"Exception in test_workflow_lifecycle_simple: {str(e)}")
            raise
        finally:
            try:
                metadata_client.unregister_workflow_def(
                    simple_workflow_def.name, simple_workflow_def.version
                )
            except Exception as e:
                print(
                    f"Warning: Failed to cleanup workflow {simple_workflow_def.name}: {str(e)}"
                )

    @pytest.mark.v3_21_16
    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_workflow_lifecycle_complex(
        self,
        metadata_client: OrkesMetadataClient,
        complex_workflow_def: WorkflowDef,
    ):
        try:
            metadata_client.register_workflow_def(complex_workflow_def, overwrite=True)

            retrieved_workflow = metadata_client.get_workflow_def(
                complex_workflow_def.name
            )
            assert retrieved_workflow.name == complex_workflow_def.name
            assert retrieved_workflow.version == complex_workflow_def.version
            assert len(retrieved_workflow.tasks) == 2

        except Exception as e:
            print(f"Exception in test_workflow_lifecycle_complex: {str(e)}")
            raise
        finally:
            try:
                metadata_client.unregister_workflow_def(
                    complex_workflow_def.name, complex_workflow_def.version
                )
            except Exception as e:
                print(
                    f"Warning: Failed to cleanup workflow {complex_workflow_def.name}: {str(e)}"
                )

    @pytest.mark.v3_21_16
    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_workflow_versioning(
        self,
        metadata_client: OrkesMetadataClient,
        test_suffix: str,
        simple_workflow_task: WorkflowTask,
    ):
        workflow_name = f"test_versioned_workflow_{test_suffix}"
        try:
            workflow_v1 = WorkflowDef(
                name=workflow_name,
                version=1,
                description="Version 1 of the workflow",
                tasks=[simple_workflow_task],
                timeout_seconds=60,
                timeout_policy="TIME_OUT_WF",
                owner_email="test@example.com",
            )

            workflow_v2 = WorkflowDef(
                name=workflow_name,
                version=2,
                description="Version 2 of the workflow",
                tasks=[simple_workflow_task],
                timeout_seconds=120,
                timeout_policy="TIME_OUT_WF",
                owner_email="test@example.com",
            )

            metadata_client.register_workflow_def(workflow_v1, overwrite=True)
            metadata_client.register_workflow_def(workflow_v2, overwrite=True)

            retrieved_v1 = metadata_client.get_workflow_def(workflow_name, version=1)
            assert retrieved_v1.version == 1
            assert retrieved_v1.timeout_seconds == 60

            retrieved_v2 = metadata_client.get_workflow_def(workflow_name, version=2)
            assert retrieved_v2.version == 2
            assert retrieved_v2.timeout_seconds == 120

        except Exception as e:
            print(f"Exception in test_workflow_versioning: {str(e)}")
            raise
        finally:
            try:
                metadata_client.unregister_workflow_def(workflow_name, 1)
                metadata_client.unregister_workflow_def(workflow_name, 2)
            except Exception as e:
                print(f"Warning: Failed to cleanup workflow {workflow_name}: {str(e)}")

    @pytest.mark.v3_21_16
    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_workflow_update(
        self,
        metadata_client: OrkesMetadataClient,
        test_suffix: str,
        simple_workflow_task: WorkflowTask,
    ):
        workflow_name = f"test_workflow_update_{test_suffix}"
        try:
            initial_workflow = WorkflowDef(
                name=workflow_name,
                version=1,
                description="Initial workflow",
                tasks=[simple_workflow_task],
                timeout_seconds=60,
                timeout_policy="TIME_OUT_WF",
                owner_email="test@example.com",
            )

            metadata_client.register_workflow_def(initial_workflow, overwrite=True)

            retrieved_workflow = metadata_client.get_workflow_def(workflow_name)
            assert retrieved_workflow.description == "Initial workflow"

            updated_workflow = WorkflowDef(
                name=workflow_name,
                version=1,
                description="Updated workflow",
                tasks=[simple_workflow_task],
                timeout_seconds=120,
                timeout_policy="TIME_OUT_WF",
                owner_email="test@example.com",
            )

            metadata_client.update_workflow_def(updated_workflow, overwrite=True)

            updated_retrieved_workflow = metadata_client.get_workflow_def(workflow_name)
            assert updated_retrieved_workflow.description == "Updated workflow"
            assert updated_retrieved_workflow.timeout_seconds == 120

        except Exception as e:
            print(f"Exception in test_workflow_update: {str(e)}")
            raise
        finally:
            try:
                metadata_client.unregister_workflow_def(workflow_name, 1)
            except Exception as e:
                print(f"Warning: Failed to cleanup workflow {workflow_name}: {str(e)}")

    @pytest.mark.v3_21_16
    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_task_lifecycle(
        self,
        metadata_client: OrkesMetadataClient,
        simple_task_def: TaskDef,
    ):
        try:
            metadata_client.register_task_def(simple_task_def)

            retrieved_task = metadata_client.get_task_def(simple_task_def.name)
            assert retrieved_task["name"] == simple_task_def.name
            assert retrieved_task["description"] == simple_task_def.description
            assert retrieved_task["timeoutSeconds"] == simple_task_def.timeout_seconds

            all_tasks = metadata_client.get_all_task_defs()
            task_names = [task.name for task in all_tasks]
            assert simple_task_def.name in task_names

        except Exception as e:
            print(f"Exception in test_task_lifecycle: {str(e)}")
            raise
        finally:
            try:
                metadata_client.unregister_task_def(simple_task_def.name)
            except Exception as e:
                print(
                    f"Warning: Failed to cleanup task {simple_task_def.name}: {str(e)}"
                )

    @pytest.mark.v3_21_16
    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_task_update(
        self,
        metadata_client: OrkesMetadataClient,
        test_suffix: str,
    ):
        task_name = f"test_task_update_{test_suffix}"
        try:
            initial_task = TaskDef(
                name=task_name,
                description="Initial task",
                timeout_seconds=30,
                total_timeout_seconds=60,
                retry_count=3,
                retry_logic="FIXED",
                retry_delay_seconds=5,
                timeout_policy="TIME_OUT_WF",
                response_timeout_seconds=30,
                concurrent_exec_limit=1,
                owner_email="test@example.com",
            )

            metadata_client.register_task_def(initial_task)

            retrieved_task = metadata_client.get_task_def(task_name)
            assert retrieved_task["description"] == "Initial task"

            updated_task = TaskDef(
                name=task_name,
                description="Updated task",
                timeout_seconds=60,
                total_timeout_seconds=120,
                retry_count=5,
                retry_logic="FIXED",
                retry_delay_seconds=10,
                timeout_policy="TIME_OUT_WF",
                response_timeout_seconds=60,
                concurrent_exec_limit=2,
                owner_email="test@example.com",
            )

            metadata_client.update_task_def(updated_task)

            updated_retrieved_task = metadata_client.get_task_def(task_name)
            assert updated_retrieved_task["description"] == "Updated task"
            assert updated_retrieved_task["timeoutSeconds"] == 60
            assert updated_retrieved_task["retryCount"] == 5

        except Exception as e:
            print(f"Exception in test_task_update: {str(e)}")
            raise
        finally:
            try:
                metadata_client.unregister_task_def(task_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup task {task_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_workflow_tags(
        self,
        metadata_client: OrkesMetadataClient,
        test_suffix: str,
        simple_workflow_task: WorkflowTask,
    ):
        workflow_name = f"test_workflow_tags_{test_suffix}"
        try:
            workflow = WorkflowDef(
                name=workflow_name,
                version=1,
                description="Workflow with tags",
                tasks=[simple_workflow_task],
                timeout_seconds=60,
                timeout_policy="TIME_OUT_WF",
            )

            metadata_client.register_workflow_def(workflow, overwrite=True)

            tags = [
                MetadataTag("environment", "test"),
                MetadataTag("owner", "integration_test"),
                MetadataTag("priority", "high"),
            ]

            for tag in tags:
                metadata_client.add_workflow_tag(tag, workflow_name)

            retrieved_tags = metadata_client.get_workflow_tags(workflow_name)
            assert len(retrieved_tags) >= 3
            tag_keys = [tag["key"] for tag in retrieved_tags]
            assert "environment" in tag_keys
            assert "owner" in tag_keys
            assert "priority" in tag_keys

            tag_to_delete = MetadataTag("priority", "high")
            metadata_client.delete_workflow_tag(tag_to_delete, workflow_name)

            retrieved_tags_after_delete = metadata_client.get_workflow_tags(
                workflow_name
            )
            remaining_tag_keys = [tag["key"] for tag in retrieved_tags_after_delete]
            assert "priority" not in remaining_tag_keys

            metadata_client.set_workflow_tags(tags, workflow_name)

            final_tags = metadata_client.get_workflow_tags(workflow_name)
            final_tag_keys = [tag["key"] for tag in final_tags]
            assert "environment" in final_tag_keys
            assert "owner" in final_tag_keys
            assert "priority" in final_tag_keys

        except Exception as e:
            print(f"Exception in test_workflow_tags: {str(e)}")
            raise
        finally:
            try:
                metadata_client.unregister_workflow_def(workflow_name, 1)
            except Exception as e:
                print(f"Warning: Failed to cleanup workflow {workflow_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_task_tags(
        self,
        metadata_client: OrkesMetadataClient,
        test_suffix: str,
    ):
        task_name = f"test_task_tags_{test_suffix}"
        try:
            task = TaskDef(
                name=task_name,
                description="Task with tags",
                timeout_seconds=30,
                total_timeout_seconds=60,
                retry_count=3,
                retry_logic="FIXED",
                retry_delay_seconds=5,
                timeout_policy="TIME_OUT_WF",
                response_timeout_seconds=30,
                concurrent_exec_limit=1,
            )

            metadata_client.register_task_def(task)

            tags = [
                MetadataTag("category", "data_processing"),
                MetadataTag("team", "backend"),
                MetadataTag("criticality", "medium"),
            ]

            for tag in tags:
                metadata_client.addTaskTag(tag, task_name)

            retrieved_tags = metadata_client.getTaskTags(task_name)
            assert len(retrieved_tags) >= 3
            tag_keys = [tag["key"] for tag in retrieved_tags]
            assert "category" in tag_keys
            assert "team" in tag_keys
            assert "criticality" in tag_keys

            tag_to_delete = MetadataTag("criticality", "medium")
            metadata_client.deleteTaskTag(tag_to_delete, task_name)

            retrieved_tags_after_delete = metadata_client.getTaskTags(task_name)
            remaining_tag_keys = [tag["key"] for tag in retrieved_tags_after_delete]
            assert "criticality" not in remaining_tag_keys

            metadata_client.setTaskTags(tags, task_name)

            final_tags = metadata_client.getTaskTags(task_name)
            final_tag_keys = [tag["key"] for tag in final_tags]
            assert "category" in final_tag_keys
            assert "team" in final_tag_keys
            assert "criticality" in final_tag_keys

        except Exception as e:
            print(f"Exception in test_task_tags: {str(e)}")
            raise
        finally:
            try:
                metadata_client.unregister_task_def(task_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup task {task_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_metadata_not_found(self, metadata_client: OrkesMetadataClient):
        non_existent_workflow = f"non_existent_{str(uuid.uuid4())}"
        non_existent_task = f"non_existent_{str(uuid.uuid4())}"

        with pytest.raises(ApiException) as exc_info:
            metadata_client.get_workflow_def(non_existent_workflow)
        assert exc_info.value.code == 404

        with pytest.raises(ApiException) as exc_info:
            metadata_client.unregister_workflow_def(non_existent_workflow, 1)
        assert exc_info.value.code == 404

        with pytest.raises(ApiException) as exc_info:
            metadata_client.get_task_def(non_existent_task)
        assert exc_info.value.code == 404

        with pytest.raises(ApiException) as exc_info:
            metadata_client.unregister_task_def(non_existent_task)
        assert exc_info.value.code == 404

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_concurrent_metadata_operations(
        self,
        metadata_client: OrkesMetadataClient,
        test_suffix: str,
        simple_workflow_task: WorkflowTask,
    ):
        try:
            import threading
            import time

            results = []
            errors = []
            created_resources = {"workflows": [], "tasks": []}
            cleanup_lock = threading.Lock()

            def create_and_delete_workflow(workflow_suffix: str):
                workflow_name = None
                try:
                    workflow_name = f"concurrent_workflow_{workflow_suffix}"
                    workflow = WorkflowDef(
                        name=workflow_name,
                        version=1,
                        description=f"Concurrent workflow {workflow_suffix}",
                        tasks=[simple_workflow_task],
                        timeout_seconds=60,
                        timeout_policy="TIME_OUT_WF",
                    )

                    metadata_client.register_workflow_def(workflow, overwrite=True)

                    with cleanup_lock:
                        created_resources["workflows"].append((workflow_name, 1))

                    time.sleep(0.1)

                    retrieved_workflow = metadata_client.get_workflow_def(workflow_name)
                    assert retrieved_workflow.name == workflow_name

                    if os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true":
                        try:
                            metadata_client.unregister_workflow_def(workflow_name, 1)
                            with cleanup_lock:
                                if (workflow_name, 1) in created_resources["workflows"]:
                                    created_resources["workflows"].remove(
                                        (workflow_name, 1)
                                    )
                        except Exception as cleanup_error:
                            print(
                                f"Warning: Failed to cleanup workflow {workflow_name} in thread: {str(cleanup_error)}"
                            )

                    results.append(f"workflow_{workflow_suffix}_success")
                except Exception as e:
                    errors.append(f"workflow_{workflow_suffix}_error: {str(e)}")
                    if (
                        workflow_name
                        and (workflow_name, 1) not in created_resources["workflows"]
                    ):
                        with cleanup_lock:
                            created_resources["workflows"].append((workflow_name, 1))

            def create_and_delete_task(task_suffix: str):
                task_name = None
                try:
                    task_name = f"concurrent_task_{task_suffix}"
                    task = TaskDef(
                        name=task_name,
                        description=f"Concurrent task {task_suffix}",
                        timeout_seconds=30,
                        total_timeout_seconds=60,
                        retry_count=3,
                        retry_logic="FIXED",
                        retry_delay_seconds=5,
                        timeout_policy="TIME_OUT_WF",
                        response_timeout_seconds=30,
                        concurrent_exec_limit=1,
                    )

                    metadata_client.register_task_def(task)

                    with cleanup_lock:
                        created_resources["tasks"].append(task_name)

                    time.sleep(0.1)

                    retrieved_task = metadata_client.get_task_def(task_name)
                    assert retrieved_task["name"] == task_name

                    if os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true":
                        try:
                            metadata_client.unregister_task_def(task_name)
                            with cleanup_lock:
                                if task_name in created_resources["tasks"]:
                                    created_resources["tasks"].remove(task_name)
                        except Exception as cleanup_error:
                            print(
                                f"Warning: Failed to cleanup task {task_name} in thread: {str(cleanup_error)}"
                            )

                    results.append(f"task_{task_suffix}_success")
                except Exception as e:
                    errors.append(f"task_{task_suffix}_error: {str(e)}")
                    if task_name and task_name not in created_resources["tasks"]:
                        with cleanup_lock:
                            created_resources["tasks"].append(task_name)

            threads = []
            for i in range(3):
                workflow_thread = threading.Thread(
                    target=create_and_delete_workflow, args=(f"{test_suffix}_{i}",)
                )
                task_thread = threading.Thread(
                    target=create_and_delete_task, args=(f"{test_suffix}_{i}",)
                )
                threads.extend([workflow_thread, task_thread])
                workflow_thread.start()
                task_thread.start()

            for thread in threads:
                thread.join()

            assert (
                len(results) == 6
            ), f"Expected 6 successful operations, got {len(results)}. Errors: {errors}"
            assert len(errors) == 0, f"Unexpected errors: {errors}"

        except Exception as e:
            print(f"Exception in test_concurrent_metadata_operations: {str(e)}")
            raise
        finally:
            for workflow_name, version in created_resources["workflows"]:
                try:
                    metadata_client.unregister_workflow_def(workflow_name, version)
                except Exception as e:
                    print(
                        f"Warning: Failed to delete workflow {workflow_name}: {str(e)}"
                    )

            for task_name in created_resources["tasks"]:
                try:
                    metadata_client.unregister_task_def(task_name)
                except Exception as e:
                    print(f"Warning: Failed to delete task {task_name}: {str(e)}")

        remaining_workflows = []
        for workflow_name, version in created_resources["workflows"]:
            try:
                metadata_client.get_workflow_def(workflow_name, version=version)
                remaining_workflows.append((workflow_name, version))
            except ApiException as e:
                if e.code == 404:
                    pass
                else:
                    remaining_workflows.append((workflow_name, version))
            except Exception:
                remaining_workflows.append((workflow_name, version))

        remaining_tasks = []
        for task_name in created_resources["tasks"]:
            try:
                metadata_client.get_task_def(task_name)
                remaining_tasks.append(task_name)
            except ApiException as e:
                if e.code == 404:
                    pass
                else:
                    remaining_tasks.append(task_name)
            except Exception:
                remaining_tasks.append(task_name)

        if remaining_workflows or remaining_tasks:
            print(
                f"Warning: {len(remaining_workflows)} workflows and {len(remaining_tasks)} tasks could not be verified as deleted: {remaining_workflows}, {remaining_tasks}"
            )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_complex_metadata_management_flow(
        self, metadata_client: OrkesMetadataClient, test_suffix: str
    ):
        created_resources = {"workflows": [], "tasks": []}

        try:
            workflow_types = {
                "data_processing": "Data processing workflow",
                "notification": "Notification workflow",
                "reporting": "Reporting workflow",
                "integration": "Integration workflow",
            }

            for workflow_type, description in workflow_types.items():
                workflow_name = f"complex_{workflow_type}_{test_suffix}"
                task = WorkflowTask(
                    name=f"{workflow_type}_task",
                    task_reference_name=f"{workflow_type}_task_ref",
                    type="SIMPLE",
                    input_parameters={},
                )

                workflow = WorkflowDef(
                    name=workflow_name,
                    version=1,
                    description=description,
                    tasks=[task],
                    timeout_seconds=60,
                    timeout_policy="TIME_OUT_WF",
                    restartable=True,
                    owner_email="test@example.com",
                )

                metadata_client.register_workflow_def(workflow, overwrite=True)
                created_resources["workflows"].append((workflow_name, 1))

                tags = [
                    MetadataTag("type", workflow_type),
                    MetadataTag("environment", "test"),
                    MetadataTag("owner", "integration_test"),
                ]

                for tag in tags:
                    metadata_client.add_workflow_tag(tag, workflow_name)

            task_types = {
                "http_task": "HTTP request task",
                "email_task": "Email sending task",
                "database_task": "Database operation task",
                "file_task": "File processing task",
            }

            for task_type, description in task_types.items():
                task_name = f"complex_{task_type}_{test_suffix}"
                task = TaskDef(
                    name=task_name,
                    description=description,
                    timeout_seconds=30,
                    total_timeout_seconds=60,
                    retry_count=3,
                    retry_logic="FIXED",
                    retry_delay_seconds=5,
                    timeout_policy="TIME_OUT_WF",
                    response_timeout_seconds=30,
                    concurrent_exec_limit=1,
                )

                metadata_client.register_task_def(task)
                created_resources["tasks"].append(task_name)

                tags = [
                    MetadataTag("category", task_type),
                    MetadataTag("team", "backend"),
                    MetadataTag("criticality", "medium"),
                ]

                for tag in tags:
                    metadata_client.addTaskTag(tag, task_name)

            all_workflows = metadata_client.get_all_workflow_defs()
            workflow_names = [wf.name for wf in all_workflows]
            for workflow_name, version in created_resources["workflows"]:
                assert (
                    workflow_name in workflow_names
                ), f"Workflow {workflow_name} not found in list"

            all_tasks = metadata_client.get_all_task_defs()
            task_names = [task.name for task in all_tasks]
            for task_name in created_resources["tasks"]:
                assert task_name in task_names, f"Task {task_name} not found in list"

            for workflow_type in workflow_types.keys():
                workflow_name = f"complex_{workflow_type}_{test_suffix}"
                retrieved_workflow = metadata_client.get_workflow_def(workflow_name)
                assert retrieved_workflow.name == workflow_name

                retrieved_tags = metadata_client.get_workflow_tags(workflow_name)
                tag_keys = [tag["key"] for tag in retrieved_tags]
                assert "type" in tag_keys
                assert "environment" in tag_keys
                assert "owner" in tag_keys

            for task_type in task_types.keys():
                task_name = f"complex_{task_type}_{test_suffix}"
                retrieved_task = metadata_client.get_task_def(task_name)
                assert retrieved_task["name"] == task_name

                retrieved_tags = metadata_client.getTaskTags(task_name)
                tag_keys = [tag["key"] for tag in retrieved_tags]
                assert "category" in tag_keys
                assert "team" in tag_keys
                assert "criticality" in tag_keys

        except Exception as e:
            print(f"Exception in test_complex_metadata_management_flow: {str(e)}")
            raise
        finally:
            self._perform_comprehensive_cleanup(metadata_client, created_resources)

    def _perform_comprehensive_cleanup(
        self, metadata_client: OrkesMetadataClient, created_resources: dict
    ):
        cleanup_enabled = os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true"
        if not cleanup_enabled:
            return

        for workflow_name, version in created_resources["workflows"]:
            try:
                metadata_client.unregister_workflow_def(workflow_name, version)
            except Exception as e:
                print(f"Warning: Failed to delete workflow {workflow_name}: {str(e)}")

        for task_name in created_resources["tasks"]:
            try:
                metadata_client.unregister_task_def(task_name)
            except Exception as e:
                print(f"Warning: Failed to delete task {task_name}: {str(e)}")

        remaining_workflows = []
        for workflow_name, version in created_resources["workflows"]:
            try:
                metadata_client.get_workflow_def(workflow_name, version=version)
                remaining_workflows.append((workflow_name, version))
            except ApiException as e:
                if e.code == 404:
                    pass
                else:
                    remaining_workflows.append((workflow_name, version))
            except Exception:
                remaining_workflows.append((workflow_name, version))

        remaining_tasks = []
        for task_name in created_resources["tasks"]:
            try:
                metadata_client.get_task_def(task_name)
                remaining_tasks.append(task_name)
            except ApiException as e:
                if e.code == 404:
                    pass
                else:
                    remaining_tasks.append(task_name)
            except Exception:
                remaining_tasks.append(task_name)

        if remaining_workflows or remaining_tasks:
            print(
                f"Warning: {len(remaining_workflows)} workflows and {len(remaining_tasks)} tasks could not be verified as deleted: {remaining_workflows}, {remaining_tasks}"
            )
