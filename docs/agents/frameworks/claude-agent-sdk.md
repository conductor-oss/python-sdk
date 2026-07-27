# Claude Agent SDK

**Prerequisites:** install `conductor-python[claude]`, configure the provider on
the Conductor server, and review any repository or shell access before use.

Install `conductor-python[claude]` and the supported Claude Agent SDK dependency.
Pass a native Claude agent/options object to `AgentRuntime`; the bridge adapts it
to a durable Conductor-agent execution and preserves tool lifecycle events.

Review CLI/code tool allowlists before running against real repositories or
credentials. See [tools](../concepts/tools.md) and the framework examples.

**Expected result:** the native Claude agent executes through the durable runtime
while preserving tool lifecycle events. **Next:** read [security](../../security.md).
