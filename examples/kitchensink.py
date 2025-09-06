from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients
from conductor.client.worker.worker_task import worker_task
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.http_task import HttpTask
from conductor.client.workflow.task.javascript_task import JavascriptTask
from conductor.client.workflow.task.json_jq_task import JsonJQTask
from conductor.client.workflow.task.set_variable_task import SetVariableTask
from conductor.client.workflow.task.switch_task import SwitchTask
from conductor.client.workflow.task.terminate_task import TerminateTask, WorkflowStatus
from conductor.client.workflow.task.wait_task import WaitTask


@worker_task(task_definition_name='route')
def route(country: str) -> str:
    return f'routing the packages to {country}'


def start_workers(api_config):
    task_handler = TaskHandler(
        workers=[],
        configuration=api_config,
        scan_for_annotated_workers=True
    )
    task_handler.start_processes()
    return task_handler


def main():
    api_config = Configuration()
    api_config.apply_logging_config()

    clients = OrkesClients(configuration=api_config)
    workflow_executor = clients.get_workflow_executor()
    task_handler = start_workers(api_config)
    wf = ConductorWorkflow(name='kitchensink2', version=1, executor=workflow_executor)

    say_hello_js = """
    function greetings() {
        return {
            "text": "hello " + $.name,
            "url": "https://orkes-api-tester.orkesconductor.com/api"
        }
    }
    greetings();
    """

    js = JavascriptTask(task_ref_name='hello_script', script=say_hello_js, bindings={'name': '${workflow.input.name}'})

    # If using Orkes, remove the line
    js.input_parameter('evaluatorType', 'javascript')

    http_call = HttpTask(task_ref_name='call_remote_api', http_input={
        'uri': 'https://orkes-api-tester.orkesconductor.com/api'
    })

    sub_workflow = ConductorWorkflow(name='sub0', executor=workflow_executor)
    sub_workflow >> HttpTask(task_ref_name='call_remote_api', http_input={
        'uri': sub_workflow.input('uri')
    })
    sub_workflow.input_parameters({
        'uri': js.output('url')
    })

    wait_for_two_sec = WaitTask(task_ref_name='wait_for_2_sec', wait_for_seconds=2)
    jq_script = """
    { key3: (.key1.value1 + .key2.value2) }
    """
    jq = JsonJQTask(task_ref_name='jq_process', script=jq_script)
    jq.input_parameters.update({
        'key1': {'value1': ['a', 'b']},
        'key2': {'value2': ['d', 'e']}
    })

    set_wf_var = SetVariableTask(task_ref_name='set_wf_var_ref')
    set_wf_var.input_parameters.update({
        'var1': 'value1',
        'var2': 42,
        'var3': ['a', 'b', 'c']
    })
    switch = SwitchTask(task_ref_name='decide', case_expression=wf.input('country'))
    switch.switch_case('US', route(task_ref_name='us_routing', country=wf.input('country')))
    switch.switch_case('CA', route(task_ref_name='ca_routing', country=wf.input('country')))
    switch.default_case(TerminateTask(task_ref_name='bad_country_Ref', termination_reason='unsupported country',
                                      status=WorkflowStatus.TERMINATED))

    wf >> js >> [sub_workflow, [http_call, wait_for_two_sec]] >> jq >> set_wf_var >> switch
    wf.output_parameters({
        'greetings': js.output()
    })

    result = wf.execute(workflow_input={'name': 'Orkes', 'country': 'US'})
    op = result.output
    print(f'\n\nWorkflow output: {op}\n\n')
    print(f'See the execution at {api_config.ui_host}/execution/{result.workflow_id}')
    task_handler.stop_processes()


if __name__ == '__main__':
    main()
