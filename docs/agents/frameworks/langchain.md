# LangChain

**Prerequisites:** install `conductor-python[langchain]`; keep callback and tool
functions importable by worker processes.

Install `conductor-python[langchain]`, then pass supported LangChain agents or
tools to the runtime bridge. The bridge retains framework authoring while
Conductor supplies durable execution, worker-backed tools, and observability.

Keep callbacks and tool callables importable by worker processes. See the
[framework examples](../../../examples/agents/README.md) and [tools](../concepts/tools.md).

**Expected result:** the bridge preserves LangChain authoring while Conductor owns
durable execution. **Next:** use [runtime modes](../concepts/deploy-serve-run.md).
