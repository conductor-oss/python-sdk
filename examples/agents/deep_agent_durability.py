"""Deep agent — survive a worker crash in the middle of a tool call.

Phase 1 starts a run whose only tool, send_notification, records its side
effect and then kills its own worker process before reporting back, the way a
crash would. The script then kills every worker it started and hands the
execution id to phase 2.

Phase 2 runs in a fresh process. It resumes the execution by id, which
registers new workers; the server retries the task after its response timeout;
the run completes. The script then reports how many times the tool was
attempted and how many times the side effect actually happened.

What this shows:
    - a run survives losing every worker mid call; nothing is persisted by the
      caller except the execution id
    - the server delivers a tool call at least once, so a tool with a side
      effect must be idempotent; here it dedupes on (execution, message)

Requirements:
    - Conductor server with LLM support
    - CONDUCTOR_SERVER_URL=http://localhost:8080/api as environment variable
    - CONDUCTOR_AGENT_LLM_MODEL=openai/gpt-4o-mini as environment variable
"""

import multiprocessing
import os
import subprocess
import sys
import time

from conductor.ai.agents import AgentRuntime, tool
from conductor.ai.agents.deep import deep_agent, workspace_dir
from conductor.ai.agents.tool import ToolContext
from settings import settings

WORKSPACE = "./workspace"


def _logs(execution_id: str):
    ws = workspace_dir(execution_id, WORKSPACE)
    ws.mkdir(parents=True, exist_ok=True)
    return ws / "attempts.log", ws / "effects.log", ws / "crashed.flag"


@tool
def send_notification(message: str, context: ToolContext = None) -> dict:
    """Send a notification message to the user. Call it once per message.

    Args:
        message: The text to send.
    """
    attempts, effects, crashed = _logs(context.execution_id)
    with attempts.open("a") as f:
        f.write(message + "\n")

    # Idempotency: the server may deliver this call again after a crash, so
    # skip the side effect if this run already sent this message.
    already = effects.exists() and message in effects.read_text().splitlines()
    if not already:
        with effects.open("a") as f:
            f.write(message + "\n")

    # First attempt only: die after the side effect, before reporting back.
    if not crashed.exists():
        crashed.write_text("1")
        os._exit(1)

    return {"sent": message, "duplicate": already}


agent = deep_agent(
    name="notifier",
    model=settings.llm_model,
    instructions=(
        "Send exactly one notification with the text 'deploy finished' using "
        "send_notification, then reply with the word done. This is a single-step "
        "task, so do not write a plan."
    ),
    tools=[send_notification],
    workspace=WORKSPACE,
)


def phase1() -> None:
    with AgentRuntime() as runtime:
        handle = runtime.start(agent, "Notify me that the deploy finished.")
        print(f"Phase 1: started {handle.execution_id}")
        attempts, _, crashed = _logs(handle.execution_id)
        for _ in range(120):
            if crashed.exists():
                break
            time.sleep(1)
        else:
            print("Phase 1: the tool never ran; giving up")
            return
        print(
            f"Phase 1: tool crashed after {len(attempts.read_text().splitlines())} attempt(s); "
            "killing every worker"
        )
        for p in multiprocessing.active_children():
            p.kill()
        execution_id = handle.execution_id
    # The runtime is gone. A new process picks the run up from the id alone.
    subprocess.run([sys.executable, __file__, "--resume", execution_id], check=False)


def phase2(execution_id: str) -> None:
    with AgentRuntime() as runtime:
        handle = runtime.resume(execution_id, agent)
        print(f"Phase 2: resumed {execution_id}; waiting for the server to retry the task")
        result = handle.join(timeout=240)
        attempts, effects, _ = _logs(execution_id)
        n_attempts = len(attempts.read_text().splitlines()) if attempts.exists() else 0
        n_effects = len(effects.read_text().splitlines()) if effects.exists() else 0
        print(f"Phase 2: status={result.status} attempts={n_attempts} side_effects={n_effects}")
        print(f"Phase 2: output={result.output!r}")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--resume":
        phase2(sys.argv[2])
    else:
        phase1()
