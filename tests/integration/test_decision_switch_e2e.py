"""Opt-in JEV cases against a real, dedicated Conductor server.

RUN_JEV_E2E=1 CONDUCTOR_SERVER_URL=http://localhost:8081/api pytest -v -s \
    tests/integration/test_decision_switch_e2e.py

The server needs DECISION_API_KEY for OpenRouter and OPENAI_API_KEY for chat
specialists. Set JEV_EVIDENCE_DIR to save actual workflow histories. Optional
controlled cases require provider 'controlled' to point to localhost:18081
with a test API key; enable with RUN_JEV_CONTROLLED=1.
"""

import asyncio
import copy
import json
import os
import re
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from conductor.ai.agents import AgentRuntime
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api_client import ApiClient
from conductor.client.orkes_clients import OrkesClients
from examples.agentic_workflows.ai_decision_routing import create_workflow
from examples.agents.decision_router import support_router
from examples.agents.decision_tool import support_agent

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_JEV_E2E") != "1", reason="Set RUN_JEV_E2E=1 for live JEV cases"
)

BILLING = "I was charged twice on my latest invoice. Please review the duplicate charge."
TECHNICAL = "The product crashes with error 503 whenever I log in. Please troubleshoot."
REQUESTED_RETRIES = 3


@pytest.fixture
def clients():
    return OrkesClients(configuration=Configuration())


def snapshot(clients, workflow_id):
    """Include child histories so selected specialists and tools are verifiable."""
    workflow = clients.get_workflow_client().get_workflow(workflow_id, include_tasks=True)
    data = ApiClient().sanitize_for_serialization(workflow)
    children = []
    for task in data["tasks"]:
        child_id = task.get("outputData", {}).get("subWorkflowId")
        if child_id:
            children.append(snapshot(clients, child_id))
    return {"workflow": data, "children": children}


def record(request, data):
    directory = os.getenv("JEV_EVIDENCE_DIR")
    if directory:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        name = re.sub(r"[^a-zA-Z0-9_-]", "_", request.node.name)
        (path / f"{name}.json").write_text(json.dumps(data, indent=2))
    workflow = data["history"]["workflow"]
    print(f"{request.node.name}: {workflow['status']} {workflow['workflowId']}")


def wait(clients, workflow_id):
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        workflow = clients.get_workflow_client().get_workflow(workflow_id, include_tasks=True)
        if workflow.status in {"COMPLETED", "FAILED", "TIMED_OUT", "TERMINATED"}:
            return workflow
        time.sleep(0.25)
    raise TimeoutError(f"Workflow {workflow_id} did not finish within 120s")


def decision_tasks(history):
    tasks = [
        t
        for t in history["workflow"]["tasks"]
        if t.get("workflowTask", {}).get("evaluatorType") == "decision"
    ]
    for child in history["children"]:
        tasks.extend(decision_tasks(child))
    return tasks


def run_workflow(
    clients, request, prompt, *, provider="openrouter", configure=None, branch_only=False
):
    workflow = create_workflow(clients.get_workflow_executor(), provider=provider)
    workflow.name = "jev_e2e_" + uuid.uuid4().hex[:12]
    definition = workflow.to_workflow_def()
    if configure:
        configure(definition.tasks[0])
    if branch_only:
        definition.tasks = definition.tasks[:1]
        definition.output_parameters = {"selectedCase": "${route_request.output.selectedCase}"}
    clients.get_metadata_client().register_workflow_def(definition, overwrite=True)
    workflow_id = clients.get_workflow_client().start_workflow_by_name(
        workflow.name, version=1, input={"request": prompt}
    )
    result = wait(clients, workflow_id)
    evidence = {
        "definition": ApiClient().sanitize_for_serialization(definition),
        "history": snapshot(clients, workflow_id),
    }
    record(request, evidence)
    return result, evidence


@pytest.mark.parametrize(("prompt", "team"), [(BILLING, "billing"), (TECHNICAL, "technical")])
def test_live_direct_routing(clients, request, prompt, team):
    result, evidence = run_workflow(clients, request, prompt)
    assert result.status == "COMPLETED", result.reason_for_incompletion
    assert result.output["selectedCase"] == team
    assert result.output["result"]["team"] == team
    tasks = decision_tasks(evidence["history"])
    assert len(tasks) == 1
    assert tasks[0]["status"] == "COMPLETED"
    assert tasks[0]["outputData"]["provider"] == "openrouter"
    assert "jev" in tasks[0]["outputData"]["model"]
    assert result.output["usage"]["inputTokens"] > 0
    assert result.output["latencyMs"] >= 0
    assert result.output["cost"] >= 0
    branches = [t["referenceTaskName"] for t in evidence["history"]["workflow"]["tasks"]]
    assert f"handle_{team}" in branches
    assert f"handle_{'technical' if team == 'billing' else 'billing'}" not in branches


def test_live_single_question_infers_expression(clients, request):
    result, _ = run_workflow(
        clients, request, BILLING, configure=lambda task: setattr(task, "expression", "")
    )
    assert result.status == "COMPLETED", result.reason_for_incompletion
    assert result.output["selectedCase"] == "billing"


def test_live_multiple_question_types(clients, request):
    def configure(task):
        task.input_parameters["questions"].update(
            {
                "urgent": {
                    "type": "boolean",
                    "instructions": "Does this request describe an outage?",
                },
                "priority": {
                    "type": "score",
                    "instructions": "How urgent is this request?",
                    "scale": ["routine", "moderate", "urgent"],
                },
            }
        )

    result, evidence = run_workflow(clients, request, TECHNICAL, configure=configure)
    assert result.status == "COMPLETED", result.reason_for_incompletion
    assert result.output["selectedCase"] == "technical"
    answers = result.output["answers"]
    assert set(answers) == {"route", "urgent", "priority"}
    assert 0 <= answers["urgent"]["probability"] <= 1
    scale = evidence["definition"]["tasks"][0]["inputParameters"]["questions"]["priority"]["scale"]
    assert 0 <= answers["priority"]["score"] < len(scale)


@pytest.mark.parametrize(("prompt", "team"), [(BILLING, "billing"), (TECHNICAL, "technical")])
def test_live_agent_router(clients, request, prompt, team):
    agent = support_router()
    agent.name += "_" + uuid.uuid4().hex[:8]
    for child in agent.agents:
        child.max_tokens = 256
    with AgentRuntime(Configuration()) as runtime:
        plan = runtime.plan(agent, prompt)
        runtime.deploy(agent)
        result = runtime.start(agent, prompt).join(timeout=120)
    evidence = {"plan": plan, "history": snapshot(clients, result.execution_id)}
    record(request, evidence)
    assert result.is_success, result.error
    tasks = decision_tasks(evidence["history"])
    assert len(tasks) == 1
    assert tasks[0]["outputData"]["selectedCase"] == team
    assert evidence["history"]["children"], "The selected specialist must execute"
    assert result.output["result"]


def test_live_async_agent_router(clients, request):
    async def run():
        agent = support_router()
        agent.name += "_async_" + uuid.uuid4().hex[:8]
        for child in agent.agents:
            child.max_tokens = 256
        async with AgentRuntime(Configuration()) as runtime:
            await runtime.deploy_async(agent)
            handle = await runtime.start_async(agent, BILLING)
            return await handle.join_async(timeout=120)

    result = asyncio.run(run())
    evidence = {"history": snapshot(clients, result.execution_id)}
    record(request, evidence)
    assert result.is_success, result.error
    assert decision_tasks(evidence["history"])[0]["outputData"]["selectedCase"] == "billing"
    assert result.output["result"]


def test_live_decision_tool(clients, request):
    agent = copy.deepcopy(support_agent)
    agent.name += "_" + uuid.uuid4().hex[:8]
    agent.max_tokens = 256
    agent.max_turns = 3
    agent.instructions = "Call classify_request exactly once, then report its department choice."
    with AgentRuntime(Configuration()) as runtime:
        result = runtime.run(agent, BILLING, timeout=120)
    evidence = {"history": snapshot(clients, result.execution_id)}
    record(request, evidence)
    assert result.is_success, result.error
    tasks = decision_tasks(evidence["history"])
    assert len(tasks) == 1, "The chat agent must actually invoke the decision tool"
    assert tasks[0]["outputData"]["answers"]["department"]["choice"] == "billing"
    assert tasks[0]["status"] == "COMPLETED"
    assert result.output["result"]


@pytest.fixture(scope="module")
def controlled_server():
    if os.getenv("RUN_JEV_CONTROLLED") != "1":
        pytest.skip("Set RUN_JEV_CONTROLLED=1 and configure the dedicated test provider")
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append(payload)
            state = payload["state"]
            status = int(state) if state in {"400", "503"} else 200
            response = {
                "model": "typesafe/jev-test",
                "id": "controlled-response",
                "answers": {"route": {"type": "choice", "choice": "billing", "confidence": 1}},
                "usage": {"input_tokens": 10, "output_tokens": 1, "cost": 0.00001},
            }
            if state == "invalid_choice":
                response["answers"]["route"]["choice"] = "unknown"
            body = b"{" if state == "malformed" else json.dumps(response).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Connection", "close")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("localhost", 18081), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.fixture
def controlled_provider(controlled_server):
    controlled_server.clear()
    return controlled_server


@pytest.mark.parametrize(
    ("state", "error"),
    [
        ("503", "Decision HTTP status 503"),
        ("400", "Decision HTTP status 400"),
        ("malformed", "Invalid Decision JSON response"),
        ("invalid_choice", "invalid choice answer"),
    ],
)
def test_provider_failure_has_no_task_retries(clients, request, controlled_provider, state, error):
    result, evidence = run_workflow(
        clients,
        request,
        state,
        provider="controlled",
        configure=lambda task: setattr(task, "retry_count", REQUESTED_RETRIES),
    )
    assert result.status == "FAILED"
    assert len(result.tasks) == 1
    task = evidence["history"]["workflow"]["tasks"][0]
    assert task["status"] == "FAILED"
    assert task["workflowTask"]["retryCount"] == REQUESTED_RETRIES
    assert error in task["reasonForIncompletion"]
    assert not task.get("retried", False)
    assert task.get("retryCount", 0) == 0
    assert len(controlled_provider) == 1


@pytest.mark.parametrize("case", ["empty_match", "default"])
def test_empty_and_default_branches(clients, request, controlled_provider, case):
    def configure(task):
        if case == "empty_match":
            task.decision_cases["billing"] = []
            task.default_case = copy.deepcopy(task.decision_cases["technical"])
            task.default_case[0].task_reference_name = "default_branch"
        else:
            task.default_case = task.decision_cases.pop("billing")

    result, evidence = run_workflow(
        clients,
        request,
        BILLING,
        provider="controlled",
        configure=configure,
        branch_only=case == "empty_match",
    )
    assert result.status == "COMPLETED", result.reason_for_incompletion
    names = [t["referenceTaskName"] for t in evidence["history"]["workflow"]["tasks"]]
    assert "handle_technical" not in names
    assert "default_branch" not in names
    assert ("handle_billing" in names) == (case == "default")
    assert len(controlled_provider) == 1
