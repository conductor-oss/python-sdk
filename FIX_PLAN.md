# Plan to Fix Async Implementation

This document outlines the plan to fix the asynchronous implementation of the Python SDK.

## 1. Introduce `anyio` and `httpx` for True, Backend-Agnostic Asynchronous HTTP Requests

The primary focus of this plan is to replace the current thread-based asynchronous implementation with a true asynchronous implementation that is not tied to a specific backend like `asyncio`. We will use `anyio` to provide backend-agnostic asynchronous operations and `httpx` for asynchronous HTTP requests, as it integrates seamlessly with `anyio`.

This will involve the following steps:

*   **Add `anyio` and `httpx` as dependencies**: Add `anyio` and `httpx` to the `pyproject.toml` file. `httpx` will replace `requests` for async operations.
*   **Create an `AsyncApiClient`**: Create/update the `AsyncApiClient` class to use an `httpx.AsyncClient` for making asynchronous HTTP requests. This client will be managed by `anyio`.
*   **Implement `async` methods**: All methods in `AsyncApiClient` that make HTTP requests will be `async` methods.
*   **Deprecate `AwaitableThread`**: The `AwaitableThread` class will be deprecated and removed from the codebase.
*   **Remove `BackgroundEventLoop`**: The custom `BackgroundEventLoop` will be removed in favor of `anyio`'s native capabilities for running async code from synchronous contexts.
*   **Add new tests and fix existing tests**: Add new tests accordingly and update existing tests

## 2. Refactor Existing Code to Use `AsyncApiClient`

Once the `AsyncApiClient` is implemented, the existing code will be refactored to use it. This will involve the following steps:

*   **Update `ApiClient`**: The `ApiClient` class will be updated to use the `AsyncApiClient` for asynchronous requests.
*   **Update `Configuration`**: The `Configuration` class will be updated to support the `AsyncApiClient`.
*   **Update method signatures**: The method signatures of the API clients will be updated to be `async` methods.
*   **Refactor the Worker**:
    *   Create a `base_worker.py` with a `BaseWorker` class containing common worker logic.
    *   update the existing `worker.py` to act as a sync that inherits from `BaseWorker` and implements the synchronous `execute` method.
    *   Create `async_worker.py` with an `AsyncWorker` that inherits from `BaseWorker` and implements the asynchronous `async_execute` method using `anyio` to run tasks.

## 3. Improve Naming Conventions

The naming conventions for asynchronous methods will be improved to be more consistent with the Python ecosystem. This will involve the following steps:

*   **Use `async` keyword**: All asynchronous methods will be defined with the `async` keyword.
*   **Use `await` keyword**: All calls to asynchronous methods will be made with the `await` keyword.
*   **Remove `async_req` parameter**: The `async_req` parameter will be removed from the method signatures.

## 4. Ensure Backward Compatibility

To ensure backward compatibility, the existing synchronous implementation will be preserved.
*   The `ApiClient` will continue to support synchronous requests.
*   The `async_req` parameter will be deprecated but not removed immediately. A warning will be issued when the `async_req` parameter is used, and it will be removed in a future release.
*   The existing `worker.py` will continue to expose as a `Worker` class for backward compatibility
