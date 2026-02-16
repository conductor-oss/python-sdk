"""
FastAPI + Conductor workers in one process.

Install (example-only deps):
    pip install fastapi uvicorn

Run (single web worker; TaskHandler will spawn one process per Conductor worker):
    export CONDUCTOR_SERVER_URL="http://localhost:8080/api"
    export CONDUCTOR_AUTH_KEY="..."
    export CONDUCTOR_AUTH_SECRET="..."
    uvicorn examples.fastapi_worker_service:app --host 0.0.0.0 --port 8081 --workers 1

Trigger the workflow via API (waits up to 10s for completion):
    curl -s -X POST http://localhost:8081/v1/hello \\
      -H 'content-type: application/json' \\
      -d '{"name":"Ada","a":2,"b":3}' | jq .

Notes:
  - Do NOT run uvicorn with multiple web workers unless you explicitly want multiple independent TaskHandlers polling.
  - TaskHandler supervision is enabled by default (monitor + restart worker subprocesses).
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.context.task_context import get_task_context
from conductor.client.orkes_clients import OrkesClients
from conductor.client.worker.worker_task import worker_task
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor


# ---------------------------------------------------------------------------
# Example worker(s)
# ---------------------------------------------------------------------------

@worker_task(
    task_definition_name="fastapi_normalize_name",
    poll_interval_millis=100,
    register_task_def=True,
    overwrite_task_def=False,
)
def normalize_name(name: str) -> str:
    # This shows how to access task context safely.
    _ = get_task_context()
    return name.strip().title()


@worker_task(
    task_definition_name="fastapi_add_numbers",
    poll_interval_millis=100,
    register_task_def=True,
    overwrite_task_def=False,
)
def add_numbers(a: int, b: int) -> int:
    _ = get_task_context()
    return a + b


@worker_task(
    task_definition_name="fastapi_build_message",
    poll_interval_millis=100,
    register_task_def=True,
    overwrite_task_def=False,
)
def build_message(normalized_name: str, total: int) -> dict:
    ctx = get_task_context()
    return {
        "message": f"Hello {normalized_name}! {total=}",
        "normalized_name": normalized_name,
        "total": total,
        "task_id": ctx.get_task_id(),
        "workflow_id": ctx.get_workflow_instance_id(),
    }


def _build_hello_workflow(executor: WorkflowExecutor) -> ConductorWorkflow:
    workflow = ConductorWorkflow(executor=executor, name="fastapi_hello_workflow", version=1)

    t1 = normalize_name(task_ref_name="normalize_name_ref", name=workflow.input("name"))
    t2 = add_numbers(task_ref_name="add_numbers_ref", a=workflow.input("a"), b=workflow.input("b"))
    t3 = build_message(
        task_ref_name="build_message_ref",
        normalized_name=t1.output("result"),
        total=t2.output("result"),
    )

    workflow >> t1 >> t2 >> t3

    workflow.output_parameters(
        output_parameters={
            "message": t3.output("message"),
            "normalized_name": t3.output("normalized_name"),
            "total": t3.output("total"),
        }
    )

    return workflow


class HelloRequest(BaseModel):
    name: str = Field(default="World", description="Name to greet")
    a: int = Field(default=1, description="First number")
    b: int = Field(default=2, description="Second number")


# ---------------------------------------------------------------------------
# FastAPI app + TaskHandler lifecycle
# ---------------------------------------------------------------------------

task_handler: Optional[TaskHandler] = None
workflow_executor: Optional[WorkflowExecutor] = None
api_config: Optional[Configuration] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global task_handler, workflow_executor, api_config

    api_config = Configuration()
    clients = OrkesClients(configuration=api_config)
    workflow_executor = clients.get_workflow_executor()

    # scan_for_annotated_workers=True will pick up @worker_task functions in this module.
    task_handler = TaskHandler(
        workers=[],
        configuration=api_config,
        scan_for_annotated_workers=True,
        # Defaults are already True, but keeping these explicit in the example:
        monitor_processes=True,
        restart_on_failure=True,
    )
    task_handler.start_processes()

    try:
        yield
    finally:
        if task_handler is not None:
            task_handler.stop_processes()
            task_handler = None
        workflow_executor = None
        api_config = None


app = FastAPI(lifespan=lifespan)


@app.get("/healthcheck")
def healthcheck():
    # 503 if worker processes aren't healthy; useful for container orchestrators.
    if task_handler is None:
        return JSONResponse({"ok": False, "detail": "workers_not_started"}, status_code=503)

    ok = task_handler.is_healthy()
    payload = {
        "ok": ok,
        "workers": task_handler.get_worker_process_status(),
    }
    return JSONResponse(payload, status_code=200 if ok else 503)


@app.post("/v1/hello")
def hello(req: HelloRequest):
    """
    Expose a Conductor workflow as an API:
    - Builds an inline workflow definition with 3 SIMPLE tasks
    - Starts it and waits up to 10 seconds for completion
    - Returns workflow output as the HTTP response
    """
    if task_handler is None or workflow_executor is None or api_config is None:
        return JSONResponse({"ok": False, "detail": "service_not_ready"}, status_code=503)
    if not task_handler.is_healthy():
        return JSONResponse(
            {"ok": False, "detail": "workers_unhealthy", "workers": task_handler.get_worker_process_status()},
            status_code=503,
        )

    workflow = _build_hello_workflow(executor=workflow_executor)
    payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()  # pydantic v2/v1

    try:
        run = workflow.execute(workflow_input=payload, wait_for_seconds=10)
    except Exception as e:
        return JSONResponse({"ok": False, "detail": "workflow_start_failed", "error": str(e)}, status_code=502)

    response = {
        "ok": run.status == "COMPLETED",
        "workflow_id": run.workflow_id,
        "status": run.status,
        "output": run.output,
        "ui_url": f"{api_config.ui_host}/execution/{run.workflow_id}",
    }
    return JSONResponse(response, status_code=200 if run.status == "COMPLETED" else 202)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "examples.fastapi_worker_service:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8081")),
        workers=1,
    )
