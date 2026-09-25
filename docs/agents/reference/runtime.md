# AgentRuntime reference

**Audience:** applications owning local tool workers and Conductor-agent lifecycle.

## Prerequisites

Create one runtime per application lifetime with a configured server connection.
Use a context manager for scripts and an application shutdown hook for services.

`AgentRuntime` owns connection-facing clients, local tool workers, and execution
lifecycle. Use it as a context manager or call `shutdown()`.

| Method | Returns | Purpose |
|---|---|---|
| `run` / `run_async` | `AgentResult` | Start and wait for completion. |
| `start` / `start_async` | `AgentHandle` | Start without waiting. |
| `stream` / `stream_async` | stream | Consume agent events. |
| `plan` | compiled definition | Compile without registration or execution. |
| `deploy` / `deploy_async` | deployment information | Register agent definitions. |
| `serve` | none | Deploy and poll tool workers. |
| `resume` / `resume_async` | `AgentHandle` | Reattach to an execution. |

`AgentConfig.from_env()` reads canonical `CONDUCTOR_AGENT_*` settings. Connection,
auth, and SDK log level belong to `Configuration` and use `CONDUCTOR_*`. Share one
runtime for an application lifetime; do not create one per request.

## Expected result and common failures

`RunSettings` overrides model/runtime options for one run without mutating the
agent definition. Use `on_event` or `stream()` for progress, and `resume()` to
reattach local workers after a process restart. A `SCHEDULED` tool task means no
compatible worker process is polling; a model error normally means the server
provider setup is incomplete.

## Cleanup and next steps

Call `shutdown()` or exit the context manager to stop local workers. Continue with
[runtime modes](../concepts/deploy-serve-run.md) and [client control](client.md).
