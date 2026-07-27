# OpenAI Agents SDK-style Conductor-agent examples

These examples show OpenAI Agents SDK-style agents running on the durable
Conductor runtime. Install `conductor-python[openai-agents]`, configure the
provider on the Conductor server, and set `CONDUCTOR_SERVER_URL` and
`CONDUCTOR_AGENT_LLM_MODEL`.

The bridge preserves familiar agent, tool, handoff, and streaming shapes while
Conductor records workflow state and tool execution. See the
[framework guide](../../../docs/agents/frameworks/openai.md).
