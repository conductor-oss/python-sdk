# Java/Python documentation parity

The Python SDK follows the same documentation information architecture as the
Java SDK while mapping instructions to the Python public API. This page makes the
intentional differences explicit so a missing page is not mistaken for support.

| Java documentation capability | Python documentation counterpart | Status |
|---|---|---|
| Server, connection, quickstart, workflows, workers, lifecycle, testing | [Core guides](README.md#build) | Supported with Python APIs |
| Schema client, schedules/events, reliability, security, deployment, observability, debugging | [Operations guides](README.md#operate) | Supported where the target server exposes the capability |
| Agent concepts, runtime, API/client, definition contract | [Conductor agent guide](agents/README.md) | Supported with Python APIs |
| Google ADK and framework bridges | [Framework bridges](agents/README.md#framework-bridges) | Python includes Google ADK, LangChain, LangGraph, OpenAI Agents, and Claude Agent SDK bridges |
| Workflow-scoped FileClient | [Compatibility](compatibility.md#workflow-scoped-files) | Not currently exposed as a public Python client |
| Spring and Spring Boot integration | [Compatibility](compatibility.md#spring-framework-integration) | Java-specific; use Python application hosting patterns instead |

## Maintenance rule

When adding a Java-style guide or a Python capability, update this map and the
documentation hub in the same change. Do not claim a Java-only client or framework
feature is available in Python.
