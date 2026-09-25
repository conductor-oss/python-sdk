# Reliability: timeouts, retries, idempotency, and domains

Set poll, response, and execution timeouts on every worker task definition. Retry
only idempotent or compensated work, use exponential backoff for transient remote
failures, and route resource-bound work to domains.

Workers may receive a task more than once. Persist idempotency keys before external
side effects and use `TaskInProgress` or lease extension for long-running work.
Verify behavior with failure-path tests and inspect task reasons before retrying.
