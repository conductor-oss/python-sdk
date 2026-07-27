# LangGraph

**Prerequisites:** install `conductor-python[langgraph]` and keep recoverable
graph nodes free of process-local state.

Install `conductor-python[langgraph]` and pass a supported LangGraph graph to
`AgentRuntime`. The bridge executes graph work through the durable runtime and
preserves streaming and human-task integration where the graph exposes it.

Start with the [LangGraph examples](../../../examples/agents/langgraph/README.md).
Avoid closures and process-local state in nodes that must run after recovery.

**Expected result:** graph work and emitted events are recorded in a durable
Conductor-agent execution. **Next:** read [streaming](../concepts/streaming-hitl.md).
