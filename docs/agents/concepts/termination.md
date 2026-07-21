# Termination conditions

**Audience:** authors bounding cost, time, and unsafe open-ended delegation.

## Prerequisites

Set a meaningful `max_turns` and decide which completion signal is safe for the
business operation before selecting an additional termination condition.

Use `MaxMessageTermination`, `StopMessageTermination`, `TextMentionTermination`,
or `TokenUsageTermination` to bound agent execution. Conditions compose with `&`
and `|`; pair them with `max_turns` for defense in depth.

Stop a live execution through `AgentHandle` or `AgentClient.stop()`. A stop should
be safe to repeat and must not assume an in-flight external tool call is reversible.

## Expected result and failures

A terminal condition ends the durable execution with its recorded reason. If a
tool has already started, stopping the agent does not undo its external side
effect; design compensating work where necessary.

## Next steps

Continue with [multi-agent](multi-agent.md), [reliability](../../reliability.md),
and [agent client control](../reference/client.md).
