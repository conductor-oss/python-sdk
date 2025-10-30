import os
import time
import uuid

import pytest

from conductor.asyncio_client.adapters.api_client_adapter import (
    ApiClientAdapter as ApiClient,
)
from conductor.asyncio_client.adapters.models.extended_task_def_adapter import (
    ExtendedTaskDefAdapter as ExtendedTaskDef,
)
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.asyncio_client.orkes.orkes_workflow_client import OrkesWorkflowClient
from conductor.asyncio_client.workflow.conductor_workflow import AsyncConductorWorkflow
from conductor.asyncio_client.workflow.executor.workflow_executor import (
    AsyncWorkflowExecutor,
)
from conductor.asyncio_client.workflow.task.dynamic_fork_task import DynamicForkTask
from conductor.asyncio_client.workflow.task.join_task import JoinTask


@pytest.fixture(scope="module")
def configuration():
    config = Configuration()
    config.debug = os.getenv("CONDUCTOR_DEBUG", "false").lower() == "true"
    config.apply_logging_config()
    return config


@pytest.fixture(scope="module")
def test_suffix():
    return str(uuid.uuid4())[:8]


@pytest.fixture(scope="module")
def test_task_name(test_suffix):
    return f"async_dynamic_fork_test_task_{test_suffix}"


@pytest.fixture(scope="module")
def test_workflow_name(test_suffix):
    return f"async_dynamic_fork_test_workflow_{test_suffix}"


@pytest.fixture(scope="module")
def test_task_def(test_task_name):
    return ExtendedTaskDef(
        name=test_task_name,
        description="Test task for async dynamic fork integration test",
        retry_count=3,
        retry_logic="FIXED",
        retry_delay_seconds=1,
        timeout_seconds=60,
        response_timeout_seconds=60,
        owner_email="test@example.com",
    )


@pytest.mark.v5_2_6
@pytest.mark.v4_1_73
@pytest.mark.v3_21_16
@pytest.mark.asyncio
async def test_async_dynamic_fork_task_with_separate_params(
    configuration,
    test_workflow_name,
    test_task_name,
    test_task_def,
):
    workflow_id = None

    async with ApiClient(configuration) as api_client:
        metadata_client = OrkesMetadataClient(configuration, api_client=api_client)
        workflow_client = OrkesWorkflowClient(configuration, api_client=api_client)
        workflow_executor = AsyncWorkflowExecutor(configuration, api_client=api_client)

        try:
            await metadata_client.register_task_def(test_task_def)
            time.sleep(1)

            join_task = JoinTask(task_ref_name="async_dynamic_join")
            dynamic_fork = DynamicForkTask(
                task_ref_name="async_dynamic_fork",
                tasks_param="dynamicTasks",
                tasks_input_param_name="dynamicTasksInputs",
                join_task=join_task,
            )

            dynamic_fork.input_parameters["dynamicTasks"] = [
                {
                    "name": test_task_name,
                    "taskReferenceName": f"{test_task_name}_1",
                    "type": "SIMPLE",
                },
                {
                    "name": test_task_name,
                    "taskReferenceName": f"{test_task_name}_2",
                    "type": "SIMPLE",
                },
            ]

            dynamic_fork.input_parameters["dynamicTasksInputs"] = [
                {"task_input_1": "value1"},
                {"task_input_2": "value2"},
            ]

            workflow = (
                AsyncConductorWorkflow(
                    executor=workflow_executor,
                    name=test_workflow_name,
                    description="Async test workflow for DynamicForkTask with separate params",
                    version=1,
                )
                .owner_email("test@example.com")
                .add(dynamic_fork)
            )

            await workflow.register(overwrite=True)
            time.sleep(2)

            registered_workflow = await metadata_client.get_workflow_def(
                test_workflow_name, version=1
            )
            assert registered_workflow is not None
            assert registered_workflow.name == test_workflow_name

            dynamic_fork_tasks = [
                task
                for task in registered_workflow.tasks
                if task.type == "FORK_JOIN_DYNAMIC"
            ]
            assert len(dynamic_fork_tasks) == 1

            dynamic_fork_task = dynamic_fork_tasks[0]
            assert dynamic_fork_task.dynamic_fork_tasks_param == "dynamicTasks"
            assert (
                dynamic_fork_task.dynamic_fork_tasks_input_param_name
                == "dynamicTasksInputs"
            )
            assert dynamic_fork_task.dynamic_fork_join_tasks_param is None

            workflow_id = await workflow_client.start_workflow_by_name(
                name=test_workflow_name,
                version=1,
                input_data={},
            )

            assert workflow_id is not None
            assert isinstance(workflow_id, str)
            assert len(workflow_id) > 0

            time.sleep(2)

            workflow_execution = await workflow_client.get_workflow(
                workflow_id, include_tasks=True
            )
            assert workflow_execution.workflow_id == workflow_id
            assert workflow_execution.workflow_name == test_workflow_name

        except Exception as e:
            print(f"Test failed with error: {str(e)}")
            raise

        finally:
            if workflow_id:
                try:
                    await workflow_client.terminate_workflow(
                        workflow_id,
                        reason="Integration test cleanup",
                        trigger_failure_workflow=False,
                    )
                    await workflow_client.delete_workflow(
                        workflow_id, archive_workflow=True
                    )
                except Exception as cleanup_error:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {cleanup_error}"
                    )

            try:
                await metadata_client.unregister_workflow_def(
                    test_workflow_name, version=1
                )
            except Exception as cleanup_error:
                print(
                    f"Warning: Failed to cleanup workflow definition: {cleanup_error}"
                )

            try:
                await metadata_client.unregister_task_def(test_task_name)
            except Exception as cleanup_error:
                print(f"Warning: Failed to cleanup task definition: {cleanup_error}")


@pytest.mark.v5_2_6
@pytest.mark.v4_1_73
@pytest.mark.v3_21_16
@pytest.mark.asyncio
async def test_async_dynamic_fork_task_with_combined_param(
    configuration,
    test_workflow_name,
    test_task_name,
    test_task_def,
):
    workflow_id = None
    workflow_name_combined = f"{test_workflow_name}_combined"

    async with ApiClient(configuration) as api_client:
        metadata_client = OrkesMetadataClient(configuration, api_client=api_client)
        workflow_client = OrkesWorkflowClient(configuration, api_client=api_client)
        workflow_executor = AsyncWorkflowExecutor(configuration, api_client=api_client)

        try:
            await metadata_client.register_task_def(test_task_def)
            time.sleep(1)

            workflow = AsyncConductorWorkflow(
                executor=workflow_executor,
                name=workflow_name_combined,
                description="Async test workflow for DynamicForkTask with combined param",
                version=1,
            ).owner_email("test@example.com")

            join_task = JoinTask(task_ref_name="async_dynamic_join_combined")
            dynamic_fork = DynamicForkTask(
                task_ref_name="async_dynamic_fork_combined",
                tasks_param="dynamicForkJoinTasks",
                join_task=join_task,
            )

            dynamic_fork.input_parameters["dynamicForkJoinTasks"] = [
                {
                    "task": {
                        "name": test_task_name,
                        "taskReferenceName": f"{test_task_name}_combined_1",
                        "type": "SIMPLE",
                    },
                    "input": {"combined_input_1": "value1"},
                },
                {
                    "task": {
                        "name": test_task_name,
                        "taskReferenceName": f"{test_task_name}_combined_2",
                        "type": "SIMPLE",
                    },
                    "input": {"combined_input_2": "value2"},
                },
            ]

            workflow.add(dynamic_fork)
            await workflow.register(overwrite=True)
            time.sleep(2)

            registered_workflow = await metadata_client.get_workflow_def(
                workflow_name_combined, version=1
            )
            assert registered_workflow is not None
            assert registered_workflow.name == workflow_name_combined

            workflow_id = await workflow_client.start_workflow_by_name(
                name=workflow_name_combined,
                version=1,
                input_data={},
            )

            assert workflow_id is not None
            assert isinstance(workflow_id, str)
            assert len(workflow_id) > 0

            time.sleep(2)

            workflow_execution = await workflow_client.get_workflow(
                workflow_id, include_tasks=True
            )
            assert workflow_execution.workflow_id == workflow_id
            assert workflow_execution.workflow_name == workflow_name_combined

        except Exception as e:
            print(f"Test failed with error: {str(e)}")
            raise

        finally:
            if workflow_id:
                try:
                    await workflow_client.terminate_workflow(
                        workflow_id,
                        reason="Integration test cleanup",
                        trigger_failure_workflow=False,
                    )
                    await workflow_client.delete_workflow(
                        workflow_id, archive_workflow=True
                    )
                except Exception as cleanup_error:
                    print(
                        f"Warning: Failed to cleanup workflow {workflow_id}: {cleanup_error}"
                    )

            try:
                await metadata_client.unregister_workflow_def(
                    workflow_name_combined, version=1
                )
            except Exception as cleanup_error:
                print(
                    f"Warning: Failed to cleanup workflow definition: {cleanup_error}"
                )

            try:
                await metadata_client.unregister_task_def(test_task_name)
            except Exception as cleanup_error:
                print(f"Warning: Failed to cleanup task definition: {cleanup_error}")
