# Deployment, scaling, and graceful shutdown

Run workers and `AgentRuntime.serve()` processes as long-lived services. Scale by
adding worker instances and use task domains or queue limits to isolate workloads.
On shutdown, stop task handlers and runtimes so in-flight tasks can be redelivered
instead of being abandoned.

Do not construct a new runtime per web request. Reuse clients and runtimes for the
application lifetime; use [reliability](reliability.md) for timeout and retry policy.
