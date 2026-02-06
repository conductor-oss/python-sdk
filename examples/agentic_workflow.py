"""
Agentic Workflow Example - Using Python Workers as Agent Tools

This example demonstrates how to create an agentic workflow where an LLM can
dynamically call Python worker tasks as tools to accomplish goals.

The workflow:
1. Takes a user query
2. LLM analyzes the query and decides which tool(s) to call
3. Python workers execute as tools
4. LLM summarizes the results

Requirements:
- Conductor server running (see README.md for startup instructions)
- OpenAI API key configured in Conductor integrations
- Set environment variables:
    export CONDUCTOR_SERVER_URL=http://localhost:8080/api
    export CONDUCTOR_AUTH_KEY=your_key  # if using Orkes Conductor
    export CONDUCTOR_AUTH_SECRET=your_secret  # if using Orkes Conductor

Usage:
    python examples/agentic_workflow.py
"""

import os
import time
from typing import Optional

from conductor.client.ai.orchestrator import AIOrchestrator
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import TaskDef
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.orkes_clients import OrkesClients
from conductor.client.worker.worker_task import worker_task
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.do_while_task import LoopTask
from conductor.client.workflow.task.dynamic_task import DynamicTask
from conductor.client.workflow.task.llm_tasks.llm_chat_complete import LlmChatComplete, ChatMessage
from conductor.client.workflow.task.set_variable_task import SetVariableTask
from conductor.client.workflow.task.switch_task import SwitchTask
from conductor.client.workflow.task.timeout_policy import TimeoutPolicy
from conductor.client.workflow.task.wait_task import WaitTask


# =============================================================================
# DEFINE PYTHON WORKERS AS AGENT TOOLS
# =============================================================================
# These workers will be available as tools for the LLM agent to call.
# Each worker is a self-contained function that performs a specific task.

@worker_task(task_definition_name='get_weather')
def get_weather(city: str, units: str = 'fahrenheit') -> dict:
    """
    Get current weather for a city.
    
    Args:
        city: City name or zip code
        units: Temperature units ('fahrenheit' or 'celsius')
    
    Returns:
        Weather information including temperature and conditions
    """
    # In a real application, this would call a weather API
    weather_data = {
        'new york': {'temp': 72, 'condition': 'Partly Cloudy', 'humidity': 65},
        'san francisco': {'temp': 58, 'condition': 'Foggy', 'humidity': 80},
        'miami': {'temp': 85, 'condition': 'Sunny', 'humidity': 75},
        'chicago': {'temp': 45, 'condition': 'Windy', 'humidity': 55},
    }
    
    city_lower = city.lower()
    data = weather_data.get(city_lower, {'temp': 70, 'condition': 'Clear', 'humidity': 50})
    
    if units == 'celsius':
        data['temp'] = round((data['temp'] - 32) * 5/9, 1)
    
    return {
        'city': city,
        'temperature': data['temp'],
        'units': units,
        'condition': data['condition'],
        'humidity': data['humidity']
    }


@worker_task(task_definition_name='search_products')
def search_products(query: str, max_results: int = 5) -> dict:
    """
    Search for products in a catalog.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
    
    Returns:
        List of matching products with prices
    """
    # Simulated product database
    products = [
        {'name': 'Wireless Headphones', 'price': 79.99, 'category': 'Electronics'},
        {'name': 'Running Shoes', 'price': 129.99, 'category': 'Sports'},
        {'name': 'Coffee Maker', 'price': 49.99, 'category': 'Kitchen'},
        {'name': 'Laptop Stand', 'price': 39.99, 'category': 'Electronics'},
        {'name': 'Yoga Mat', 'price': 24.99, 'category': 'Sports'},
        {'name': 'Bluetooth Speaker', 'price': 59.99, 'category': 'Electronics'},
        {'name': 'Water Bottle', 'price': 19.99, 'category': 'Sports'},
    ]
    
    query_lower = query.lower()
    matches = [p for p in products if query_lower in p['name'].lower() or query_lower in p['category'].lower()]
    
    return {
        'query': query,
        'total_found': len(matches),
        'products': matches[:max_results]
    }


@worker_task(task_definition_name='calculate')
def calculate(expression: str) -> dict:
    """
    Perform a mathematical calculation.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2", "sqrt(16)")
    
    Returns:
        Calculation result
    """
    import math
    
    # Safe evaluation with limited functions
    safe_dict = {
        'abs': abs, 'round': round, 'min': min, 'max': max,
        'sqrt': math.sqrt, 'pow': pow, 'log': math.log,
        'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
        'pi': math.pi, 'e': math.e
    }
    
    try:
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        return {'expression': expression, 'result': result, 'success': True}
    except Exception as e:
        return {'expression': expression, 'error': str(e), 'success': False}


@worker_task(task_definition_name='send_notification')
def send_notification(recipient: str, message: str, channel: str = 'email') -> dict:
    """
    Send a notification to a user.
    
    Args:
        recipient: Email address or phone number
        message: Notification message content
        channel: Notification channel ('email', 'sms', 'push')
    
    Returns:
        Confirmation of notification sent
    """
    # In a real application, this would integrate with notification services
    return {
        'status': 'sent',
        'recipient': recipient,
        'channel': channel,
        'message_preview': message[:50] + '...' if len(message) > 50 else message,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }


# =============================================================================
# AGENT WORKFLOW SETUP
# =============================================================================

def start_workers(api_config: Configuration) -> TaskHandler:
    """Start the task handler with worker discovery."""
    task_handler = TaskHandler(
        workers=[],
        configuration=api_config,
        scan_for_annotated_workers=True,
    )
    task_handler.start_processes()
    return task_handler


def register_tool_tasks(metadata_client) -> None:
    """Register task definitions for our worker tools."""
    tools = ['get_weather', 'search_products', 'calculate', 'send_notification']
    for tool in tools:
        metadata_client.register_task_def(task_def=TaskDef(name=tool))


def create_agent_prompt() -> str:
    """Create the system prompt that defines available tools for the agent."""
    return """
You are a helpful AI assistant with access to the following tools:

1. get_weather(city: str, units: str = 'fahrenheit') -> dict
   - Get current weather for a city
   - units can be 'fahrenheit' or 'celsius'

2. search_products(query: str, max_results: int = 5) -> dict
   - Search for products in our catalog
   - Returns product names and prices

3. calculate(expression: str) -> dict
   - Perform mathematical calculations
   - Supports basic math, sqrt, pow, log, trig functions

4. send_notification(recipient: str, message: str, channel: str = 'email') -> dict
   - Send notifications via email, sms, or push

When you need to use a tool, respond with a JSON object in this exact format:
{
    "type": "function",
    "function": "FUNCTION_NAME",
    "function_parameters": {"param1": "value1", "param2": "value2"}
}

If you don't need to use a tool, just respond normally with text.
Always be helpful and explain your actions to the user.
"""


def create_agentic_workflow(
    workflow_executor,
    llm_provider: str,
    model: str,
    prompt_name: str
) -> ConductorWorkflow:
    """
    Create an agentic workflow that uses Python workers as tools.
    
    The workflow:
    1. Waits for user input
    2. Sends to LLM with tool definitions
    3. If LLM wants to call a tool, dynamically execute the worker
    4. Loop back for more interactions
    """
    wf = ConductorWorkflow(name='python_agent_workflow', version=1, executor=workflow_executor)
    
    # Wait for user input
    user_input = WaitTask(task_ref_name='get_user_input')
    
    # Collect conversation history
    collect_history = SetVariableTask(task_ref_name='collect_history_ref')
    collect_history.input_parameter('messages', [
        ChatMessage(role='user', message='${get_user_input.output.question}')
    ])
    collect_history.input_parameter('_merge', True)
    
    # LLM chat completion with tool awareness
    chat_complete = LlmChatComplete(
        task_ref_name='chat_complete_ref',
        llm_provider=llm_provider,
        model=model,
        instructions_template=prompt_name,
        messages='${workflow.variables.messages}',
        max_tokens=1000,
        temperature=0
    )
    
    # Dynamic task to call the function returned by LLM
    function_call = DynamicTask(
        task_reference_name='fn_call_ref',
        dynamic_task=chat_complete.output('function')
    )
    function_call.input_parameters['inputs'] = chat_complete.output('function_parameters')
    function_call.input_parameters['dynamicTaskInputParam'] = 'inputs'
    
    # Switch to check if LLM wants to call a function
    should_call_fn = SwitchTask(
        task_ref_name='check_function_call',
        case_expression="$.type == 'function' ? 'call_function' : 'direct_response'",
        use_javascript=True
    )
    should_call_fn.input_parameter('type', chat_complete.output('type'))
    should_call_fn.switch_case('call_function', [function_call])
    should_call_fn.default_case([])  # No function call needed
    
    # Update history with assistant response
    update_history = SetVariableTask(task_ref_name='update_history_ref')
    update_history.input_parameter('messages', [
        ChatMessage(role='assistant', message='${chat_complete_ref.output.result}')
    ])
    update_history.input_parameter('_merge', True)
    
    # Create the conversation loop
    loop_tasks = [user_input, collect_history, chat_complete, should_call_fn, update_history]
    chat_loop = LoopTask(task_ref_name='agent_loop', iterations=10, tasks=loop_tasks)
    
    wf >> chat_loop
    
    # Set workflow timeout (5 minutes)
    wf.timeout_seconds(300).timeout_policy(timeout_policy=TimeoutPolicy.TIME_OUT_WORKFLOW)
    
    return wf


def main():
    """Main entry point for the agentic workflow example."""
    
    # Configuration
    llm_provider = 'openai'  # Change to your configured provider
    model = 'gpt-4'  # Or 'gpt-3.5-turbo' for faster/cheaper responses
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║          🤖 Conductor Agentic Workflow Example                   ║
╠══════════════════════════════════════════════════════════════════╣
║  This agent can:                                                 ║
║  • Get weather for any city                                      ║
║  • Search products in a catalog                                  ║
║  • Perform calculations                                          ║
║  • Send notifications                                            ║
║                                                                  ║
║  Try asking:                                                     ║
║  - "What's the weather in San Francisco?"                        ║
║  - "Search for electronics under $100"                           ║
║  - "Calculate the square root of 144"                            ║
║  - "Send an email to user@example.com saying hello"              ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # Initialize configuration and clients
    api_config = Configuration()
    clients = OrkesClients(configuration=api_config)
    workflow_executor = clients.get_workflow_executor()
    workflow_client = clients.get_workflow_client()
    task_client = clients.get_task_client()
    metadata_client = clients.get_metadata_client()
    
    # Start workers
    task_handler = start_workers(api_config)
    
    # Register tool tasks
    register_tool_tasks(metadata_client)
    
    # Set up AI orchestrator and prompt
    orchestrator = AIOrchestrator(api_configuration=api_config)
    prompt_name = 'python_agent_instructions'
    prompt_text = create_agent_prompt()
    
    orchestrator.add_prompt_template(prompt_name, prompt_text, 'Agent with Python tool access')
    orchestrator.associate_prompt_template(prompt_name, llm_provider, [model])
    
    # Create and register workflow
    wf = create_agentic_workflow(workflow_executor, llm_provider, model, prompt_name)
    wf.register(overwrite=True)
    
    print(f"✅ Workflow registered: {wf.name}")
    print(f"🌐 Conductor UI: {api_config.ui_host}\n")
    
    # Start workflow execution
    workflow_run = wf.execute(
        wait_until_task_ref='get_user_input',
        wait_for_seconds=1,
        workflow_input={}
    )
    workflow_id = workflow_run.workflow_id
    
    print(f"🚀 Workflow started: {api_config.ui_host}/execution/{workflow_id}\n")
    
    # Interactive conversation loop
    try:
        while workflow_run.is_running():
            current_task = workflow_run.current_task
            if current_task and current_task.workflow_task.task_reference_name == 'get_user_input':
                
                # Check for previous function call results
                fn_call_task = workflow_run.get_task(task_reference_name='fn_call_ref')
                if fn_call_task and fn_call_task.output_data:
                    print(f"\n🔧 Tool Result: {fn_call_task.output_data.get('result', fn_call_task.output_data)}")
                
                # Check for LLM response
                chat_task = workflow_run.get_task(task_reference_name='chat_complete_ref')
                if chat_task and chat_task.output_data.get('result'):
                    print(f"\n🤖 Assistant: {chat_task.output_data['result']}")
                
                # Get user input
                question = input('\n👤 You: ')
                if question.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                # Submit user input to workflow
                task_client.update_task_sync(
                    workflow_id=workflow_id,
                    task_ref_name='get_user_input',
                    status=TaskResultStatus.COMPLETED,
                    output={'question': question}
                )
            
            time.sleep(0.5)
            workflow_run = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    finally:
        # Cleanup
        print("\n🛑 Stopping workers...")
        task_handler.stop_processes()
        print("✅ Done!")


if __name__ == '__main__':
    main()
