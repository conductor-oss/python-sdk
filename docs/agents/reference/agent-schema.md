# Agent configuration contract

**Audience:** integrators inspecting or validating the `agentConfig` payload sent
to the Conductor agent control plane.

## Canonical schema

The canonical Python wire contract is the dictionary emitted by
`conductor.ai.agents.config_serializer.AgentConfigSerializer` under the
`agentConfig` request field. Its serializer tests validate supported agent,
tool, guardrail, handoff, memory, termination, callbacks, planning, and framework
configuration shapes.

Configuration keys are camelCase on the wire even when Python constructor fields
are snake_case. Nested `agents`, `router`, `planner`, and `fallback` serialize
recursively. The published [JSON Schema](agent-schema.json) rejects unknown root
agent fields while allowing intentionally open JSON payloads such as metadata,
tool input schemas, and framework passthrough configuration.

## Compatibility

The schema describes payloads emitted by the current Python serializer; it is not
a promise that arbitrary server-side fields can be supplied by callers. Extend the
serializer, schema, reference, and contract tests together when adding a public
agent field. For request envelopes and responses, see [AgentClient](client.md).

## Next steps

Read [agent definition fields](agent-definition.md) for Python authoring and
[runtime](runtime.md) for submission lifecycle.
