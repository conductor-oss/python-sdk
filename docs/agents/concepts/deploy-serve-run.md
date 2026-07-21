# Deploy · Serve · Run · Plan

**Audience:** developers choosing a local, CI/CD, or long-lived runtime mode.

## Prerequisites

Create an `AgentRuntime` with the target Conductor configuration. Ensure every
Python `@tool` is importable in the process that will call `serve()` or `run()`.

| Operation | Effect |
|---|---|
| `runtime.plan(agent)` | Compile only; does not register or execute. |
| `runtime.deploy(agent)` | Compile and register; does not execute. |
| `runtime.serve(agent)` | Deploy, start local tool workers, and block. |
| `runtime.run(agent, prompt)` | Start and wait for an `AgentResult`. |
| `runtime.start(agent, prompt)` | Start and return an `AgentHandle`. |
| `runtime.resume(execution_id, agent)` | Reattach workers to a prior execution. |

Use `deploy` in CI/CD and `serve` in long-lived worker processes. `run` is the
best local quickstart. Always call `shutdown()` or use `with AgentRuntime()` for
short-lived programs. See the [runtime reference](../reference/runtime.md).

## Production pattern

Compile/register with `deploy()` during release, then run `serve()` in one or more
long-lived worker services. Use `plan()` in CI to inspect the compiled workflow
before deployment. Use `start()` for asynchronous callers and `resume()` after a
local worker process restart.

## Expected result and cleanup

`deploy()` returns deployment information without executing an agent; `serve()`
blocks until interrupted; `run()` returns a terminal `AgentResult`. Use the
runtime context manager or `shutdown()` to stop local polling cleanly.

## Next steps

See [deployment and scaling](../../deployment-scaling.md), [runtime reference](../reference/runtime.md), and [agent client](../reference/client.md).
