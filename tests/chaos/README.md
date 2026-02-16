# Chaos Tests (TaskHandler)

These tests are intentionally heavier than unit tests. They run `TaskHandler` with real multiprocessing worker
processes and inject failures (protocol errors, forced worker kills) to validate that:

- Workers keep polling under transient transport failures
- `TaskHandler` detects dead worker processes and restarts them

## Run

Chaos tests are opt-in and skipped by default.

```bash
RUN_CHAOS_TESTS=1 pytest -q tests/chaos -q
```

Default timeout is 60s (set `CHAOS_TEST_TIMEOUT_SECONDS` to override) so runs cannot hang CI.

## What is simulated

- A transport-level stub for `httpx.Client` (used by the SDK REST layer) that:
  - returns `[]` for `GET /tasks/poll/batch/{tasktype}`
  - optionally raises `httpx.ProtocolError` on the first poll call
  - returns `OK` for `POST /tasks`

## Notes

- These tests do not require a real Conductor/Orkes server.
- They do not validate "real" HTTP/2 GOAWAY semantics (that requires an HTTP/2-capable proxy/server), but they do
  validate the SDK code paths that handle protocol errors and reset the underlying client.
