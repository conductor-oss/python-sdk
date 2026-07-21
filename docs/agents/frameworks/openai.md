# OpenAI Agents SDK

**Prerequisites:** install `conductor-python[openai-agents]` and configure the
provider credential on the Conductor server.

Install `conductor-python[openai-agents]`. The top-level `Runner` and
`function_tool` compatibility surface lets OpenAI Agents SDK-style applications
run through Conductor while retaining familiar agent, tool, handoff, and streaming
shapes.

```python
from conductor.ai import Runner, function_tool
```

The runtime still requires a Conductor server and server-side provider credential.
See the [OpenAI examples](../../../examples/agents/openai/README.md).

**Expected result:** familiar OpenAI Agents-style calls execute through Conductor.
**Next:** see [tools](../concepts/tools.md) and [runtime modes](../concepts/deploy-serve-run.md).
