"""Wait for Message (Streaming) — send messages to a running agent and stream its responses.

Demonstrates:
    - wait_for_message_tool with streaming: push messages in and see the agent react
    - Using handle.stream() to observe WAITING → processing → WAITING cycles
    - runtime.send_message() to push payloads into the Workflow Message Queue
    - handle.stop() ending the loop deterministically

The agent starts, immediately waits for a message, answers it with respond(),
then loops back to wait_for_message.  The caller drives the conversation from a
background thread — sending a task every 8 seconds — while the main thread reads
streamed events.

The agent's instructions tell it to never stop, so the loop only ends when the
sender calls handle.stop() — after giving the last task time to be answered.
That sets the ``_stop_requested`` workflow variable
checked by the DoWhile condition and pushes a ``{"_signal": "stop"}`` message to
unblock the pending PULL_WORKFLOW_MESSAGES.  stream() then yields DONE.

Requirements:
    - Conductor server running at http://localhost:8080
    - CONDUCTOR_SERVER_URL=http://localhost:8080/api as environment variable
    - CONDUCTOR_AGENT_LLM_MODEL=openai/gpt-4o-mini as environment variable
"""

import os
import threading
import time

os.environ.setdefault("CONDUCTOR_LOG_LEVEL", "WARNING")

from conductor.ai.agents import Agent, AgentRuntime, EventType, wait_for_message_tool, tool
from settings import settings


@tool
def respond(answer: str) -> str:
    """Send your answer back to the caller."""
    return "ok"


receive_message = wait_for_message_tool(
    name="wait_for_message",
    description=(
        "Wait for the next instruction from the caller. "
        "The message payload contains a 'task' field with the request."
    ),
)

agent = Agent(
    name="reactive_agent",
    model=settings.llm_model,
    tools=[receive_message, respond],
    max_turns=10000,
    stateful=True,
    instructions=(
        "You are a reactive agent. Repeat this cycle indefinitely without stopping: "
        "1. Call wait_for_message to receive your next instruction. "
        "2. Think through the task in the 'task' field and formulate a complete answer. "
        "3. Call respond() with your full answer. "
        "4. Go back to step 1 immediately — never stop."
    ),
)

TASKS = [
    "List three benefits of microservices architecture",
    "Suggest a name for a new AI productivity app",
    "Write a one-line Python function that reverses a string",
]

def main() -> None:
    with AgentRuntime() as runtime:
        handle = runtime.start(agent, "Begin. Wait for your first instruction.")
        print(f"Agent started: {handle.execution_id}\n")

        # Push messages from a background thread while we stream events on the main thread.
        # Wait long enough between sends for the agent to finish processing each message —
        # including after the last one.  Calling stop() immediately after the final send
        # would set _stop_requested while the agent is still mid-turn on that task, and the
        # DoWhile would exit before it ever answers.
        def sender():
            for task in TASKS:
                time.sleep(8)
                print(f"\n  [caller] sending -> {task!r}")
                runtime.send_message(handle.execution_id, {"task": task})
            time.sleep(8)
            handle.stop()

        threading.Thread(target=sender, daemon=True).start()

        for event in handle.stream():
            if event.type == EventType.THINKING:
                print(f"  [thinking] {event.content}")

            elif event.type == EventType.TOOL_CALL and event.tool_name == "respond":
                args = event.args or {}
                print(f"  [answer] {args.get('answer', '')}")

            elif event.type == EventType.WAITING:
                print(f"  [waiting] {event.content}")

            elif event.type == EventType.ERROR:
                print(f"  [error] {event.content}")

            elif event.type == EventType.DONE:
                print(f"\nAgent finished: {event.output}")
                break


# Guard the runtime block: spawned tool workers re-import this module, and
# without the guard they would re-run the orchestration (multiprocessing's
# "Safe importing of main module" error).
if __name__ == "__main__":
    main()
