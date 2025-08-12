import os
import time

from conductor.client.ai.orchestrator import AIOrchestrator
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import TaskDef
from conductor.shared.http.enums import TaskResultStatus
from conductor.client.orkes_clients import OrkesClients
from conductor.client.worker.worker_task import worker_task
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.do_while_task import LoopTask
from conductor.client.workflow.task.dynamic_task import DynamicTask
from conductor.client.workflow.task.llm_tasks.llm_chat_complete import LlmChatComplete
from conductor.client.workflow.task.timeout_policy import TimeoutPolicy
from conductor.client.workflow.task.wait_task import WaitTask
from workers.chat_workers import collect_history


def start_workers(api_config):
    task_handler = TaskHandler(
        workers=[],
        configuration=api_config,
        scan_for_annotated_workers=True,
    )
    task_handler.start_processes()
    return task_handler


@worker_task(task_definition_name='get_weather')
def get_weather(city: str) -> str:
    return f'weather in {city} today is rainy'


@worker_task(task_definition_name='get_price_from_amazon')
def get_price_from_amazon(product: str) -> float:
    return 42.42


def main():
    llm_provider = 'open_ai_' + os.getlogin()
    chat_complete_model = 'gpt-4'

    api_config = Configuration()
    clients = OrkesClients(configuration=api_config)
    workflow_executor = clients.get_workflow_executor()
    workflow_client = clients.get_workflow_client()
    task_client = clients.get_task_client()
    metadata_client = clients.get_metadata_client()
    task_handler = start_workers(api_config=api_config)

    # register our two tasks
    metadata_client.register_task_def(task_def=TaskDef(name='get_weather'))
    metadata_client.register_task_def(task_def=TaskDef(name='get_price_from_amazon'))

    # Define and associate prompt with the AI integration
    prompt_name = 'chat_function_instructions'
    prompt_text = """
    You are a helpful assistant that can answer questions using tools provided.  
    You have the following tools specified as functions in python:
    1. get_weather(city:str) ->  str (useful to get weather for a city input is the city name or zipcode)
    2. get_price_from_amazon(str: item) -> float (useful to get the price of an item from amazon)
    When asked a question, you can use one of these functions to answer the question if required.
    If you have to call these functions, respond with a python code that will call this function. 
    When you have to call a function return in the following valid JSON format that can be parsed using json util:
    {
      "type": "function",
      "function": "ACTUAL_PYTHON_FUNCTION_NAME_TO_CALL_WITHOUT_PARAMETERS"
      "function_parameters": "PARAMETERS FOR THE FUNCTION as a JSON map with key as parameter name and value as parameter value"
    }
    """

    orchestrator = AIOrchestrator(api_configuration=api_config)
    orchestrator.add_prompt_template(prompt_name, prompt_text, 'chat instructions')

    # associate the prompts
    orchestrator.associate_prompt_template(prompt_name, llm_provider, [chat_complete_model])

    wf = ConductorWorkflow(name='my_function_chatbot', version=1, executor=workflow_executor)

    user_input = WaitTask(task_ref_name='get_user_input')

    collect_history_task = collect_history(task_ref_name='collect_history_ref',
                                           user_input=user_input.output('question'),
                                           history='${chat_complete_ref.input.messages}',
                                           assistant_response='${chat_complete_ref.output.result}')

    chat_complete = LlmChatComplete(task_ref_name='chat_complete_ref',
                                    llm_provider=llm_provider, model=chat_complete_model,
                                    instructions_template=prompt_name,
                                    messages=collect_history_task.output('result'))
    function_call = DynamicTask(task_reference_name='fn_call_ref', dynamic_task=chat_complete.output('function'))
    function_call.input_parameters['inputs'] = chat_complete.output('function_parameters')
    function_call.input_parameters['dynamicTaskInputParam'] = 'inputs'

    #  ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓
    loop_tasks = [user_input, collect_history_task, chat_complete, function_call]
    #  ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑

    chat_loop = LoopTask(task_ref_name='loop', iterations=3, tasks=loop_tasks)

    wf >> chat_loop

    # let's make sure we don't run it for more than 2 minutes -- avoid runaway loops
    wf.timeout_seconds(120).timeout_policy(timeout_policy=TimeoutPolicy.TIME_OUT_WORKFLOW)
    message = """
    AI Function call example.  
    This chatbot is programmed to handle two types of queries:
    1. Get the weather for a location
    2. Get the price of an item 
    """
    print(message)
    workflow_run = wf.execute(wait_until_task_ref=user_input.task_reference_name, wait_for_seconds=1)
    workflow_id = workflow_run.workflow_id
    while workflow_run.is_running():
        if workflow_run.current_task.workflow_task.task_reference_name == user_input.task_reference_name:
            function_call_task = workflow_run.get_task(task_reference_name=function_call.task_reference_name)
            if function_call_task is not None:
                assistant = function_call_task.output_data['result']
                print(f'assistant: {assistant}')
            if workflow_run.current_task.workflow_task.task_reference_name == user_input.task_reference_name:
                question = input('Question: >> ')
                task_client.update_task_sync(workflow_id=workflow_id, task_ref_name=user_input.task_reference_name,
                                             status=TaskResultStatus.COMPLETED,
                                             output={'question': question})
        time.sleep(0.5)
        workflow_run = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)

    print(f'{workflow_run.output}')
    task_handler.stop_processes()


if __name__ == '__main__':
    main()
