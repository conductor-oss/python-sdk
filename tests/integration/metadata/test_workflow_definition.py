import time
from typing import List

from conductor.client.http.models import TaskDef
from conductor.client.http.rest import ApiException
from conductor.client.http.models.start_workflow_request import StartWorkflowRequest
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from conductor.client.workflow.task.do_while_task import LoopTask
from conductor.client.workflow.task.dynamic_fork_task import DynamicForkTask
from conductor.client.workflow.task.fork_task import ForkTask
from conductor.client.workflow.task.http_task import HttpTask, HttpInput
from conductor.client.workflow.task.join_task import JoinTask
from conductor.client.workflow.task.json_jq_task import JsonJQTask
from conductor.client.workflow.task.set_variable_task import SetVariableTask
from conductor.client.workflow.task.simple_task import SimpleTask
from conductor.client.workflow.task.sub_workflow_task import SubWorkflowTask, InlineSubWorkflowTask
from conductor.client.workflow.task.switch_task import SwitchTask
from conductor.client.workflow.task.terminate_task import TerminateTask, WorkflowStatus
from tests.integration.retry_helpers import retry_scenario

WORKFLOW_NAME = 'python_test_workflow'
TASK_NAME = 'python_test_simple_task'
WORKFLOW_OWNER_EMAIL = "test@test"


def run_workflow_definition_tests(workflow_executor: WorkflowExecutor, deadline=None) -> None:
    retry_scenario('test_kitchensink_workflow_registration',
                   test_kitchensink_workflow_registration, workflow_executor,
                   deadline=deadline)


def generate_tasks_defs() -> List[TaskDef]:
    python_simple_task_from_code = TaskDef(
        description="desc python_simple_task_from_code",
        owner_app="python_integration_test_app",
        timeout_seconds=3,
        response_timeout_seconds=2,
        created_by=WORKFLOW_OWNER_EMAIL,
        name="python_simple_task_from_code",
        input_keys=["input1"],
        output_keys=[],
        owner_email=WORKFLOW_OWNER_EMAIL,
    )

    return [python_simple_task_from_code]


def test_kitchensink_workflow_registration(workflow_executor: WorkflowExecutor) -> None:
    workflow = generate_sub_workflow(workflow_executor)
    try:
        workflow_executor.metadata_client.unregister_workflow_def_with_http_info(
            workflow.name, workflow.version
        )
    except:
        pass
    workflow.register(True)
    workflow = generate_workflow(workflow_executor)
    workflow_executor.metadata_client.register_task_def(generate_tasks_defs())
    try:
        workflow_executor.metadata_client.unregister_workflow_def_with_http_info(
            workflow.name, workflow.version
        )
    except:
        pass
    workflow.register(True)
    workflow_id = workflow_executor.start_workflow(
        start_workflow_request=StartWorkflowRequest(
            name=workflow.name,
            correlation_id='kitchensink_test'
        )
    )
    if type(workflow_id) != str or workflow_id == '':
        raise Exception(f'failed to start workflow, name: {WORKFLOW_NAME}')

    _terminate_with_retry(workflow_executor, workflow_id, reason="End test")


def _terminate_with_retry(workflow_executor: WorkflowExecutor, workflow_id: str,
                          reason: str, retries: int = 5) -> None:
    # Terminating a workflow that the server is still evaluating can transiently
    # return 423 Locked ("Unable to acquire lock"). Retry with backoff so the
    # test tolerates that race instead of failing.
    for attempt in range(retries):
        try:
            workflow_executor.terminate(workflow_id=workflow_id, reason=reason)
            return
        except ApiException as e:
            if e.status == 423 and attempt < retries - 1:
                time.sleep(1 << attempt)
                continue
            raise


def generate_simple_task(id: int) -> SimpleTask:
    return SimpleTask(
        task_def_name=TASK_NAME,
        task_reference_name=f'{TASK_NAME}_{id}'
    )


def generate_sub_workflow_inline_task(workflow_executor: WorkflowExecutor) -> InlineSubWorkflowTask:
    return InlineSubWorkflowTask(
        task_ref_name='python_sub_flow_inline_from_code',
        workflow=ConductorWorkflow(
            executor=workflow_executor,
            name='python_simple_workflow'
        ).add(
            task=generate_simple_task(0)
        )
    )


def generate_switch_task() -> SwitchTask:
    return SwitchTask(
        task_ref_name='fact_length',
        case_expression="$.number < 15 ? 'LONG':'LONG'",
        use_javascript=True,
    ).input(
        key='number',
        value='${workflow.input.number}',
    ).switch_case(
        case_name='LONG',
        tasks=[generate_simple_task(i) for i in range(1, 3)],
    ).default_case(
        tasks=[
            TerminateTask(
                task_ref_name="too_short",
                status=WorkflowStatus.FAILED,
                termination_reason="value too short",
            ),
        ],
    )


def generate_do_while_task() -> LoopTask:
    return LoopTask(
        task_ref_name="loop_until_success",
        iterations=2,
        tasks=generate_switch_task(),
    )


def generate_do_while_task_multiple() -> LoopTask:
    return LoopTask(
        task_ref_name="loop_until_success_multiple",
        iterations=1,
        tasks=[generate_simple_task(i) for i in range(13, 14)],
    )


def generate_fork_task(workflow_executor: WorkflowExecutor) -> ForkTask:
    return ForkTask(
        task_ref_name='forked',
        forked_tasks=[
            [
                generate_do_while_task(),
                generate_do_while_task_multiple(),
                generate_sub_workflow_inline_task(workflow_executor)
            ],
            [generate_simple_task(i) for i in range(3, 5)]
        ]
    )


def generate_join_task(workflow_executor: WorkflowExecutor, fork_task: ForkTask) -> JoinTask:
    return JoinTask(
        task_ref_name='join_forked',
        join_on=fork_task.to_workflow_task().join_on
    )


def generate_sub_workflow_task() -> SubWorkflowTask:
    return SubWorkflowTask(
        task_ref_name='sub_workflow',
        workflow_name='PopulationMinMax'
    )


def generate_set_variable_task() -> SetVariableTask:
    return SetVariableTask(
        task_ref_name='set_state'
    ).input(
        key='call_made', value=True
    ).input(
        key='number', value='value'
    )


def generate_dynamic_fork_task() -> DynamicForkTask:
    return DynamicForkTask(
        task_ref_name='dynamic_fork',
        join_task=JoinTask(
            'join', join_on=[]
        ),
    )


def generate_http_task(task_ref_name='http_task') -> HttpTask:
    return HttpTask(
        task_ref_name, HttpInput(
            uri="https://orkes-api-tester.orkesconductor.com/get"
        ),
    )


def generate_json_jq_task() -> JsonJQTask:
    return JsonJQTask(
        task_ref_name='jq',
        script='{ key3: (.key1.value1 + .key2.value2) }'
    ).input(
        key='value1', value=['a', 'b'],
    ).input(
        key='value2', value=['d', 'e'],
    )


def generate_sub_workflow(workflow_executor: WorkflowExecutor) -> ConductorWorkflow:
    workflow = (
        ConductorWorkflow(
            executor=workflow_executor,
            name="PopulationMinMax",
            description="Python workflow example from code",
            version=1234,
        )
        .owner_email(WORKFLOW_OWNER_EMAIL)
        .add(generate_set_variable_task())
    )
    return workflow


def generate_workflow(workflow_executor: WorkflowExecutor) -> ConductorWorkflow:
    fork_task = generate_fork_task(workflow_executor)

    workflow = ConductorWorkflow(
        executor=workflow_executor,
        name='test-python-sdk-workflow-as-code',
        description='Python workflow example from code',
        version=1234,
    ).add(
        generate_http_task("http_task_0")
    ).add(
        generate_simple_task(12)
    ).add(
        generate_set_variable_task()
    ).add(
        fork_task
    ).add(
        generate_join_task(workflow_executor, fork_task)
    ).owner_email(WORKFLOW_OWNER_EMAIL)

    workflow >> generate_sub_workflow_task() >> generate_json_jq_task()

    forked_task_1 = generate_http_task("http_task_1")
    forked_task_2 = generate_http_task("http_task_2")
    forked_task_31 = generate_http_task("http_task_31")
    forked_task_32 = generate_http_task("http_task_32")
    forked_task_41 = generate_http_task("http_task_41")
    forked_task_42 = generate_http_task("http_task_42")

    workflow >> [forked_task_1, forked_task_2]
    workflow >> [[forked_task_31, forked_task_32], [forked_task_41, forked_task_42]]

    return workflow
