"""
Function Calling Example - LLM Invokes Python Workers as Tools

Demonstrates how an LLM can dynamically call Python worker functions based on
user queries. The LLM analyzes the request, decides which function to call,
and Conductor executes the corresponding worker via a DYNAMIC task.

Available tools:
    - get_weather(city) -- get current weather
    - get_price(product) -- look up product prices
    - calculate(expression) -- evaluate math expressions
    - get_top_customers(n) -- get top N customers by spend

Pipeline:
    loop(wait_for_user --> chat_complete --> dynamic_function_call)

Requirements:
    - Conductor server with AI/LLM support
    - LLM provider named 'openai' with a valid API key configured
    - export CONDUCTOR_SERVER_URL=http://localhost:7001/api

Usage:
    python examples/agentic_workflows/function_calling_example.py
"""

import json
import math
import random
import time
from dataclasses import dataclass

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.orkes_clients import OrkesClients
from conductor.client.worker.worker_task import worker_task
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.do_while_task import LoopTask
from conductor.client.workflow.task.llm_tasks.llm_chat_complete import LlmChatComplete, ChatMessage
from conductor.client.workflow.task.timeout_policy import TimeoutPolicy
from conductor.client.workflow.task.wait_task import WaitTask

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LLM_PROVIDER = "openai"
LLM_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """
You are a helpful assistant with access to the following tools (Python functions):

1. get_weather(city: str) -> dict
   Get current weather for a city.

2. get_price(product: str) -> dict
   Look up the price of a product.

3. calculate(expression: str) -> dict
   Evaluate a math expression. Supports sqrt, pow, log, sin, cos, pi, e.

4. get_top_customers(n: int) -> list
   Get the top N customers by annual spend.

When you need to use a tool, respond with ONLY this JSON (no other text):
{
    "type": "function",
    "function": "FUNCTION_NAME",
    "function_parameters": {"param1": "value1"}
}

If you don't need a tool, respond normally with text.
"""


# ---------------------------------------------------------------------------
# Workers (tools for the LLM)
# ---------------------------------------------------------------------------

@dataclass
class Customer:
    id: int
    name: str
    annual_spend: float


# ---------------------------------------------------------------------------
# Tool functions (called by dispatch_function, NOT registered as workers)
# ---------------------------------------------------------------------------

def get_weather(city: str) -> dict:
    """Get current weather for a city."""
    weather_db = {
        'new york': {'temp': 72, 'condition': 'Partly Cloudy'},
        'san francisco': {'temp': 58, 'condition': 'Foggy'},
        'miami': {'temp': 85, 'condition': 'Sunny'},
        'chicago': {'temp': 45, 'condition': 'Windy'},
        'london': {'temp': 55, 'condition': 'Rainy'},
        'tokyo': {'temp': 68, 'condition': 'Clear'},
    }
    data = weather_db.get(city.lower(), {'temp': 70, 'condition': 'Clear'})
    return {'city': city, 'temperature_f': data['temp'], 'condition': data['condition']}


def get_price(product: str) -> dict:
    """Look up the price of a product."""
    prices = {
        'laptop': 999.99, 'headphones': 79.99, 'keyboard': 49.99,
        'mouse': 29.99, 'monitor': 349.99, 'webcam': 69.99,
    }
    query = product.lower()
    for name, price in prices.items():
        if query in name or name in query:
            return {'product': name, 'price': price, 'currency': 'USD'}
    return {'product': product, 'price': None, 'message': 'Product not found'}


def calculate(expression: str) -> dict:
    """Evaluate a math expression safely."""
    safe_builtins = {
        'abs': abs, 'round': round, 'min': min, 'max': max,
        'sqrt': math.sqrt, 'pow': pow, 'log': math.log,
        'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
        'pi': math.pi, 'e': math.e,
    }
    try:
        result = eval(expression, {"__builtins__": {}}, safe_builtins)
        return {'expression': expression, 'result': result}
    except Exception as e:
        return {'expression': expression, 'error': str(e)}


def get_top_customers(n: int) -> list:
    """Get top N customers by annual spend."""
    customers = [
        Customer(i, f"Customer_{random.randint(1000,9999)}", random.randint(100_000, 9_000_000))
        for i in range(50)
    ]
    customers.sort(key=lambda c: c.annual_spend, reverse=True)
    return [
        {'id': c.id, 'name': c.name, 'annual_spend': c.annual_spend}
        for c in customers[:n]
    ]


TOOL_REGISTRY = {
    "get_weather": get_weather,
    "get_price": get_price,
    "calculate": calculate,
    "get_top_customers": get_top_customers,
}


@worker_task(task_definition_name='dispatch_function')
def dispatch_function(llm_response: dict = None) -> dict:
    """Parse the LLM's JSON response and call the requested function.

    If the LLM didn't request a function call, returns the raw text.
    """
    if not llm_response:
        return {"error": "No LLM response"}

    # Handle parsed dict (json_output=True)
    if isinstance(llm_response, dict):
        data = llm_response
    elif isinstance(llm_response, str):
        # Try to extract JSON from the response
        try:
            data = json.loads(llm_response)
        except json.JSONDecodeError:
            return {"response": llm_response}
    else:
        return {"response": str(llm_response)}

    fn_name = data.get("function", "")
    fn_params = data.get("function_parameters", {})

    if fn_name not in TOOL_REGISTRY:
        # LLM responded with text instead of a function call
        return {"response": data.get("result", data.get("response", str(data)))}

    try:
        result = TOOL_REGISTRY[fn_name](**fn_params)
        return {"function": fn_name, "parameters": fn_params, "result": result}
    except Exception as e:
        return {"function": fn_name, "error": str(e)}


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

def create_function_calling_workflow(executor) -> ConductorWorkflow:
    wf = ConductorWorkflow(name="function_calling_demo", version=1, executor=executor)

    # Wait for user query
    user_input = WaitTask(task_ref_name="get_user_input")

    # LLM decides which function to call (json_output=True to parse result)
    chat_complete = LlmChatComplete(
        task_ref_name="chat_complete_ref",
        llm_provider=LLM_PROVIDER,
        model=LLM_MODEL,
        messages=[
            ChatMessage(role="system", message=SYSTEM_PROMPT),
            ChatMessage(role="user", message="${get_user_input.output.question}"),
        ],
        max_tokens=500,
        temperature=0,
        json_output=True,
    )

    # Dispatch the LLM's function call via a worker
    fn_dispatch = dispatch_function(
        task_ref_name="fn_call_ref",
        llm_response="${chat_complete_ref.output.result}",
    )

    # Loop: user input -> LLM -> dispatch function
    loop = LoopTask(task_ref_name="loop", iterations=5, tasks=[user_input, chat_complete, fn_dispatch])

    wf >> loop
    wf.timeout_seconds(300).timeout_policy(timeout_policy=TimeoutPolicy.TIME_OUT_WORKFLOW)

    return wf


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    api_config = Configuration()
    clients = OrkesClients(configuration=api_config)
    workflow_executor = clients.get_workflow_executor()
    workflow_client = clients.get_workflow_client()
    task_client = clients.get_task_client()

    # Start workers
    task_handler = TaskHandler(
        workers=[], configuration=api_config, scan_for_annotated_workers=True,
    )
    task_handler.start_processes()

    try:
        wf = create_function_calling_workflow(workflow_executor)
        wf.register(overwrite=True)

        print("Function Calling Agent")
        print("=" * 50)
        print("Try:")
        print("  - What's the weather in Tokyo?")
        print("  - How much does a laptop cost?")
        print("  - Calculate sqrt(144) + pi")
        print("  - Show me the top 3 customers")
        print("  - Type 'quit' to exit")
        print("=" * 50)

        workflow_run = wf.execute(
            wait_until_task_ref="get_user_input",
            wait_for_seconds=1,
        )
        workflow_id = workflow_run.workflow_id
        print(f"\nWorkflow: {api_config.ui_host}/execution/{workflow_id}\n")

        while workflow_run.is_running():
            current = workflow_run.current_task
            if current and current.workflow_task.task_reference_name == "get_user_input":
                # Show previous function call result
                fn_task = workflow_run.get_task(task_reference_name="fn_call_ref")
                if fn_task and fn_task.output_data:
                    out = fn_task.output_data.get("result", fn_task.output_data)
                    if isinstance(out, dict):
                        fn_result = out.get("result", out.get("response", out))
                        fn_name = out.get("function", "")
                        if fn_name:
                            print(f"[{fn_name}] {fn_result}")
                        else:
                            print(f"Assistant: {fn_result}")
                    else:
                        print(f"Result: {out}")
                    print()

                question = input("You: ")
                if question.lower() in ("quit", "exit", "q"):
                    print("\nDone.")
                    break

                task_client.update_task_sync(
                    workflow_id=workflow_id,
                    task_ref_name="get_user_input",
                    status=TaskResultStatus.COMPLETED,
                    output={"question": question},
                )

            time.sleep(0.5)
            workflow_run = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)

        print(f"Full execution: {api_config.ui_host}/execution/{workflow_id}")

    finally:
        task_handler.stop_processes()


if __name__ == "__main__":
    main()
