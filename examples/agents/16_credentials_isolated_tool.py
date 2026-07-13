# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""Credentials — per-user secrets injected into isolated tool subprocesses.

Demonstrates:
    - @tool with credentials=["GH_TOKEN"] declares the tool's secret needs
    - Credentials injected into a fresh subprocess — parent env never touched
    - Tool reads credential from os.environ inside the subprocess
    - Fails closed if a declared credential isn't delivered — no ambient-env fallback

How it works:
    1. Declaring credentials=["GH_TOKEN"] stamps the name on the tool's
       TaskDef.runtimeMetadata at registration (conductor-oss PR #1255).
    2. At poll time the server resolves that name against its credential
       store and delivers the value wire-only on Task.runtimeMetadata —
       never persisted, no separate fetch call or execution token.
    3. The tool function runs in a fresh subprocess with the delivered
       value injected as an env var. The parent process's os.environ is
       unchanged. If a declared credential wasn't delivered, the call fails
       instead of silently reading the ambient environment.

Setup (one-time, via CLI):
    agentspan login                                     # authenticate
    agentspan credentials set GH_TOKEN <your-github-token> # enter token when prompted

Requirements:
    - Agentspan server running at AGENTSPAN_SERVER_URL (with runtimeMetadata support)
    - AGENTSPAN_LLM_MODEL set (or defaults to openai/gpt-5.4)
    - GH_TOKEN stored via `agentspan credentials set`
"""

import os
import subprocess

from settings import settings

from conductor.ai.agents import Agent, AgentRuntime, tool


@tool(credentials=["GH_TOKEN"])
def list_github_repos(username: str) -> dict:
    """List public repositories for a GitHub user.

    The GH_TOKEN env var is injected into this subprocess automatically.
    """
    token = os.environ.get("GH_TOKEN", "")
    headers = ["Accept: application/vnd.github+json"]
    if token:
        headers.append(f"Authorization: Bearer {token}")

    result = subprocess.run(
        [
            "curl",
            "-sf",
            "-H",
            headers[0],
            "-H",
            headers[-1],
            f"https://api.github.com/users/{username}/repos?per_page=5&sort=updated",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return {"error": result.stderr.strip()}

    import json

    repos = json.loads(result.stdout)
    return {
        "username": username,
        "repos": [{"name": r["name"], "stars": r["stargazers_count"]} for r in repos],
        "authenticated": bool(token),
    }


@tool(credentials=["GH_TOKEN"])
def create_github_issue(repo: str, title: str, body: str) -> dict:
    """Create a GitHub issue. Requires GH_TOKEN with write access.

    repo format: "owner/repo-name"
    """
    token = os.environ.get("GH_TOKEN")
    if not token:
        return {"error": "GH_TOKEN not available — cannot create issues without auth"}

    import json

    payload = json.dumps({"title": title, "body": body})
    result = subprocess.run(
        [
            "curl",
            "-sf",
            "-X",
            "POST",
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            f"Authorization: Bearer {token}",
            "-H",
            "Content-Type: application/json",
            "-d",
            payload,
            f"https://api.github.com/repos/{repo}/issues",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return {"error": result.stderr.strip()}

    issue = json.loads(result.stdout)
    return {"issue_number": issue.get("number"), "url": issue.get("html_url")}


agent = Agent(
    name="github_agent",
    model=settings.llm_model,
    tools=[list_github_repos, create_github_issue],
    # Declare credentials at the agent level — SDK auto-fetches for all tools
    credentials=["GH_TOKEN"],
    instructions=(
        "You are a GitHub assistant. You can list repos and create issues. "
        "Always confirm with the user before creating issues."
    ),
)


if __name__ == "__main__":
    with AgentRuntime() as runtime:
        result = runtime.run(
            agent,
            "List the 5 most recently updated repos for the 'agentspan-ai' GitHub org.",
        )
        result.print_result()

        # Production pattern:
        # 1. Deploy once during CI/CD:
        # runtime.deploy(agent)
        # CLI alternative:
        # agentspan deploy --package examples.16_credentials_isolated_tool
        #
        # 2. In a separate long-lived worker process:
        # runtime.serve(agent)
