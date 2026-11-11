"""Serve — keep tool workers running as a persistent service.

Demonstrates:
    - runtime.serve() to register agents + Python workers and block until interrupted
    - Serving multiple agents in a single process
    - The deploy/serve/run separation: this process owns the workers for a
      pre-deployed agent while another process runs it by name

serve() = deploy() + serve: it registers each agent on the server (compiles
the workflow and task definitions), registers the local Python tool functions
(tools, custom guardrails, callbacks, handoff checks) as Conductor workers,
and starts polling for tasks. It blocks until Ctrl+C / SIGTERM.

Run this in one terminal and run the matching run-by-name client
(63c_run_by_name.py) in another. Without a process serving the workers the
run-by-name client schedules tool tasks that nothing ever polls, so it hangs.

    python 63b_serve.py

Requirements:
    - Conductor server running
    - CONDUCTOR_SERVER_URL=http://localhost:8080/api in .env or environment
    - CONDUCTOR_AGENT_LLM_MODEL=openai/gpt-4o-mini in .env or environment
"""

from conductor.ai.agents import Agent, AgentRuntime, tool
from settings import settings


@tool
def search_docs(query: str) -> str:
    """Search internal documentation.

    Args:
        query: Search query string.

    Returns:
        Matching documentation excerpts.
    """
    return f"Found 3 results for: {query}"


@tool
def check_status(service: str) -> str:
    """Check service health status.

    Args:
        service: Name of the service to check.

    Returns:
        Health status string.
    """
    return f"{service}: healthy"


# ── Define agents (same definitions as 63_deploy.py) ─────────────────

doc_assistant = Agent(
    name="doc_assistant",
    model=settings.llm_model,
    tools=[search_docs],
    instructions="Help users find documentation. Use search_docs to look up answers.",
)

ops_bot = Agent(
    name="ops_bot",
    model=settings.llm_model,
    tools=[check_status],
    instructions="Monitor service health. Use check_status to inspect services.",
)

if __name__ == "__main__":
    with AgentRuntime() as runtime:
        # serve() registers doc_assistant/ops_bot on the server, then serves
        # their tool workers and blocks until Ctrl+C. Run this in one terminal
        # so that 63c_run_by_name.py (and any other run-by-name client) finds
        # a live process polling the agents' task queues.
        runtime.serve(doc_assistant, ops_bot)
