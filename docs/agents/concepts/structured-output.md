# Structured output

**Audience:** callers requiring a validated, typed final answer from a
Conductor agent.

## Prerequisites

Define a small dataclass or Pydantic model with explicit optional fields. Ensure
the prompt asks for the same shape the model declares.

Set `output_type` to a dataclass or Pydantic model to ask the server to validate
the final result against a schema. Keep the model small, make optional fields
explicit, and handle validation failures as retryable only when the prompt can
produce a different result. The returned `AgentResult.output` is the parsed value
when validation succeeds.

## Expected result and failures

Successful runs return the parsed typed value. A validation error means the model
did not satisfy the requested contract; improve instructions or use a bounded
retry policy rather than silently accepting malformed data.

## Next steps

See [agent schema](../reference/agent-schema.md), [guardrails](guardrails.md), and
[runtime reference](../reference/runtime.md).
