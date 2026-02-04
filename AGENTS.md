# AI Agent Guide for Conductor Python SDK

This document provides context and instructions for AI agents working on the `conductor-python` repository.

## 1. Project Overview

The **Conductor Python SDK** allows Python applications to interact with [Netflix Conductor](https://conductor.netflix.com/) and [Orkes Conductor](https://orkes.io/). It enables developers to:
1.  **Create Workers**: Poll for tasks and execute business logic.
2.  **Manage Workflows**: Start, stop, pause, and query workflows.
3.  **Manage Metadata**: Register task and workflow definitions.

## 2. Repository Structure

| Directory | Description |
|-----------|-------------|
| `src/conductor/client` | Core SDK source code. |
| `src/conductor/client/automator` | **Worker Framework**: `TaskRunner`, `AsyncTaskRunner`, `TaskHandler`. |
| `src/conductor/client/http` | **API Layer**: Low-level HTTP clients (OpenAPI generated). |
| `src/conductor/client/worker` | **Worker Interfaces**: `@worker_task` decorator, `WorkerInterface`. |
| `src/conductor/client/configuration` | **Configuration**: Settings, Auth, multi-homed logic. |
| `tests/unit` | Unit tests (fast, mocked). |
| `tests/integration` | Integration tests (require running Conductor server). |
| `examples/` | usage examples for users. |

## 3. Key Components & Architecture

### 3.1 Worker Framework (`automator/`)

The worker framework is the most complex part of the SDK. It handles the "polling loop" pattern.

*   **`TaskHandler`**: Entry point. Manages `TaskRunner` instances. Auto-detects configuration.
*   **`TaskRunner` (Sync)**:
    *   Uses `ThreadPoolExecutor` for concurrent task execution.
    *   Supports **Multi-Homed Polling** (polling multiple servers in parallel).
    *   **Crucial Logic**: `__batch_poll_tasks` handles the poll loop, circuit breakers, and timeouts.
*   **`AsyncTaskRunner` (Async)**:
    *   Uses `asyncio` event loop.
    *   Optimized for high-concurrency I/O bound tasks.
    *   Also supports multi-homed polling.

### 3.2 Configuration (`configuration/`)

The `Configuration` class manages server connection details.
*   **Factory Method**: `Configuration.from_env_multi()` allows creating multiple config objects from comma-separated env vars (`CONDUCTOR_SERVER_URL`).
*   **Authentication**: Handled via `AuthenticationSettings` (key/secret).

### 3.3 Multi-Homed Workers (Feature Highlight)

Refactored in Jan 2026 to support High Availability.
*   **Concept**: Workers poll from N servers.
*   **Implementation**:
    *   `_poll_executor`: Dedicated thread pool for polling (TaskRunner).
    *   `_server_map`: Internal map `{task_id: server_index}` to route updates back to the correct server.
    *   **Resilience**: Circuit Breaker (skips down servers for 30s) and Poll Timeout (5s).

## 4. Development Guidelines

### 4.1 Running Tests

*   **Unit Tests**: Run with `pytest`.
    ```bash
    PYTHONPATH=src pytest tests/unit
    ```
*   **Key Test Files**:
    *   `tests/unit/automator/test_multi_homed.py`: Validates multi-server logic and circuit breakers.
    *   `tests/unit/automator/test_task_runner.py`: Validates core runner logic.

### 4.2 Logging

*   Use `logging.getLogger(__name__)`.
*   The SDK has extensive logging for debugging polling issues.

### 4.3 Code Style

*   Follow PEP 8.
*   Type hints are strongly encouraged (`def foo(bar: str) -> int:`).
*   Use `logger.debug` for high-volume logs (like polling loops).

## 5. Common Tasks

### Adding a New API Method
1.  Check `src/conductor/client/http/api` (Generated code). Do NOT edit manually if possible.
2.  Add high-level method to `OrkesTaskClient` or `OrkesWorkflowClient`.

### Debugging Worker Issues
1.  Check `TaskRunner.run()` loop.
2.  Verify `_task_server_map` logic if updates fail.
3.  Check `_auth_failures` and circuit breaker state if polling stops.

## 6. Artifacts
*   **`AGENTS.md`**: This file.
*   **`SDK_IMPLEMENTATION_GUIDE.md`**: General architecture guide for *all* language SDKs (formerly AGENTS.md).
