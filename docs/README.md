# Python SDK documentation

Build durable workflow workers and Conductor agents with Python. These guides
cover OSS and Orkes; pages call out capabilities that require Orkes.

## Start here

| Goal | Guide | Expected result |
|---|---|---|
| Connect to a server | [Server setup](server-setup.md) and [connection/authentication](connection-authentication.md) | The SDK can reach an OSS or Orkes API endpoint. |
| Build a workflow and worker | [Core quickstart](core-quickstart.md) | The hello-world workflow prints its result. |
| Build a Conductor agent | [Agent quickstart](agents/getting-started.md) | An LLM-backed agent completes through Conductor. |

## Build

- [Workflows](workflows.md), [workflow lifecycle](workflow-lifecycle.md), and [workers](workers.md)
- [Workflow testing](workflow-testing.md), [schemas](schema-client.md), and [schedules/events](schedules-events.md)
- [Conductor agents](agents/README.md), [tools](agents/concepts/tools.md), and [framework bridges](agents/README.md#framework-bridges)
- [Recommended examples](examples.md); [examples/README.md](../examples/README.md) is the full catalog.

## Operate

- [Reliability](reliability.md), [security](security.md), and [deployment/scaling](deployment-scaling.md)
- [Metrics and logging](observability.md) and [debugging](debugging.md)

## Reference and upgrades

- [Core API map](api-map.md), [compatibility](compatibility.md), and [upgrading](upgrading.md)
- [Agent runtime](agents/reference/runtime.md), [control plane](agents/reference/client.md), and [agent definition](agents/reference/agent-definition.md)
- [Java/Python documentation parity](documentation-parity.md) — intentional Python mappings and unsupported Java-only surfaces.

## Documentation conventions

Primary guides follow the [documentation standard](documentation-standard.md).
Provider credentials belong on the Conductor server or its secret provider, not
in workflow input, example source, or a client-side `.env` committed to Git.
