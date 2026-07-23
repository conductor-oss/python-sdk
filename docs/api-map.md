# Core API map

| Need | Python type | Reference |
|---|---|---|
| Configure transport and auth | `Configuration` / `OrkesClients` | [connection/authentication](connection-authentication.md) |
| Run workflow executions | `WorkflowExecutor` / `WorkflowClient` | [WORKFLOW.md](WORKFLOW.md) |
| Poll and update tasks | `TaskHandler` / `TaskClient` | [TASK_MANAGEMENT.md](TASK_MANAGEMENT.md) |
| Manage definitions | `MetadataClient` | [METADATA.md](METADATA.md) |
| Schedule workflows | `SchedulerClient` | [SCHEDULE.md](SCHEDULE.md) |
| Manage schemas | `SchemaClient` | [schema client](schema-client.md) |
| Manage secrets and integrations | `SecretClient` / `IntegrationClient` | [security](security.md) |
| Compile, deploy, run, signal agents | `AgentClient` / `AgentRuntime` | [agent control plane](agents/reference/client.md) |

Python does not currently expose a public workflow-scoped `FileClient`; use the
server and task capabilities appropriate to your deployment instead.
