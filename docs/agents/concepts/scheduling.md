# Scheduling

**Audience:** operators scheduling recurring Conductor-agent executions.

## Prerequisites

Deploy the agent, choose a stable schedule name, and decide the correlation or
idempotency key that prevents duplicate business work.

Deploy an agent before scheduling it, then use the shared scheduler client from
`runtime.schedules_client()` or `OrkesClients.get_scheduler_client()`. Use stable
schedule names, timezone-aware cron expressions, and idempotent workflow input.

The schedule API is the core workflow scheduler, not a separate agent-only facade.
See [SCHEDULE.md](../../SCHEDULE.md) for request fields and lifecycle operations.

## Expected result and cleanup

A saved schedule starts the deployed agent on its cron cadence. Pause or delete
the schedule before removing the agent definition or retiring the worker service.

## Next steps

Read [schedules and events](../../schedules-events.md) and [runtime modes](deploy-serve-run.md).
