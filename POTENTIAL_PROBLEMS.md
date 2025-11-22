# Potential Problems in Async Implementation

This document outlines the potential problems identified in the current asynchronous implementation of the Python SDK.

## 1. Fake Asynchronous Operations using `threading.Thread`

The current implementation of asynchronous operations is based on wrapping blocking calls in a separate thread (`AwaitableThread`). This is not a true asynchronous implementation and has several drawbacks:

*   **Resource Intensive**: Creating a new thread for each request is resource-intensive and does not scale well. Each thread consumes memory and CPU resources, and a large number of threads can lead to performance degradation.
*   **No I/O Concurrency**: The underlying I/O operations are still blocking. This means that the thread is blocked waiting for the I/O operation to complete, and it is not possible to achieve true I/O concurrency.
*   **Incompatible with `asyncio`**: The current implementation is not compatible with the `asyncio` ecosystem. This means that it is not possible to use the SDK with other `asyncio`-based libraries and frameworks, such as `aiohttp`, `fastapi`, etc.

## 2. Lack of aiohttp Client Session

The current implementation does not use an `aiohttp.ClientSession`. A `ClientSession` is a key component of `aiohttp` that allows for connection pooling and other performance optimizations. By not using a `ClientSession`, the SDK is not taking advantage of these performance benefits.

## 3. Inconsistent Naming Conventions

The current implementation uses inconsistent naming conventions for asynchronous methods. For example, the `call_api` method has an `async_req` parameter that is used to enable asynchronous operations. This is not a standard way of defining asynchronous methods in Python.
