# Compatibility matrix

| Area | Supported baseline | Notes |
|---|---|---|
| Python SDK | Python 3.10+ | Defined by `pyproject.toml`. |
| OSS Conductor | Supported server deployment | Test the target server during upgrades. |
| Orkes | Supported tenant API | Enterprise features depend on tenant permissions. |
| Conductor agents | Server agent runtime and provider integration | Provider credentials live on the server. |

The Python SDK does not currently provide Java's `FileClient` or Spring Boot
modules. This documentation does not present either as available Python support.

## Workflow-scoped files

The Python SDK does not currently expose a public workflow-scoped `FileClient`.
Use task-appropriate object storage or a server capability selected by your
deployment; do not copy Java `FileClient` examples into Python applications.

## Spring framework integration

Spring and Spring Boot modules are Java-specific. Host Python workers and
Conductor-agent services in the application framework your deployment uses; see
the [FastAPI worker example](../examples/fastapi_worker_service.py) and
[deployment/scaling](deployment-scaling.md).
