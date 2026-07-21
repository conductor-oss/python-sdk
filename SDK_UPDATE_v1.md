# SDK Update v1 — Agent Layer: Components, Method Contracts, and Bug Fixes

**Source:** Python SDK branch `feat/agent-client-worker-credentials` (PR conductor-oss/python-sdk#421)
**Audience:** Developers and coding agents updating the **Java / Go / C# / JavaScript-TypeScript** Conductor SDKs.
**Purpose:** A single reference describing (1) how the agent-layer components are designed and used — `ApiClient`, `AgentClient`, `AgentRuntime`, `AgentConfig`, `RunSettings` — (2) the exact contracts of `run` / `start` / `deploy` / `serve`, and (3) **every bug fix** on this branch, with root cause and port guidance.

> Companion document: `docs/design/AGENT_SDK_PORTING_SPEC.md` — the same changes expressed as numbered requirements (R1–R13) with acceptance criteria and a test matrix. Use *this* document to understand the design and the fixes; use the spec to drive implementation.

Code snippets below are the Python reference implementation; port the contracts, not the syntax.

---

## Part 1 — Components

### 1.1 `ApiClient` — the single token authority

The `ApiClient` (and its async twin) is the **only** component in the SDK that performs authentication. Everything else — generated resource APIs, domain clients, the agent control plane, and worker-side HTTP — reuses it.

**What it owns:**

| Capability | Behavior |
|---|---|
| Token mint | `POST {host}/token` with `{"keyId": …, "keySecret": …}` → `{"token": "<jwt>"}` |
| Token cache | Token + mint timestamp held on the `Configuration`; shared by every client built from it |
| TTL refresh | Before injecting the header, if the token is older than the TTL, re-mint proactively |
| 401 retry | Any `call_api` that fails with an auth error force-refreshes the token and retries exactly once |
| Header | `X-Authorization: <jwt>` on every request (except `/token` itself); no header for anonymous servers |
| Open-server detection | A 404 from `/token` = auth-disabled server → operate anonymously |

**Generic call surface** — arbitrary endpoints (used by the agent layer for `/agent/*`):

```python
api_client.call_api(
    "/agent/start", "POST",          # resource path is relative to Configuration.host,
    {}, [], headers,                 #   which already ends in /api
    body=payload,
    response_type="object",          # None => fire-and-forget (executes, returns None)
    auth_settings=["api_key"],
    _return_http_data_only=True,
)
```

**New in this branch — public auth-header accessor** (for transports that cannot go through `call_api`, e.g. SSE):

```python
api_client.get_authentication_headers()
# -> {"header": {"X-Authorization": "<jwt>"}} or None (anonymous)
# TTL-aware: renews the token if expired before returning.
```

**Rule for all SDKs:** never mint or cache a token anywhere else. If a component needs auth, give it an `ApiClient` (or this accessor). See bug fixes #3 and #12.

---

### 1.2 `AgentClient` — the agent control plane

A new **domain client** following the SDK's established interface + Orkes-implementation pattern (like `WorkflowClient` / `OrkesWorkflowClient`).

```
AgentClient (interface)  ←implements—  OrkesAgentClient (built on OrkesBaseClient + ApiClient)
                                          └── created via OrkesClients.get_agent_client()
```

**Methods** (each has a sync and an `*_async` variant):

| Method | HTTP | Notes |
|---|---|---|
| `start_agent(payload)` | `POST /agent/start` | Server compiles + registers + starts in one call; returns `{executionId, requiredWorkers?}` |
| `deploy_agent(payload)` | `POST /agent/deploy` | Register only; returns `{agentName}` |
| `compile_agent(payload)` | `POST /agent/compile` | Returns the compiled workflow definition |
| `get_status(execution_id)` | `GET /agent/{id}/status` | |
| `get_execution(execution_id)` | `GET /agent/execution/{id}` | |
| `list_executions(params?)` | `GET /agent/executions` | Query params |
| `respond(execution_id, body)` | `POST /agent/{id}/respond` | Human-in-the-loop answer |
| `stop(execution_id)` | `POST /agent/{id}/stop` | Graceful stop |
| `signal(execution_id, message)` | `POST /agent/{id}/signal` | Inject persistent context |
| `stream_sse(execution_id, last_event_id?)` | `GET /agent/stream/{id}` | SSE event generator |
| `close()` | — | Release async transports |

**Implementation rules:**
- All non-streaming methods delegate to `api_client.call_api(...)` → token management inherited, zero token code in this class.
- **SSE** uses a streaming HTTP transport but sets its auth header from `api_client.get_authentication_headers()` on every (re)connect. Sends `Accept: text/event-stream` and `Last-Event-ID` on reconnect. Raises `SSEUnavailableError` when the server has no streaming (callers fall back to status polling).
- **Error mapping:** transport `ApiException` → `AgentNotFoundError` (404) / `AgentAPIError` (everything else), both carrying status, body, url.

**Usage:**

```python
clients = OrkesClients(configuration=Configuration())
agent_client = clients.get_agent_client()
data = agent_client.start_agent({"agentConfig": cfg, "prompt": "hi", "sessionId": "", "media": []})
```

---

### 1.3 `AgentRuntime` — the facade

The single user-facing entry point for authoring-and-running agents.

**Constructor contract:**

```python
AgentRuntime(configuration: Optional[Configuration] = None, *, settings: Optional[AgentConfig] = None)
```

- `configuration` — the standard SDK `Configuration`; **sole source** of host, auth, and log level. Defaults to env-resolved `Configuration()`.
- `settings` — optional `AgentConfig` (behaviour knobs only, §1.4). Defaults to `AgentConfig.from_env()`.

**Composition** (all built from ONE `OrkesClients(configuration)`, hence one token cache):

```
AgentRuntime
 ├── _agent_client   = clients.get_agent_client()      # control plane (§1.2); exposed as runtime.client
 ├── _workflow_client / _task_client                   # status polling, HITL updates, messaging
 └── _worker_manager = WorkerManager(configuration, …) # wraps TaskHandler/TaskRunner; serves tool workers
```

- Context manager, sync and async (`with` / `async with`).
- Every `/agent/*` operation goes through `_agent_client`. The runtime holds **no** URL builders, HTTP transports, or token helpers of its own.
- There is **no server auto-start**: the runtime never probes for or launches a server (removed on this branch; a missing server surfaces as a connection error).

**Execution model:** an agent is authored locally but **compiled and executed on the server** as a Conductor workflow. The agent's tools are ordinary Conductor **workers** served by the runtime's `WorkerManager` — the standard poll/execute/update loop, unchanged.

---

### 1.4 `AgentConfig` — agent-runtime behaviour ONLY

Reduced on this branch to behaviour knobs. **Connection, auth, and log level are NOT here** — they live on `Configuration` (see bug fix #8).

| Field | Type | Default | Env var |
|---|---|---|---|
| `worker_poll_interval_ms` | int | 100 | `AGENTSPAN_WORKER_POLL_INTERVAL` |
| `worker_thread_count` | int | 1 | `AGENTSPAN_WORKER_THREADS` |
| `auto_start_workers` | bool | true | `AGENTSPAN_AUTO_START_WORKERS` |
| `daemon_workers` | bool | true | `AGENTSPAN_DAEMON_WORKERS` |
| `auto_register_integrations` | bool | false | `AGENTSPAN_INTEGRATIONS_AUTO_REGISTER` |
| `streaming_enabled` | bool | true | `AGENTSPAN_STREAMING_ENABLED` |
| `liveness_enabled` | bool | true | `AGENTSPAN_LIVENESS_ENABLED` |
| `liveness_stall_seconds` | float | 30.0 | `AGENTSPAN_LIVENESS_STALL_SECONDS` |
| `liveness_check_interval_seconds` | float | 10.0 | `AGENTSPAN_LIVENESS_CHECK_INTERVAL_SECONDS` |

**Removed fields** (do not port): `server_url`, `api_key`, `auth_key`, `auth_secret` (+ `api_secret` alias), `llm_retry_count` (dead — never read), `secret_strict_mode` (dead — fail-closed credentials are unconditional), `log_level` (moved to `Configuration`), `auto_start_server`.

**`Configuration` env resolution** (for reference — this is where connection/auth/log level live):
- Host: `CONDUCTOR_SERVER_URL` → `AGENTSPAN_SERVER_URL` → `http://localhost:8080/api`
- Auth: `CONDUCTOR_AUTH_KEY` / `CONDUCTOR_AUTH_SECRET`
- Log level: explicit param → `CONDUCTOR_LOG_LEVEL` → `AGENTSPAN_LOG_LEVEL` → derived from `debug`

---

### 1.5 `RunSettings` — per-run LLM overrides

New on this branch. Lets one invocation override the LLM settings baked into an `Agent`, without constructing a new agent.

```python
from conductor.ai.agents import RunSettings

result = runtime.run(
    agent, "Summarize this.",
    run_settings=RunSettings(model="anthropic/claude-sonnet-4-6", temperature=0.0, max_tokens=512),
)
```

| Field | Overrides `agentConfig` wire key |
|---|---|
| `model` | `model` |
| `temperature` | `temperature` |
| `max_tokens` | `maxTokens` |
| `reasoning_effort` | `reasoningEffort` |
| `thinking_budget_tokens` | `thinkingConfig = {"enabled": true, "budgetTokens": n}` |

**Semantics (all MUST hold in every SDK):**
- Applied to the **serialized root `agentConfig`** after serialization, immediately before `start_agent` — pure SDK-side payload mutation; no new server field. Because start = compile+register+start atomically, the override flows into the compiled LLM tasks.
- **Null-check, not truthiness**: only fields that are *set* override — `temperature=0.0` and `max_tokens=0` are valid overrides and must apply.
- Root-only: sub-agents keep their own per-agent settings (no cascade).
- Accepted by `run`, `start`, and their async variants (and module-level convenience wrappers). A plain map with the same keys is also accepted; unknown keys are an error.
- `top_p` is deliberately absent — it does not exist in the agentConfig contract.

---

## Part 2 — Method contracts

The exact semantics of the runtime verbs. Implementations must match this table:

| Method | Blocks | Returns | Starts tool workers | Registers agent on server | Executes |
|---|---|---|---|---|---|
| `run(agent, prompt, …)` | yes — polls to completion | **result object** (`output`, `status`, ids, token usage) | **yes** | via start (one server call compiles + registers + starts) | yes |
| `start(agent, prompt, …)` | no | **handle object** (`execution_id`, `join()`, `stop()`, `stream()`) | **yes** | via start | yes |
| `deploy(*agents, packages=?, schedules=?)` | yes | list of deployment info | **no** | **yes** — `POST /agent/deploy` per agent | no |
| `serve(*agents, packages=?, blocking=true)` | yes, until SIGINT/SIGTERM (`blocking=false` returns) | void | **yes** — registers + polls | **yes** — deploys each agent first (`serve` = `deploy` + serve) | no |
| `plan(agent)` | yes | compiled workflow def | no | no | no |
| `stream(agent, prompt, …)` | iterates | event stream | yes | via start | yes |

### `run` — start, wait, return the result
`run(agent, prompt, *, version?, media?, session_id?, idempotency_key?, on_event?, timeout?, credentials?, context?, run_settings?) -> AgentResult`
Serializes the agent (+ `run_settings` overrides), calls `start_agent`, starts the required tool workers, then polls status to a terminal state. Returns the rich result — the output is `result.output`, **not** a bare value. Credential names configure worker `TaskDef.runtimeMetadata` locally and are not sent as workflow input.

### `start` — fire-and-forget
`start(agent, prompt, *, version?, media?, session_id?, idempotency_key?, context?, run_settings?) -> AgentHandle`
Same start flow, but returns immediately with a handle: `handle.execution_id`, `handle.join(timeout)`, `handle.stop()`, streaming, HITL helpers. Also starts the tool workers (scheduled tool tasks must have someone to execute them). The first argument accepts an `Agent` object **or** an agent name string (with optional `version=`) for pre-deployed agents.

### `deploy` — CI/CD registration, nothing runs
`deploy(*agents, packages=None, schedules=UNSET) -> list[DeploymentInfo]`
For each agent (passed directly or discovered from `packages`), detect the framework and call `deploy_agent` — the server compiles and registers the workflow + task definitions. **No local workers are registered or started, nothing executes.** Optional `schedules=` reconciles cron schedules for a single agent.

### `serve` — register the agent AND serve its workers
`serve(*agents, packages=None, blocking=True) -> None`
Per agent: (1) **deploy it to the server** (same helper `deploy` uses — new on this branch, see bug fix #7), (2) register its local tool workers (task defs registered with overwrite semantics — idempotent with step 1), then start the worker manager polling. With `blocking=True`, installs SIGINT/SIGTERM handlers and blocks until interrupted; `blocking=False` returns after startup (embedding, tests).

### Shared start flow (pseudocode)

```
config_json = serialize(agent)
if run_settings: config_json.update(run_settings.to_config_overrides())
payload = {agentConfig: config_json, prompt, sessionId: session_id ?? "", media: media ?? []}
+ optional keys only when set: context, idempotencyKey, timeoutSeconds, runId, static_plan
data = agent_client.start_agent(payload)
execution_id, required_workers = data.executionId, data.requiredWorkers?
prepare_workers(agent, required_workers)     # WorkerManager start — serve the tools
```

---

## Part 3 — Bug fixes on this branch (complete list)

Each fix lists symptom → root cause → fix → **Port** (what other SDKs must do).

### SDK bugs

**#1 — Worker credentials failed on secured hosts (`Required credentials not found: GH_TOKEN. No execution token available`)**
*Cause:* two-fold. The credentials fetcher authenticated with `Authorization: Bearer <keyId>` — sending the raw key id as if it were a token instead of minting a JWT for `X-Authorization`. And the whole delivery design depended on a per-execution token + `POST /workers/secrets` fetch that stateless tool workers often didn't have.
*Fix:* the delivery contract was replaced entirely (see #2). The interim header fix (mint via `POST /token`, send `X-Authorization`) applies to any custom transport an SDK still has.
*Port:* never send key ids as bearer tokens; all auth goes through the ApiClient contract (§1.1).

**#2 — Credential delivery redesigned: `runtimeMetadata` (fail-closed)**
*Cause:* the execution-token/`/workers/secrets` path was racy, added a second auth path, and broke for stateless workers.
*Fix:* new wire contract. `TaskDef.runtimeMetadata: string[]` declares the secret **names** a task type needs — the SDK stamps it at tool registration, and because worker registration uses overwrite semantics, it **re-stamps on every registration** (a sub-bug here: a plain re-register used to wipe the server-side value). At poll time the server resolves the names and delivers the **values** on the wire-only `Task.runtimeMetadata: map<string,string>` (never persisted). The worker injects them for that call only and **fails** (`CredentialNotFoundError`) if a declared name wasn't delivered — it never falls back to the ambient process environment.
*Port:* add both model fields (JSON name `runtimeMetadata`), stamp on registration, resolve fail-closed at dispatch, delete the fetcher. Requires a server that persists/delivers runtimeMetadata (conductor-oss PR #1255); capability-probe in integration tests.

**#3 — Parallel token cache in framework workers**
*Symptom:* worker processes held **two token authorities** — `ApiClient`'s and a standalone `token_utils` mint/cache used by raw `requests.post` calls to `/agent/*` (event push, tracking workflows, task injection/completion) — with separate TTL/refresh behavior.
*Fix:* new internal `agent_http` helper: an `ApiClient` **cached per `(server_url, auth_key)`**, reconstructed inside the worker process from plain strings (the constructor mints a token, so caching is mandatory), and `agent_post(path, body, read_response)` on `call_api`. Fire-and-forget callers swallow errors (return null); readers get the parsed object or null. Task-progress updates moved from raw `requests` to the native task client (`update_task`, `IN_PROGRESS`) on the **same** cached client. The standalone mint/cache was deleted (only a JWT-`exp` decoder remains).
*Port:* one `POST /token` code path in the whole SDK. Worker-side posts go through a cached authenticated client.

**#4 — CLI tools worker was not spawn-safe (`SpawnSafetyError: worker 'run_command' is not spawn-safe`)**
*Cause:* the auto-generated `run_command` tool was a `<locals>` closure; spawned worker processes cannot import it.
*Fix:* a module-level callable class (`_CliCommandRunner`) holding plain config (allowed commands, timeout, cwd) — pickles by value.
*Port:* any auto-generated worker must be a top-level callable/class, never a closure.

**#5 — `GPTAssistantAgent` was not spawn-safe**
*Cause:* its `call_assistant` tool was a closure over `self` inside `__init__`.
*Fix:* module-level `_AssistantCall` callable class with plain-data fields (assistant id, api key, model, instructions); the agent method delegates to it.
*Port:* same invariant as #4 for any built-in agent types.

**#6 — `AttributeError: 'AgentConfig' object has no attribute 'liveness_stall_seconds'`**
*Cause:* the result/handle code started a `ServerLivenessMonitor` for stateful runs and read three `AgentConfig` fields that were never defined.
*Fix:* added `liveness_enabled` / `liveness_stall_seconds` (30.0) / `liveness_check_interval_seconds` (10.0) with env parsing. The monitor polls the workflow; if a task has had **no polls** for the stall window (worker died), blocking `join()`/`result()` raise `WorkerStallError` instead of hanging forever.
*Port:* implement the liveness monitor + config fields together; never ship a reader without its config.

**#7 — `serve` did not register the agent on the server**
*Symptom:* `serve` only registered local worker task defs and polled; the agent's workflow definition was never registered, so `serve` alone couldn't make an agent runnable — users had to know to call `deploy` first.
*Fix:* `serve` now deploys each agent (same internal helper as `deploy`) before registering/starting its workers — `serve` = `deploy` + serve. Idempotent with overwrite task-def registration; same ordering `run` already used.
*Port:* add the deploy step at the top of serve's per-agent loop, covering native and framework agents.

**#8 — `AgentConfig` duplicated connection/auth/log settings (two sources of truth)**
*Symptom:* `AgentConfig.server_url/auth_key/auth_secret/api_key` could disagree with `Configuration`; `llm_retry_count` and `secret_strict_mode` were **dead** (documented behavior that didn't exist — `secret_strict_mode` claimed to control an env fallback that the fail-closed resolver never had).
*Fix:* removed all of them (§1.4). Connection/auth from `Configuration` only; `configure()` convenience now takes a `Configuration` for connection.
*Port:* keep agent settings behaviour-only; delete dead flags rather than documenting them.

**#9 — Log level only applied to some loggers, configured in the wrong place**
*Cause:* `AgentConfig.log_level` was applied to the agent loggers only; the rest of the SDK had a separate debug-derived level on `Configuration`.
*Fix:* `Configuration` gained a settable `log_level` (param + `CONDUCTOR_LOG_LEVEL` → `AGENTSPAN_LOG_LEVEL` env); the agent runtime reads it from there. One SDK-wide setting.
*Port:* single log-level knob on the configuration object.

**#10 — Agent server auto-start removed**
*Symptom:* the SDK probed whether an agent server was running and could launch one — masking misconfiguration, surprising in CI, and coupling the SDK to a server distribution.
*Fix:* all detection/launch logic deleted (`runtime/server.py`, `auto_start_server` flag, `AGENTSPAN_AUTO_START_SERVER` env). A missing server is a connection error.
*Port:* do not auto-start servers from the SDK.

**#11 — Swarm transfers: multiple transfer calls silently dropped; hand-off message lost**
*Symptom:* when the LLM emitted multiple `*_transfer_to_*` calls in one turn, only the first mattered and the rest vanished with no trace; the transfer tool's `message` argument (the hand-off note for the receiving agent) was discarded.
*Fix:* `check_transfer` is now explicitly **first-wins**: it returns `{is_transfer, transfer_to, transfer_message}` and, when extra transfers were emitted, logs a warning and surfaces them as `dropped_transfers` in the task output. The transfer no-op tool now accepts and echoes `message` (schema includes `message: str`), and the server records the hand-off as `[agent -> target]: <message>` in the conversation.
*Port:* transfer detection must carry the message and make dropped transfers visible — never silently discard model intent.

**#12 — SSE streaming minted its own token**
*Cause:* the old streaming transport (and the bespoke `AgentApiClient`) had independent JWT minting.
*Fix:* superseded by `OrkesAgentClient.stream_sse`, which borrows the header from `api_client.get_authentication_headers()` per (re)connect (new public accessor — §1.1).
*Port:* streaming reuses the client token; add the accessor.

### Deleted components (consequence of the fixes)

| Deleted | Replaced by |
|---|---|
| `client/ai/agent_api_client.py` (bespoke transport, own JWT) | `OrkesAgentClient` on `ApiClient` |
| `runtime/http_client.py` (DX wrapper client) | `runtime.client` → `AgentClient` |
| `runtime/credentials/fetcher.py` (execution-token fetch) | `runtimeMetadata` contract (#2) |
| `runtime/server.py` (server auto-start) | — (#10) |
| `token_utils` mint/cache | `agent_http` on cached `ApiClient` (#3) |

### Example-level fixes (Python-specific, but the invariants generalize)

- **Missing main-module guards** (`75/76/82/83/84_*.py`): stateful examples ran orchestration at module top level; spawned worker processes re-imported the module and re-ran it (multiprocessing "safe importing of main module" error / hangs). Fixed with `if __name__ == "__main__":` guards. *Invariant: entry scripts must be safely re-importable wherever workers are separate processes.*
- **Spawn-unsafe example workers** (`82`, `92`, `16g`): tools defined as closures over the runtime or inside factory functions → hoisted to module level; `82` also moved to an **env-var-shared IPC directory** (a per-import temp dir gave every spawned worker a different directory) and rebuilds its workflow client inside the worker from `Configuration()`.
- **Missing `import sys`** (`72`, `73`): `NameError` at entry.
- **Hardcoded server URLs** (`hello_world_schedule*, settings`): now env-resolved (`CONDUCTOR_SERVER_URL` → `AGENTSPAN_SERVER_URL`).
- **Unavailable model id** (`58_scatter_gather`): hardcoded model replaced with the shared settings default.

### Test/e2e hardening (port the patterns)

- **Capability probe:** credential e2e tests probe whether the server persists `TaskDef.runtimeMetadata` and skip when it doesn't (older servers) — instead of failing.
- **Determinism:** credential suites use a per-test (function-scoped) runtime so worker task defs are re-registered per test — a cached module-scoped runtime masked registration regressions (verified by mutation testing).
- **Env isolation:** tests that assert "no auth configured" clear ambient `CONDUCTOR_AUTH_*` env vars (CI sets them).
- **Client-layer tests without mocks:** `AgentClient`/`agent_http` tests run against an in-process HTTP server counting `/token` mints and capturing headers — the mint-once assertion is the guard against reintroducing per-call minting.

---

## Porting order

1. `ApiClient` accessor + `Configuration` env/log changes (§1.1, #9)
2. `AgentClient` + factory; `AgentRuntime` on it; delete bespoke transports + auto-start (§1.2–1.3, #10, #12)
3. Credentials via `runtimeMetadata` (#1, #2)
4. Worker-side single token authority (#3)
5. `RunSettings` + verb contract incl. `serve` = deploy + serve (§1.5, Part 2, #7)
6. Spawn-safety/registration invariants, liveness, swarm transfer fixes (#4–#6, #11)
7. Deletion sweep + test patterns (tables above)

Definition of done and per-requirement acceptance criteria: see `docs/design/AGENT_SDK_PORTING_SPEC.md`.
