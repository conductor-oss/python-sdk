# Guardrails

**Audience:** authors defining validation and safety controls for Conductor-agent
input, output, or tool work.

## Prerequisites

Decide whether failure should block, retry, repair, or require human review. Test
both a passing and failing value before deploying a guardrail.

Guardrails validate input or output before it affects the next agent step. Use
`RegexGuardrail`, `LLMGuardrail`, a `Guardrail`, or `@guardrail` for custom logic.
`OnFail` can retry, raise, fix, or request a human decision.

Attach guardrails to an agent or tool, keep custom functions importable by worker
processes, and avoid sending secrets to model-based validation. Test both pass and
failure paths. See [API reference](../reference/api.md).

## Patterns

Use `RegexGuardrail` for deterministic format checks, `LLMGuardrail` for semantic
policy checks, and a custom `@guardrail` only when the rule needs application
state. Apply a tool guardrail closest to the side effect; use an agent guardrail
for broad input/output policy. A retry policy is appropriate only when a new model
response can plausibly pass.

## Expected result and failures

Guardrail decisions appear in the execution history. If a model-based guardrail
receives a secret or raw sensitive record, remove that input and validate a
redacted representation instead.

## Next steps

Pair guardrails with [human approval](streaming-hitl.md), [tool policy](tools.md),
and [security guidance](../../security.md).
