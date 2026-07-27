# Google ADK Conductor-agent examples

These examples run standard Google ADK agents through the durable Conductor agent
runtime. Install `conductor-python[adk]`, configure a server-side Gemini/provider
integration, and set `CONDUCTOR_SERVER_URL` plus `CONDUCTOR_AGENT_LLM_MODEL`.

Run examples from `examples/agents` so shared settings resolve correctly. See the
[Google ADK guide](../../../docs/agents/frameworks/google-adk.md) for the supported
bridge contract.
