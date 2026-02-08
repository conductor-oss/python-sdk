"""
Multi-Agent Chat Example

Demonstrates a multi-agent conversation where a moderator LLM routes questions
between two "panelist" agents. Each agent has a different persona and perspective.
The moderator summarizes progress and picks who speaks next.

Pipeline:
    loop(moderator --> switch(agent_1 | agent_2) --> update_history)

Requirements:
    - Conductor server with AI/LLM support
    - LLM provider named 'openai' with a valid API key configured
    - export CONDUCTOR_SERVER_URL=http://localhost:7001/api

Usage:
    python examples/agentic_workflows/multiagent_chat.py
    python examples/agentic_workflows/multiagent_chat.py --topic "climate change"
    python examples/agentic_workflows/multiagent_chat.py --agent1 "scientist" --agent2 "economist"
"""

import argparse
import time

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients
from conductor.client.worker.worker_task import worker_task
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.do_while_task import LoopTask
from conductor.client.workflow.task.llm_tasks.llm_chat_complete import LlmChatComplete, ChatMessage
from conductor.client.workflow.task.set_variable_task import SetVariableTask
from conductor.client.workflow.task.switch_task import SwitchTask
from conductor.client.workflow.task.timeout_policy import TimeoutPolicy

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LLM_PROVIDER = "openai"
LLM_MODEL = "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------

@worker_task(task_definition_name='build_moderator_messages')
def build_moderator_messages(
    system_prompt: str = "",
    history: object = None,
) -> list:
    """Prepend a system message to the conversation history for the moderator."""
    messages = [{"role": "system", "message": system_prompt}]
    if history and isinstance(history, list):
        for item in history:
            if isinstance(item, dict) and "role" in item and "message" in item:
                messages.append({"role": item["role"], "message": item["message"]})
    return messages


@worker_task(task_definition_name='update_multiagent_history')
def update_multiagent_history(
    history: object = None,
    moderator_message: str = None,
    agent_name: str = None,
    agent_response: str = None,
) -> list:
    """Append the moderator's summary and agent response to the history."""
    all_history = []
    if history and isinstance(history, list):
        for item in history:
            if isinstance(item, dict) and "role" in item and "message" in item:
                all_history.append({"role": item["role"], "message": item["message"]})

    if moderator_message and not str(moderator_message).startswith("$"):
        all_history.append({"role": "assistant", "message": moderator_message})

    if agent_response and not str(agent_response).startswith("$"):
        prefix = f"[{agent_name}] " if agent_name else ""
        all_history.append({"role": "user", "message": f"{prefix}{agent_response}"})

    return all_history


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

def create_multiagent_workflow(executor) -> ConductorWorkflow:
    wf = ConductorWorkflow(name="multiagent_chat_demo", version=1, executor=executor)

    # -- Initialize conversation state --
    init = SetVariableTask(task_ref_name="init_ref")
    init.input_parameter("history", [
        {"role": "user", "message": "Discuss the following topic: ${workflow.input.topic}"}
    ])
    init.input_parameter("last_speaker", "")

    # -- Build moderator messages (worker prepends system prompt to history) --
    build_messages_task = build_moderator_messages(
        task_ref_name="build_mod_msgs_ref",
        system_prompt=(
            "You are a discussion moderator. Two panelists are debating: "
            "${workflow.input.agent1_name} and ${workflow.input.agent2_name}.\n"
            "Summarize the latest exchange, then ask a follow-up question to "
            "one of them. Alternate fairly. The last speaker was: ${workflow.variables.last_speaker}.\n\n"
            "Respond ONLY with valid JSON:\n"
            '{"result": "your moderator message", "user": "name_of_next_speaker"}'
        ),
        history="${workflow.variables.history}",
    )

    # -- Moderator: summarizes and picks next speaker --
    moderator_task = LlmChatComplete(
        task_ref_name="moderator_ref",
        llm_provider=LLM_PROVIDER,
        model=LLM_MODEL,
        max_tokens=500,
        temperature=0.7,
        json_output=True,
    )
    moderator_task.input_parameters["messages"] = "${build_mod_msgs_ref.output.result}"

    # -- Agent 1 response --
    agent1_task = LlmChatComplete(
        task_ref_name="agent1_ref",
        llm_provider=LLM_PROVIDER,
        model=LLM_MODEL,
        messages=[
            ChatMessage(
                role="system",
                message=(
                    "You are ${workflow.input.agent1_name}. You reason and speak like this persona. "
                    "You are in a panel discussion. Provide insightful analysis and ask follow-up questions. "
                    "Do not mention that you are an AI. Keep responses concise (2-3 paragraphs max).\n\n"
                    "Topic context:\n${workflow.input.topic}"
                ),
            ),
            ChatMessage(role="user", message="${moderator_ref.output.result.result}"),
        ],
        max_tokens=400,
        temperature=0.8,
    )

    update_history1 = update_multiagent_history(
        task_ref_name="update_hist1_ref",
        history="${workflow.variables.history}",
        moderator_message="${moderator_ref.output.result.result}",
        agent_name="${workflow.input.agent1_name}",
        agent_response="${agent1_ref.output.result}",
    )

    save_var1 = SetVariableTask(task_ref_name="save_var1_ref")
    save_var1.input_parameter("history", "${update_hist1_ref.output.result}")
    save_var1.input_parameter("last_speaker", "${workflow.input.agent1_name}")

    # -- Agent 2 response --
    agent2_task = LlmChatComplete(
        task_ref_name="agent2_ref",
        llm_provider=LLM_PROVIDER,
        model=LLM_MODEL,
        messages=[
            ChatMessage(
                role="system",
                message=(
                    "You are ${workflow.input.agent2_name}. You reason and speak like this persona. "
                    "You bring contrarian views and challenge assumptions. "
                    "You are in a panel discussion. Be provocative but civil. "
                    "Do not mention that you are an AI. Keep responses concise (2-3 paragraphs max).\n\n"
                    "Topic context:\n${workflow.input.topic}"
                ),
            ),
            ChatMessage(role="user", message="${moderator_ref.output.result.result}"),
        ],
        max_tokens=400,
        temperature=0.8,
    )

    update_history2 = update_multiagent_history(
        task_ref_name="update_hist2_ref",
        history="${workflow.variables.history}",
        moderator_message="${moderator_ref.output.result.result}",
        agent_name="${workflow.input.agent2_name}",
        agent_response="${agent2_ref.output.result}",
    )

    save_var2 = SetVariableTask(task_ref_name="save_var2_ref")
    save_var2.input_parameter("history", "${update_hist2_ref.output.result}")
    save_var2.input_parameter("last_speaker", "${workflow.input.agent2_name}")

    # -- Route to the correct agent based on moderator's pick --
    # Use flexible matching: check if any significant word from the agent name
    # appears in the moderator's selected user string
    route_script = """
    (function(){
        var user = ($.user || '').toLowerCase();
        var a1 = ($.a1 || '').toLowerCase();
        var a2 = ($.a2 || '').toLowerCase();
        function matches(user, name) {
            var words = name.split(' ');
            for (var i = 0; i < words.length; i++) {
                if (words[i].length > 3 && user.indexOf(words[i]) >= 0) return true;
            }
            return false;
        }
        if (matches(user, a1) && !matches(user, a2)) return 'agent1';
        if (matches(user, a2) && !matches(user, a1)) return 'agent2';
        if (matches(user, a2)) return 'agent2';
        if (matches(user, a1)) return 'agent1';
        return 'agent1';
    })();
    """
    router = SwitchTask(task_ref_name="route_ref", case_expression=route_script, use_javascript=True)
    router.switch_case("agent1", [agent1_task, update_history1, save_var1])
    router.switch_case("agent2", [agent2_task, update_history2, save_var2])
    router.input_parameter("user", "${moderator_ref.output.result.user}")
    router.input_parameter("a1", "${workflow.input.agent1_name}")
    router.input_parameter("a2", "${workflow.input.agent2_name}")

    # -- Conversation loop --
    loop = LoopTask(task_ref_name="loop", iterations=4, tasks=[build_messages_task, moderator_task, router])

    wf >> init >> loop
    wf.timeout_seconds(600).timeout_policy(timeout_policy=TimeoutPolicy.TIME_OUT_WORKFLOW)

    return wf


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Multi-agent chat example")
    parser.add_argument("--topic", default="The impact of artificial intelligence on employment",
                        help="Discussion topic")
    parser.add_argument("--agent1", default="an optimistic technologist", help="Agent 1 persona")
    parser.add_argument("--agent2", default="a cautious labor economist", help="Agent 2 persona")
    parser.add_argument("--rounds", type=int, default=4, help="Number of discussion rounds")
    args = parser.parse_args()

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
        wf = create_multiagent_workflow(workflow_executor)
        wf.register(overwrite=True)

        wf_input = {
            "topic": args.topic,
            "agent1_name": args.agent1,
            "agent2_name": args.agent2,
        }

        print(f"Topic: {args.topic}")
        print(f"Agent 1: {args.agent1}")
        print(f"Agent 2: {args.agent2}")
        print(f"Rounds: {args.rounds}")
        print("=" * 70)

        result = wf.execute(
            wait_until_task_ref="build_mod_msgs_ref",
            wait_for_seconds=1,
            workflow_input=wf_input,
        )

        workflow_id = result.workflow_id
        print(f"Workflow: {api_config.ui_host}/execution/{workflow_id}\n")

        # Poll until complete, printing new conversation turns
        printed_tasks = set()
        result = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)

        while result.is_running():
            for task in (result.tasks or []):
                ref = task.reference_task_name
                if task.status == "COMPLETED" and ref not in printed_tasks:
                    text = (task.output_data or {}).get("result", "")
                    if not text:
                        continue
                    if ref.startswith("moderator_ref"):
                        msg = text.get("result", str(text)) if isinstance(text, dict) else str(text)
                        print(f"  [Moderator] {str(msg).strip()[:300]}")
                        printed_tasks.add(ref)
                    elif ref.startswith("agent1_ref"):
                        print(f"  [{args.agent1}] {str(text).strip()[:300]}")
                        printed_tasks.add(ref)
                    elif ref.startswith("agent2_ref"):
                        print(f"  [{args.agent2}] {str(text).strip()[:300]}")
                        printed_tasks.add(ref)
                        print()
            time.sleep(3)
            result = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)

        print("=" * 70)
        print("Discussion complete.")
        print(f"Full execution: {api_config.ui_host}/execution/{workflow_id}")
    finally:
        task_handler.stop_processes()


if __name__ == "__main__":
    main()
