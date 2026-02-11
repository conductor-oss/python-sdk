"""
LLM Multi-Turn Chat Example

Demonstrates an automated multi-turn conversation using Conductor's LLM_CHAT_COMPLETE
system task. A "questioner" LLM generates questions about science, and a "responder"
LLM answers them. The conversation history is maintained across turns using a worker
that collects chat messages.

Pipeline:
    generate_question --> loop(collect_history --> chat_complete --> generate_followup)
                      --> collect_conversation

Requirements:
    - Conductor server with AI/LLM support
    - LLM provider named 'openai' with a valid API key configured
    - export CONDUCTOR_SERVER_URL=http://localhost:7001/api

Usage:
    python examples/agentic_workflows/llm_chat.py
"""

import time
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients
from conductor.client.worker.worker_task import worker_task
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.do_while_task import LoopTask
from conductor.client.workflow.task.llm_tasks.llm_chat_complete import LlmChatComplete, ChatMessage
from conductor.client.workflow.task.timeout_policy import TimeoutPolicy

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LLM_PROVIDER = "openai"
LLM_MODEL = "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------

@worker_task(task_definition_name='chat_collect_history')
def collect_history(
    user_input: str = None,
    seed_question: str = None,
    assistant_response: str = None,
    history: object = None,
) -> list:
    """Append the latest user and assistant messages to the conversation history.

    Returns a list of ChatMessage-compatible dicts with 'role' and 'message' keys.
    Handles the first iteration where history references resolve to unsubstituted
    expressions (strings starting with '$').
    """
    all_history = []

    # On the first loop iteration, unresolved references come as literal strings
    if history and isinstance(history, list):
        for item in history:
            if isinstance(item, dict) and "role" in item and "message" in item:
                all_history.append(item)

    if assistant_response and not assistant_response.startswith("$"):
        all_history.append({"role": "assistant", "message": assistant_response})

    if user_input and not user_input.startswith("$"):
        all_history.append({"role": "user", "message": user_input})
    elif seed_question and not seed_question.startswith("$"):
        all_history.append({"role": "user", "message": seed_question})

    return all_history


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

def create_chat_workflow(executor) -> ConductorWorkflow:
    wf = ConductorWorkflow(name="llm_chat_demo", version=1, executor=executor)

    # 1. Generate a seed question about science
    question_gen = LlmChatComplete(
        task_ref_name="gen_question_ref",
        llm_provider=LLM_PROVIDER,
        model=LLM_MODEL,
        messages=[
            ChatMessage(
                role="system",
                message="You are an expert in science. Think of a random scientific "
                        "discovery and create a short, interesting question about it.",
            ),
        ],
        temperature=0.7,
    )

    # 2. Collect conversation history (worker)
    collect_history_task = collect_history(
        task_ref_name="collect_history_ref",
        user_input="${followup_question_ref.output.result}",
        seed_question="${gen_question_ref.output.result}",
        history="${chat_complete_ref.input.messages}",
        assistant_response="${chat_complete_ref.output.result}",
    )

    # 3. Main chat completion -- answers the question
    chat_complete = LlmChatComplete(
        task_ref_name="chat_complete_ref",
        llm_provider=LLM_PROVIDER,
        model=LLM_MODEL,
    )
    # Set messages as a dynamic reference (must bypass constructor to avoid string iteration)
    chat_complete.input_parameters["messages"] = "${collect_history_ref.output.result}"

    # 4. Generate a follow-up question based on the answer
    followup_gen = LlmChatComplete(
        task_ref_name="followup_question_ref",
        llm_provider=LLM_PROVIDER,
        model=LLM_MODEL,
        messages=[
            ChatMessage(
                role="system",
                message=(
                    "You are an expert in science. Given the context below, "
                    "generate a follow-up question to dive deeper into the topic. "
                    "Do not repeat previous questions.\n\n"
                    "Context:\n${chat_complete_ref.output.result}\n\n"
                    "Previous questions:\n"
                    "${collect_history_ref.input.history}"
                ),
            ),
        ],
        temperature=0.7,
    )

    # Loop: collect history -> answer -> follow-up question
    loop_tasks = [collect_history_task, chat_complete, followup_gen]
    chat_loop = LoopTask(task_ref_name="loop", iterations=3, tasks=loop_tasks)

    wf >> question_gen >> chat_loop
    wf.timeout_seconds(120).timeout_policy(timeout_policy=TimeoutPolicy.TIME_OUT_WORKFLOW)

    return wf


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    api_config = Configuration()
    clients = OrkesClients(configuration=api_config)
    workflow_executor = clients.get_workflow_executor()
    workflow_client = clients.get_workflow_client()

    # Start workers
    task_handler = TaskHandler(
        workers=[], configuration=api_config, scan_for_annotated_workers=True,
    )
    task_handler.start_processes()

    try:
        wf = create_chat_workflow(workflow_executor)
        wf.register(overwrite=True)

        print("Starting automated multi-turn science chat...\n")
        result = wf.execute(
            wait_until_task_ref="collect_history_ref",
            wait_for_seconds=10,
        )

        # Print the seed question
        seed_task = result.get_task(task_reference_name="gen_question_ref")
        if seed_task:
            print(f"Seed question: {seed_task.output_data.get('result', '').strip()}")
            print("=" * 70)

        workflow_id = result.workflow_id
        print(f"Workflow: {api_config.ui_host}/execution/{workflow_id}\n")

        # Poll until complete, printing new conversation turns as they appear
        printed_tasks = set()
        while not result.is_completed():
            result = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)
            for task in (result.tasks or []):
                ref = task.reference_task_name
                if task.status == "COMPLETED" and ref not in printed_tasks:
                    text = (task.output_data or {}).get("result", "")
                    if not text:
                        continue
                    text = str(text).strip()
                    if ref.startswith("chat_complete_ref"):
                        print(f"  [Answer] {text[:300]}")
                        printed_tasks.add(ref)
                    elif ref.startswith("followup_question_ref"):
                        print(f"  [Follow-up] {text[:300]}")
                        print()
                        printed_tasks.add(ref)
            time.sleep(2)

        print("=" * 70)
        print("Conversation complete.")
        print(f"Full execution: {api_config.ui_host}/execution/{workflow_id}")
        print("=" * 70)

    finally:
        task_handler.stop_processes()


if __name__ == "__main__":
    main()
