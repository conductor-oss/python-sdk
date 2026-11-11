"""Serve from Package — auto-discover and serve all agents in a package.

Demonstrates:
    - runtime.serve(packages=["myapp.agents"]) — auto-discovery
    - Scanning Python packages for module-level Agent instances
    - Mixing explicit agents with package-based discovery

discover_agents() recursively imports the specified packages and
collects all module-level Agent instances. This avoids the need to
explicitly list every agent when serving a large codebase.

serve() registers each agent on the server (compile + register, like
deploy()) and then serves its Python tool workers, blocking until Ctrl+C.
Run this in one terminal and run the matching run-by-name client
(63e_run_monitoring.py) in another; without a serving process the client
schedules tool tasks that nothing ever polls, so it hangs.

    python 63d_serve_from_package.py

Requirements:
    - Conductor server running
    - CONDUCTOR_SERVER_URL=http://localhost:8080/api in .env or environment
    - CONDUCTOR_AGENT_LLM_MODEL=openai/gpt-4o-mini in .env or environment
"""

from conductor.ai.agents import Agent, AgentRuntime, discover_agents, tool
from settings import settings


# ── Option 1: Discover agents from packages ──────────────────────────

# Preview what would be discovered (useful for debugging)
# agents = discover_agents(["myapp.agents"])
# for a in agents:
#     print(f"  Discovered: {a.name}")


# ── Option 2: Mix explicit agents with package discovery ─────────────

@tool
def health_check() -> str:
    """Perform a basic health check.

    Returns:
        Health status message.
    """
    return "All systems operational"


monitoring_agent = Agent(
    name="monitoring",
    model=settings.llm_model,
    tools=[health_check],
    instructions="You monitor system health.",
)


if __name__ == "__main__":
    with AgentRuntime() as runtime:
        # serve() registers monitoring on the server, serves its tool workers,
        # and blocks until Ctrl+C. Run this in one terminal so that
        # 63e_run_monitoring.py (and any other run-by-name client) finds a live
        # process polling the monitoring agent's task queue.
        #
        # Add packages=["myapp.agents"] to auto-discover and serve every
        # module-level Agent in that package alongside the explicit agent.
        runtime.serve(monitoring_agent)
