import asyncio
import json
import random
import string
from dataclasses import dataclass
from typing import Dict, List

from conductor.asyncio_client.adapters.models import (ExtendedTaskDef,
                                                      TaskResult)
from conductor.asyncio_client.ai.orchestrator import AsyncAIOrchestrator
from conductor.asyncio_client.automator.task_handler import TaskHandler
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.http.api_client import ApiClient
from conductor.asyncio_client.http.models.workflow_state_update import \
    WorkflowStateUpdate
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients
from conductor.asyncio_client.worker.worker_task import worker_task
from conductor.asyncio_client.workflow.conductor_workflow import \
    AsyncConductorWorkflow
from conductor.asyncio_client.workflow.task.dynamic_task import DynamicTask
from conductor.asyncio_client.workflow.task.llm_tasks.llm_chat_complete import (
    ChatMessage, LlmChatComplete)
from conductor.asyncio_client.workflow.task.simple_task import SimpleTask
from conductor.asyncio_client.workflow.task.sub_workflow_task import \
    SubWorkflowTask
from conductor.asyncio_client.workflow.task.switch_task import SwitchTask
from conductor.asyncio_client.workflow.task.wait_task import WaitTask
from conductor.shared.ai.configuration import OpenAIConfig
from conductor.shared.ai.enums import LLMProvider
from conductor.shared.http.enums import TaskResultStatus
from conductor.shared.workflow.enums import TimeoutPolicy


@dataclass
class Customer:
    id: int
    name: str
    annual_spend: float
    country: str


def start_workers(api_config):
    task_handler = TaskHandler(
        workers=[],
        configuration=api_config,
        scan_for_annotated_workers=True,
    )
    task_handler.start_processes()
    return task_handler


@worker_task(task_definition_name="get_customer_list")
def get_customer_list() -> List[Customer]:
    customers = []
    for i in range(100):
        customer_name = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=5)
        )
        spend = random.randint(a=100000, b=9000000)
        customers.append(
            Customer(
                id=i, name="Customer " + customer_name, annual_spend=spend, country="US"
            )
        )
    return customers


@worker_task(task_definition_name="get_top_n")
def get_top_n_customers(n: int, customers: List[Customer]) -> List[Customer]:
    customers.sort(key=lambda x: x.annual_spend, reverse=True)
    end = min(n + 1, len(customers))
    return customers[1:end]


@worker_task(task_definition_name="generate_promo_code")
def generate_promo_code() -> str:
    res = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return res


@worker_task(task_definition_name="send_email")
def send_email(customer: list[Customer], promo_code: str) -> str:
    return f"Sent {promo_code} to {len(customer)} customers"


@worker_task(task_definition_name="create_workflow")
def create_workflow(
    steps: list[str],
    inputs: Dict[str, object],
) -> dict:
    workflow_def = {"name": "copilot_execution", "version": 1, "tasks": []}

    for step in steps:
        if step == "review":
            task_def = {
                "name": "review",
                "taskReferenceName": "review",
                "type": "HUMAN",
                "displayName": "review email",
                "formVersion": 0,
                "formTemplate": "email_review",
            }
        else:
            task_def = {"name": step, "taskReferenceName": step, "type": "SIMPLE"}

        if step in inputs:
            task_def["inputParameters"] = inputs[step]

        workflow_def["tasks"].append(task_def)

    return workflow_def


async def main():
    llm_provider = "openai"
    chat_complete_model = "gpt-5"
    api_config = Configuration()

    async with ApiClient(api_config) as api_client:
        clients = OrkesClients(api_client=api_client, configuration=api_config)

        workflow_executor = clients.get_workflow_executor()
        metadata_client = clients.get_metadata_client()
        workflow_client = clients.get_workflow_client()
        task_handler = start_workers(api_config=api_config)

        # register our two tasks
        await metadata_client.register_task_def(
            task_def=ExtendedTaskDef(
                name="get_weather", timeoutSeconds=3600, totalTimeoutSeconds=3600
            )
        )
        await metadata_client.register_task_def(
            task_def=ExtendedTaskDef(
                name="get_price_from_amazon",
                timeoutSeconds=3600,
                totalTimeoutSeconds=3600,
            )
        )

        # Define and associate prompt with the AI integration
        prompt_name = "chat_function_instructions"
        prompt_text = """
        You are a helpful assistant that can answer questions using tools provided.  
        You have the following tools specified as functions in python:
        1. get_customer_list() ->  Customer (useful to get the list of customers / all the customers / customers)
        2. generate_promo_code() -> str (useful to generate a promocode for the customer)
        3. send_email(customer: Customer, promo_code: str) (useful when sending an email to a customer, promo code is the output of the generate_promo_code function)
        4. get_top_n(n: int, customers: List[Customer]) -> List[Customer]
            (
                useful to get the top N customers based on their spend.
                customers as input can come from the output of get_customer_list function using ${get_customer_list.output.result} 
                reference.
                This function needs a list of customers as input to get the top N. 
            ).
        5. create_workflow(steps: List[str], inputs: dict[str, dict]) -> dict 
        (Useful to chain the function calls.  
        inputs are: 
            steps: which is the list of python functions to be executed
            inputs: a dictionary with key as the function name and value as the dictionary object that is given as the input
                    to the function when calling 
        ).
        6. review(input: str) (useful when you wan a human to review something)
        note, if you have to execute multiple steps, then you MUST use create_workflow function.  
        Do not call a function from another function to chain them.  
        
        When asked a question, you can use one of these functions to answer the question if required.
        
        If you have to call these functions, respond with a python code that will call this function. 
        Make sure, when you have to call a function return in the following valid JSON format that can be parsed directly as a json object:
        {
        "type": "function",
        "function": "ACTUAL_PYTHON_FUNCTION_NAME_TO_CALL_WITHOUT_PARAMETERS"
        "function_parameters": "PARAMETERS FOR THE FUNCTION as a JSON map with key as parameter name and value as parameter value"
        }
        
        Rule: Think about the steps to do this, but your output MUST be the above JSON formatted response.
        ONLY send the JSON response - nothing else!
        
        """
        open_ai_config = OpenAIConfig()

        orchestrator = AsyncAIOrchestrator(
            api_client=api_client, api_configuration=api_config
        )
        await orchestrator.add_ai_integration(
            ai_integration_name=llm_provider,
            provider=LLMProvider.OPEN_AI,
            models=[chat_complete_model],
            description="openai config",
            config=open_ai_config,
        )

        await orchestrator.add_prompt_template(
            prompt_name, prompt_text, "chat instructions"
        )

        # associate the prompts
        await orchestrator.associate_prompt_template(
            prompt_name, llm_provider, [chat_complete_model]
        )

        wf = AsyncConductorWorkflow(
            name="my_function_chatbot", version=1, executor=workflow_executor
        )

        user_input = WaitTask(task_ref_name="get_user_input")

        chat_complete = LlmChatComplete(
            task_ref_name="chat_complete_ref",
            llm_provider=llm_provider,
            model=chat_complete_model,
            instructions_template=prompt_name,
            messages=[ChatMessage(role="user", message=user_input.output("query"))],
            max_tokens=2048,
        )

        function_call = DynamicTask(
            task_reference_name="fn_call_ref", dynamic_task="SUB_WORKFLOW"
        )
        function_call.input_parameters["steps"] = chat_complete.output(
            "function_parameters.steps"
        )
        function_call.input_parameters["inputs"] = chat_complete.output(
            "function_parameters.inputs"
        )
        function_call.input_parameters["subWorkflowName"] = "copilot_execution"
        function_call.input_parameters["subWorkflowVersion"] = 1

        sub_workflow = SubWorkflowTask(
            task_ref_name="execute_workflow",
            workflow_name="copilot_execution",
            version=1,
        )

        create = SimpleTask(
            task_reference_name="create_workflow_task", task_def_name="create_workflow"
        )
        create.input_parameters["steps"] = chat_complete.output(
            "result.function_parameters.steps"
        )
        create.input_parameters["inputs"] = chat_complete.output(
            "result.function_parameters.inputs"
        )
        call_function = SwitchTask(
            task_ref_name="to_call_or_not",
            case_expression=chat_complete.output("result.function"),
        )
        call_function.switch_case("create_workflow", [create, sub_workflow])

        call_one_fun = DynamicTask(
            task_reference_name="call_one_fun_ref",
            dynamic_task=chat_complete.output("result.function"),
        )
        call_one_fun.input_parameters["inputs"] = chat_complete.output(
            "result.function_parameters"
        )
        call_one_fun.input_parameters["dynamicTaskInputParam"] = "inputs"

        call_function.default_case([call_one_fun])

        wf >> user_input >> chat_complete

        wf.timeout_seconds(120).timeout_policy(
            timeout_policy=TimeoutPolicy.TIME_OUT_WORKFLOW
        )
        message = """
        I am a helpful bot that can help with your customer management. 
        
        Here are some examples:
        
        1. Get me the list of top N customers
        2. Get the list of all the customers
        3. Get the list of top N customers and send them a promo code
        """
        print(message)
        workflow_run = await wf.execute(
            wait_until_task_ref=user_input.task_reference_name, wait_for_seconds=120
        )
        workflow_id = workflow_run.workflow_id
        query = input(">> ")
        input_task = workflow_run.get_task(
            task_reference_name=user_input.task_reference_name
        )
        workflow_run = await workflow_client.update_state(
            workflow_id=workflow_id,
            update_request=WorkflowStateUpdate(
                task_reference_name=user_input.task_reference_name,
                task_result=TaskResult(
                    task_id=input_task.task_id,
                    output_data={"query": query},
                    status=TaskResultStatus.COMPLETED,
                ),
            ),
        )

        task_handler.stop_processes()
        output = json.dumps(workflow_run.output["result"], indent=3)
        print(
            f"""
        
        {output}
        
        """
        )

        print(
            f"""
        See the complete execution graph here: 
        
        http://localhost:5001/execution/{workflow_id}
        
        """
        )


if __name__ == "__main__":
    asyncio.run(main())
