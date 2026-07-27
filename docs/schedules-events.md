# Schedules and events

Use `SchedulerClient` for workflow schedules and the event client for event-driven
integration. Give scheduled executions a stable correlation or idempotency key so
retries do not duplicate business effects.

```python
scheduler = clients.get_scheduler_client()
# scheduler.save_schedule(...)
```

See [SCHEDULE.md](SCHEDULE.md) for the complete schedule request model and
[workflow lifecycle](workflow-lifecycle.md) for safe operational handling.
