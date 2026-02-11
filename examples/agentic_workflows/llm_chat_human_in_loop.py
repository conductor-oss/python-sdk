"""
LLM Chat with Human-in-the-Loop

Demonstrates an interactive chat where the workflow pauses for user input
between LLM responses using Conductor's WAIT task. The user types questions
in the terminal, and the LLM responds, maintaining conversation history.

Pipeline:
    loop(wait_for_user --> collect_history --> chat_complete) --> summary

Requirements:
    - Conductor server with AI/LLM support
    - LLM provider named 'openai' with a valid API key configured
    - export CONDUCTOR_SERVER_URL=http://localhost:7001/api

Usage:
    python examples/agentic_workflows/llm_chat_human_in_loop.py
"""

import json
import time

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
SYSTEM_PROMPT = (
    "You are a helpful assistant that knows about science. "
    "Answer questions clearly and concisely. If you don't know "
    "something, say so. Stay on topic."
)


# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------

@worker_task(task_definition_name='human_chat_collect_history')
def collect_history(
    user_input: str = None,
    assistant_response: str = None,
    history: object = None,
) -> list:
    """Append the latest user and assistant messages to the conversation history.

    Handles the first loop iteration where unresolved references arrive as
    literal strings starting with '$'.
    """
    all_history = []

    if history and isinstance(history, list):
        for item in history:
            if isinstance(item, dict) and "role" in item and "message" in item:
                all_history.append(item)

    if assistant_response and not str(assistant_response).startswith("$"):
        all_history.append({"role": "assistant", "message": assistant_response})

    if user_input and not str(user_input).startswith("$"):
        all_history.append({"role": "user", "message": user_input})

    return all_history


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

def create_human_chat_workflow(executor) -> ConductorWorkflow:
    wf = ConductorWorkflow(name="llm_chat_human_in_loop", version=1, executor=executor)

    # Wait for the user to type a question
    user_input = WaitTask(task_ref_name="user_input_ref")

    # Collect conversation history
    collect_history_task = collect_history(
        task_ref_name="collect_history_ref",
        user_input="${user_input_ref.output.question}",
        history="${chat_complete_ref.input.messages}",
        assistant_response="${chat_complete_ref.output.result}",
    )

    # Chat completion with system prompt passed inline
    chat_complete = LlmChatComplete(
        task_ref_name="chat_complete_ref",
        llm_provider=LLM_PROVIDER,
        model=LLM_MODEL,
    )
    # Set messages as a dynamic reference (bypass constructor to avoid string iteration)
    chat_complete.input_parameters["messages"] = "${collect_history_ref.output.result}"

    # Loop: wait for user -> collect history -> respond
    loop_tasks = [user_input, collect_history_task, chat_complete]
    chat_loop = LoopTask(task_ref_name="loop", iterations=5, tasks=loop_tasks)

    wf >> chat_loop
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
        wf = create_human_chat_workflow(workflow_executor)
        wf.register(overwrite=True)

        print("Interactive science chat (type 'quit' to exit)")
        print("=" * 50)

        workflow_run = wf.execute(
            wait_until_task_ref="user_input_ref",
            wait_for_seconds=1,
        )
        workflow_id = workflow_run.workflow_id
        print(f"Workflow: {api_config.ui_host}/execution/{workflow_id}\n")

        while workflow_run.is_running():
            current = workflow_run.current_task
            if current and current.workflow_task.task_reference_name == "user_input_ref":
                # Show the previous assistant response if available
                assistant_task = workflow_run.get_task(task_reference_name="chat_complete_ref")
                if assistant_task and assistant_task.output_data.get("result"):
                    print(f"Assistant: {assistant_task.output_data['result'].strip()}\n")

                # Get user input
                question = input("You: ")
                if question.lower() in ("quit", "exit", "q"):
                    print("\nEnding conversation.")
                    break

                # Complete the WAIT task with user's question
                task_client.update_task_sync(
                    workflow_id=workflow_id,
                    task_ref_name="user_input_ref",
                    status=TaskResultStatus.COMPLETED,
                    output={"question": question},
                )

            time.sleep(0.5)
            workflow_run = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)

        # Show final assistant response
        if workflow_run.is_completed():
            assistant_task = workflow_run.get_task(task_reference_name="chat_complete_ref")
            if assistant_task and assistant_task.output_data.get("result"):
                print(f"Assistant: {assistant_task.output_data['result'].strip()}")

        print(f"\nFull conversation: {api_config.ui_host}/execution/{workflow_id}")

    finally:
        task_handler.stop_processes()


if __name__ == "__main__":
    main()
