# Agent SDK Porting Spec — Parity with Python SDK PR #421

**Version:** 1.1
**Audience:** Coding agents (Claude, GPT, …) and SDK developers working in the
Conductor **Java / Go / C# / JavaScript-TypeScript** SDK repositories.
**Scope:** The delta required to bring an SDK's *agent layer* to parity with the
Python SDK after PR `conductor-oss/python-sdk#421` (branch
`feat/agent-client-worker-credentials`).
**Self-contained:** Every contract needed (endpoints, wire keys, semantics,
acceptance criteria) is stated in this document. You do not need access to the
Python repository.

---

## How to use this spec

1. Implement the numbered requirements **in the order given in §5** (they are
   dependency-ordered). Keep your language's idioms — port the *contracts*, not
   Python syntax.
2. Every requirement (R1–R12) ends with **acceptance criteria**. A requirement is
   done only when all its criteria hold and are covered by tests.
3. If your SDK does not yet have an agent layer at all, R1–R3 still apply to the
   core client (they are prerequisites), and the rest defines the agent layer you
   will build.
4. MUST / MUST NOT / SHOULD are used in the RFC-2119 sense.

### Design principles behind this delta

- **Single token authority.** Every HTTP call in the agent layer — control plane
  and worker-side — reuses the SDK's one authenticated API client (token
  mint / cache / TTL-refresh / 401-retry). No second token cache anywhere.
- **Interface + implementation client pattern.** The agent control plane is a
  first-class domain client, like Task/Workflow/Secret clients.
- **Configuration single-sourcing.** Server connection, auth, and log level live
  on the SDK `Configuration` only. Agent-runtime settings hold behaviour knobs
  only.
- **Fail-closed credentials.** Tool workers get secrets from the server on the
  wire, per task — never from the worker's ambient environment.

---

## 1. Summary of changes

| # | Change | Kind |
|---|--------|------|
| R1 | `AgentClient` interface + `OrkesAgentClient` implementation on the standard API client; `OrkesClients.getAgentClient()` factory | **Add** |
| R2 | Public, TTL-aware `getAuthenticationHeaders()` on the API client (sync + async) | **Add** |
| R3 | `Configuration`: host env fallback + settable SDK-wide log level | **Change** |
| R4 | `AgentConfig` reduced to agent-runtime behaviour only; liveness fields added | **Change** |
| R5 | `AgentRuntime` constructor contract; all `/agent/*` traffic via `AgentClient`; server auto-start removed | **Change** |
| R6 | Worker credential delivery via `runtimeMetadata` (TaskDef declares names; Task delivers values); execution-token path retired | **Change** |
| R7 | Worker-side agent posts routed through a cached API client (single token authority); parallel token cache deleted | **Change** |
| R8 | `RunSettings` — per-run LLM overrides on `run`/`start` | **Add** |
| R9 | Verb contract: `serve` = `deploy` + serve; exact run/start/deploy/serve/plan semantics | **Change** |
| R10 | Worker-callable registration safety (spawn-safety invariant) | **Change** |
| R11 | Liveness monitor for stateful runs | **Add** |
| R12 | Deletions: bespoke agent HTTP clients, credentials fetcher, server auto-start, parallel token mint/cache, dead config fields | **Remove** |
| R13 | Swarm transfer contract: `message` hand-off note on transfer tools; `check_transfer` first-wins with `transfer_message` + `dropped_transfers` | **Change** |

---

## 2. Requirements

### R1 — `AgentClient` interface + Orkes implementation

**Rationale:** The agent control plane (`/agent/*`) was previously reached through
bespoke HTTP transports with their own auth. It becomes a standard domain client:
an abstract interface plus a Conductor/Orkes implementation built on the SDK's
authenticated API client, wired into the client factory.

**Interface.** Define `AgentClient` (interface/ABC) with these operations, each in
a sync and an async variant (per your language's conventions — e.g. Go may expose
context-based methods only; C# `*Async`; TS Promise-based only):

| Method | HTTP call | Returns |
|---|---|---|
| `startAgent(payload)` | `POST /agent/start` | object (contains `executionId`, optional `requiredWorkers[]`) |
| `deployAgent(payload)` | `POST /agent/deploy` | object (contains `agentName`) |
| `compileAgent(payload)` | `POST /agent/compile` | object (compiled workflow def) |
| `getStatus(executionId)` | `GET /agent/{executionId}/status` | object |
| `getExecution(executionId)` | `GET /agent/execution/{executionId}` | object |
| `listExecutions(params?)` | `GET /agent/executions` (query params) | object |
| `respond(executionId, body)` | `POST /agent/{executionId}/respond` | void |
| `stop(executionId)` | `POST /agent/{executionId}/stop` | void |
| `signal(executionId, message)` | `POST /agent/{executionId}/signal` | void |
| `streamSse(executionId, lastEventId?)` | `GET /agent/stream/{executionId}` (SSE) | event iterator/stream |
| `close()` | — | release transports |

**Implementation (`OrkesAgentClient`):**
- MUST extend/compose the SDK's shared base client and route all non-streaming
  calls through the standard API client's generic call method (the same code path
  the generated resource APIs use). This inherits authentication header injection,
  token TTL refresh, and automatic one-shot retry on 401 **for free**. MUST NOT
  add any token logic of its own.
- Paths are relative to `Configuration.host`, which already ends in `/api` — so
  resource paths are `"/agent/..."` (leading slash, no `/api` prefix).
- **SSE** cannot go through the generic call method. Use a streaming HTTP
  transport, but obtain the auth header from the API client's public accessor
  (R2) per (re)connect. Send `Accept: text/event-stream` and, on reconnect,
  `Last-Event-ID: <id>`. Raise a dedicated `SSEUnavailableError` when the server
  does not support streaming (caller falls back to polling).
- **Error mapping:** catch the transport's `ApiException`; map HTTP 404 →
  `AgentNotFoundError`, everything else → `AgentAPIError` (both carrying status,
  body, url). Do not leak raw transport exceptions.
- **Factory:** add `getAgentClient(): AgentClient` to the SDK's `OrkesClients`
  factory, constructed from the same `Configuration` as every other client (hence
  the same token cache).

**Acceptance criteria**
- [ ] `OrkesClients.getAgentClient()` returns an `AgentClient` implementation.
- [ ] Every non-streaming call sends `X-Authorization: <jwt>` on a secured server
      and retries exactly once after a 401 (token force-refresh) — inherited, not
      re-implemented.
- [ ] SSE requests carry the same `X-Authorization` header sourced from the API
      client (verify no second `POST /token` occurs for streaming).
- [ ] 404 from any `/agent/*` call surfaces as `AgentNotFoundError`; 5xx as
      `AgentAPIError`.
- [ ] Interface-conformance test: the implementation satisfies the interface type.

---

### R2 — Public TTL-aware auth-header accessor on the API client

**Rationale:** Transports that bypass the generic call method (SSE, any custom
streaming) must reuse the API client's token rather than minting their own.

**Contract:** Add a public method on the API client (sync and async variants):

```
getAuthenticationHeaders() -> { "X-Authorization": <token> } | null
```

- Returns `null` for anonymous servers (no authentication settings).
- MUST be TTL-aware: if the cached token is older than the configured TTL, renew
  it (same `POST /token` mint the client already uses) before returning.
- It is a thin public wrapper over the client's existing private token machinery —
  do not duplicate mint/cache logic.

**Acceptance criteria**
- [ ] Two calls within TTL → one mint. A call after TTL expiry → re-mint.
- [ ] Anonymous configuration → returns null/empty, no mint attempted.

---

### R3 — `Configuration`: host fallback + SDK-wide log level

**Contract:**
1. **Host resolution order** (when not passed explicitly):
   `CONDUCTOR_SERVER_URL` → `AGENTSPAN_SERVER_URL` → default
   `http://localhost:8080/api`.
2. **Log level**: `Configuration` accepts an optional `logLevel` (level name or
   numeric level). Resolution order: explicit param → `CONDUCTOR_LOG_LEVEL` env →
   `AGENTSPAN_LOG_LEVEL` env → derived from the `debug` flag (DEBUG/INFO). This is
   the **only** log-level setting in the SDK; the agent runtime reads it from
   `Configuration` (see R4 — `AgentConfig` has no log level).

**Acceptance criteria**
- [ ] With only `AGENTSPAN_SERVER_URL` set, `Configuration()` resolves it; with
      both set, `CONDUCTOR_SERVER_URL` wins.
- [ ] `Configuration(logLevel="WARNING")` and `CONDUCTOR_LOG_LEVEL=WARNING` both
      yield WARNING; the agent runtime applies it to the agent loggers.

---

### R4 — `AgentConfig` is agent-runtime behaviour ONLY

**Rationale:** `AgentConfig` previously duplicated connection/auth/log settings,
creating two sources of truth. Connection, auth, and log level now come from
`Configuration` exclusively.

**REMOVE from `AgentConfig`** (or never add): `serverUrl`, `apiKey`, `authKey`,
`authSecret` (and any `apiSecret` alias), `llmRetryCount` (dead), `secretStrictMode`
(dead — fail-closed is unconditional, see R6), `logLevel` (moved to Configuration).

**KEEP / ADD** (defaults and env names):

| Field | Type | Default | Env var |
|---|---|---|---|
| `workerPollIntervalMs` | int | 100 | `AGENTSPAN_WORKER_POLL_INTERVAL` |
| `workerThreadCount` | int | 1 | `AGENTSPAN_WORKER_THREADS` |
| `autoStartWorkers` | bool | true | `AGENTSPAN_AUTO_START_WORKERS` |
| `daemonWorkers` | bool | true | `AGENTSPAN_DAEMON_WORKERS` |
| `autoRegisterIntegrations` | bool | false | `AGENTSPAN_INTEGRATIONS_AUTO_REGISTER` |
| `streamingEnabled` | bool | true | `AGENTSPAN_STREAMING_ENABLED` |
| `livenessEnabled` | bool | true | `AGENTSPAN_LIVENESS_ENABLED` |
| `livenessStallSeconds` | float | 30.0 | `AGENTSPAN_LIVENESS_STALL_SECONDS` |
| `livenessCheckIntervalSeconds` | float | 10.0 | `AGENTSPAN_LIVENESS_CHECK_INTERVAL_SECONDS` |

`AgentConfig.fromEnv()` reads the env vars above. It MUST NOT read server URL,
credentials, or log level.

**Acceptance criteria**
- [ ] Constructing `AgentConfig` with a connection/auth/log field is a compile
      error (typed languages) or raises (dynamic languages).
- [ ] `fromEnv()` honors each env var; empty string falls back to the default.
- [ ] Liveness defaults: enabled, 30.0s stall, 10.0s interval.

---

### R5 — `AgentRuntime` construction and transport

**Constructor contract:**

```
AgentRuntime(configuration?: Configuration, settings?: AgentConfig)
```

- `configuration` defaults to an env-resolved `Configuration()` and is the sole
  source of host/auth/log level. `settings` defaults to `AgentConfig.fromEnv()`.
- The runtime builds its clients from ONE `OrkesClients(configuration)`:
  `agentClient = clients.getAgentClient()` plus the workflow/task clients it
  needs. All share one API client token cache.
- **Every** `/agent/*` operation (start, deploy, compile, status, execution list,
  respond, stop, signal, SSE) goes through `agentClient`. The runtime MUST NOT
  hold its own HTTP transport, base-URL builder, or token helper.
- Expose the transport as a read-only `client` property returning the
  `AgentClient` (useful for tests and advanced callers).
- **REMOVE server auto-start:** no code that probes whether the agent server is
  running or launches one. Absence of a server surfaces as a connection error.

**Start flow** (shared by `run`/`start`, sync and async):

```
FUNCTION startInternal(agent, prompt, runSettings?, media?, sessionId?,
                       idempotencyKey?, timeout?, credentials?, context?, runId?):
    configJson = serialize(agent)                      // agent -> agentConfig
    IF runSettings != null:
        applyOverrides(configJson, runSettings)        // R8
    payload = { agentConfig: configJson, prompt: prompt,
                sessionId: sessionId ?? "", media: media ?? [] }
    // optional keys, only when set:
    //   context, idempotencyKey, timeoutSeconds, credentials, runId
    data = agentClient.startAgent(payload)             // server: compile+register+start
    executionId     = data["executionId"]
    requiredWorkers = data["requiredWorkers"]          // optional set of task names
    prepareWorkers(agent, requiredWorkers)             // start tool workers
    RETURN executionId
```

**Acceptance criteria**
- [ ] `AgentRuntime(Configuration(serverApiUrl=X))` talks to X; an `AgentConfig`
      passed as `settings` cannot alter connection or auth.
- [ ] Grep-level check: no `POST /token`, no raw URL string-building for
      `/agent/*`, and no server-launch code anywhere in the runtime.
- [ ] `runtime.client` is the same `AgentClient` instance the runtime uses.

---

### R6 — Worker credentials via `runtimeMetadata` (fail-closed)

**Rationale:** Tool workers need secrets (API keys, tokens). The old design used a
per-execution token and a `POST /workers/secrets` fetch — a second auth path.
The new contract makes the *server* resolve secrets at poll time and deliver them
on the task, wire-only.

**Model fields** (add to the SDK's HTTP models; JSON wire names are exact):

| Model | Field | JSON wire name | Type | Semantics |
|---|---|---|---|---|
| `TaskDef` | runtimeMetadata | `runtimeMetadata` | `string[]` | Names of secrets this task type requires |
| `Task` | runtimeMetadata | `runtimeMetadata` | `map<string,string>` | Name → resolved secret value; delivered on the wire at poll time; never persisted |

**Registration (SDK side):** when a tool declares credentials
(`tool(credentials=["GH_TOKEN"])` or equivalent), the SDK MUST stamp those *names*
onto the tool's `TaskDef.runtimeMetadata` at worker registration. Because worker
registration typically uses overwrite semantics (`overwriteTaskDef=true`), the SDK
MUST re-stamp on every registration so a re-register does not wipe the
server-side value.

**Dispatch (worker side):** before invoking the tool function:

```
FUNCTION resolveSecrets(task, declaredNames):
    delivered = task.runtimeMetadata ?? {}
    missing = [n FOR n IN declaredNames IF n NOT IN delivered]
    IF missing NOT EMPTY:
        THROW CredentialNotFoundError(missing)      // task FAILS — no fallback
    RETURN { n: delivered[n] FOR n IN declaredNames }
```

- Inject the resolved values into the tool's execution environment **for that call
  only** (e.g. scoped env-var injection with restoration, or explicit parameter).
- **Fail closed:** if a declared credential was not delivered, the task fails with
  a clear error. The worker MUST NOT fall back to reading the ambient process
  environment.
- **RETIRE** the execution-token flow: remove any `executionToken` /
  `__agentspan_ctx__` handling and any `POST /workers/secrets` client code.

**Server dependency note:** this contract requires a server that persists
`TaskDef.runtimeMetadata` and delivers `Task.runtimeMetadata`
(conductor-oss PR #1255 / agentspan server > 0.4.2). Integration tests SHOULD
capability-probe (register a TaskDef with `runtimeMetadata`, read it back; skip
the suite if the server drops the field).

**Acceptance criteria**
- [ ] Registering a tool with declared credentials produces a server TaskDef whose
      `runtimeMetadata` equals the declared name list, and re-registration
      preserves it.
- [ ] A task delivering `runtimeMetadata: {NAME: value}` results in the tool
      seeing `value`; the injected value is gone after the call.
- [ ] With the secret absent server-side and `NAME` present in the worker's own
      environment, the task FAILS (env value never used).
- [ ] No references to `workers/secrets` or execution tokens remain.

---

### R7 — Single token authority for worker-side agent posts

**Rationale:** Framework/tool workers running inside worker executors also call
the server (progress, events, sub-agent tracking). These calls previously used a
standalone token mint+cache. They must reuse the standard API client.

**Constraint:** worker executors may be separate processes that cannot receive a
live client object; they receive plain strings `(serverUrl, authKey, authSecret)`.

**Contract — an internal `agentHttp` helper:**

```
// Module/package-level cache. The API client constructor mints a token,
// so caching per credential is MANDATORY (never construct per call).
cache: Map<(serverUrl, authKey), ApiClient>   // guarded by a lock

FUNCTION agentApiClient(serverUrl, authKey, authSecret) -> ApiClient:
    RETURN cache.getOrCreate((serverUrl, authKey), () ->
        ApiClient(Configuration(serverApiUrl=serverUrl,
                  authenticationSettings=(authKey ? {authKey, authSecret} : null))))

FUNCTION agentPost(serverUrl, authKey, authSecret, path, body,
                   readResponse=false) -> object | null:
    TRY:
        client = agentApiClient(serverUrl, authKey, authSecret)
        RETURN client.callApi(path, "POST", body,
                              responseType = readResponse ? "object" : none)
    CATCH anything:
        log_debug(...); RETURN null      // graceful degradation — callers never crash
```

- `path` starts with `/` and omits `/api` (host already ends in `/api`).
- Fire-and-forget callers (event push, task-status completion) ignore the return.
  Read-response callers interpret `null` as failure (e.g. "tracking workflow not
  created", "injection failed → false").
- Worker-side endpoints served by this helper:
  `POST /agent/events/{executionId}` (event push),
  `POST /agent/execution` (create tracking workflow → `{executionId}`),
  `POST /agent/{executionId}/tasks` (inject display task),
  `POST /agent/tasks/{executionId}/{refTaskName}/{status}` (complete injected task),
  `POST /agent/execution/{executionId}/complete` (complete tracking workflow).
  Task-progress updates use the native task client (`updateTask` with
  `IN_PROGRESS`) built on the **same** cached client.
- **DELETE** the parallel token helper: any standalone
  `POST {server}/token` mint with its own `(serverUrl, authKey) → (token, exp)`
  cache. If a JWT-expiry decoder is used elsewhere, keep only the decoder.

**Acceptance criteria**
- [ ] Two `agentPost` calls with the same `(serverUrl, authKey)` cause exactly
      **one** `POST /token` mint; both requests carry `X-Authorization`.
- [ ] Anonymous (`authKey` empty): no mint, no auth header, request still sent.
- [ ] HTTP 500 and 404 both return `null` (no exception escapes).
- [ ] `readResponse=true` returns the parsed JSON object.
- [ ] Grep-level check: exactly one code path in the SDK performs `POST /token`.

---

### R8 — `RunSettings`: per-run LLM overrides

**Contract:** a small value type accepted by `run`/`start` (and async variants,
and any module-level convenience wrappers) as `runSettings`:

| Field | Overrides `agentConfig` wire key |
|---|---|
| `model` | `model` |
| `temperature` | `temperature` |
| `maxTokens` | `maxTokens` |
| `reasoningEffort` | `reasoningEffort` |
| `thinkingBudgetTokens` | `thinkingConfig = {"enabled": true, "budgetTokens": <n>}` |

```
FUNCTION applyOverrides(configJson, rs):
    FOR (field, wireKey) IN mapping:
        IF rs[field] != null:                 // null-check, NOT truthiness:
            configJson[wireKey] = rs[field]   // temperature=0.0, maxTokens=0 must apply
```

- Applied to the **serialized root** `agentConfig` after serialization, before
  `startAgent` — SDK-side only, no new server field. Sub-agents keep their own
  per-agent settings (no cascade).
- Only set fields override; unset fields keep the agent's values.
- Accept both the typed value and a plain map with the same keys (where idiomatic);
  unknown keys are an error.
- Do NOT add `top_p`/`topP` — it does not exist in the agentConfig contract.

**Acceptance criteria**
- [ ] Full override lands in the start payload (`model`, `temperature`,
      `maxTokens`, `reasoningEffort`, `thinkingConfig`).
- [ ] No `runSettings` → payload equals the agent's own settings.
- [ ] Partial override changes only provided fields; `temperature=0.0` applies.
- [ ] `run` and `start` both forward `runSettings` to the shared start flow.

---

### R9 — Verb contract (`serve` = `deploy` + serve)

The runtime verbs MUST behave exactly as follows:

| Method | Blocks | Returns | Starts workers | Registers agent on server | Executes |
|---|---|---|---|---|---|
| `run(agent, prompt, …)` | yes (poll to completion) | result object (`output`, `status`, ids, usage) | **yes** | via start (compile+register+start is one server call) | yes |
| `start(agent, prompt, …)` | no | handle object (`executionId`, `join()`, `stop()`, streaming) | **yes** | via start | yes |
| `deploy(*agents, …)` | yes | list of deployment info | **no** | **yes** (`POST /agent/deploy` per agent) | no |
| `serve(*agents, blocking=true)` | yes, until SIGINT/SIGTERM (`blocking=false` returns) | void | **yes** (registers tool workers + starts polling) | **yes** — deploys each agent before starting workers | no |
| `plan(agent)` | yes | compiled workflow def | no | no | no |

- `run` = start + wait; both `run` and `start` also start the tool workers so the
  scheduled tool tasks execute.
- Keep the rich return objects (result/handle) — do NOT return bare
  ids/outputs; the id is `handle.executionId`, the output is `result.output`.
- **`serve` change:** in its per-agent loop, call the same internal deploy helper
  `deployViaServer(agent, framework)` **before** registering/starting that agent's
  workers. This covers native and framework agents, and is idempotent with
  overwrite-style task-def registration (same ordering `run` already uses).
- `serve(blocking=false)` MUST return after registration + worker start (needed
  for tests and embedding).

**Acceptance criteria**
- [ ] `deploy` registers the workflow server-side and starts zero worker
      processes.
- [ ] `serve(agent, blocking=false)` (a) triggers one deploy call per agent,
      (b) deploy happens before worker start, (c) workers are polling on return.
- [ ] `start` returns immediately with a usable handle; `run` blocks and returns
      the result; both started the required workers.

---

### R10 — Worker-callable registration safety

**Invariant (language-agnostic):** every callable registered as a worker/tool must
be **reconstructible in the executor context** that runs it.

- If your worker executors are **spawned processes** (Python-style): callables
  must be importable by qualified name or serializable by value — module-level
  functions, or module-level classes instantiated with plain-data fields. Local
  closures, lambdas capturing live objects, and functions defined inside other
  functions MUST be rejected at registration time with an actionable error
  ("define the callable at module level"). Entry-point scripts must guard
  top-level orchestration with the language's main-module idiom so a re-import in
  the child does not re-run it.
- If your executors are **threads in-process** (Java/Go/C#/TS typical): the
  invariant reduces to "no capture of per-run mutable runtime state"; document it,
  and keep factory boundaries clean regardless (next point).
- **Factory boundary:** framework/tool worker factories receive only plain data —
  `(serverUrl, authKey, authSecret)` strings plus config — never a live runtime,
  client, or connection object. Inside the executor they reconstruct clients via
  R7's cached helper.
- Auto-generated workers (e.g. a CLI-command tool) must follow the same rule:
  implement them as a module-level callable class holding plain config (allowed
  commands, timeout, working dir), not a closure.

**Acceptance criteria**
- [ ] Registering a closure/lambda as a tool fails fast with an actionable error
      (process-spawn runtimes) or is impossible by API design (typed runtimes).
- [ ] A registration-time round-trip test: serialize/reconstruct each registered
      callable the way the executor would, and invoke it.

---

### R11 — Liveness monitor (stateful runs)

**Rationale:** for stateful runs, tasks are routed to this process's workers via a
domain. If the worker dies, the server-side task sits with `pollCount=0` forever
and a blocking `join()`/`result()` would hang.

**Contract:** when a run is stateful (domain-routed) and
`AgentConfig.livenessEnabled`:
- A monitor polls the workflow every `livenessCheckIntervalSeconds`.
- If a scheduled task has had **no polls** for `livenessStallSeconds`, the monitor
  fires a stall: blocking waiters (`join`/`result`) raise a `WorkerStallError`
  (message naming the stalled task) instead of blocking forever.
- The monitor stops when the run reaches a terminal state or the handle is closed.

**Acceptance criteria**
- [ ] With a killed worker, `join(timeout=∞)` surfaces `WorkerStallError` within
      `stall + interval` seconds.
- [ ] `livenessEnabled=false` disables the monitor entirely.

---

### R12 — Deletions checklist

Remove (and ensure nothing references them):

- [ ] Bespoke agent HTTP transport classes (e.g. an `AgentApiClient` that minted
      its own JWT) and any DX wrapper client around them.
- [ ] The credentials **fetcher** (execution-token + `POST /workers/secrets`).
- [ ] Agent **server auto-start / detection** logic and its config flag
      (`autoStartServer` / `AGENTSPAN_AUTO_START_SERVER`).
- [ ] The **parallel token cache** (standalone `POST /token` mint helper) — keep
      at most a JWT-`exp` decoder.
- [ ] Dead `AgentConfig` fields (R4 list) and any `toConductorConfiguration()`
      bridge that mapped AgentConfig connection fields into `Configuration`.

---

### R13 — Swarm transfer contract (hand-off note + first-wins)

**Rationale:** in the swarm strategy, agents hand off via server-compiled
`{source}_transfer_to_{target}` tools, and the SDK supplies two system workers:
the per-tool **transfer worker** and the per-agent **`{name}_check_transfer`**
worker that inspects the LLM's `toolCalls` output. Two failure modes were
observed in production runs and are now part of the contract:

1. A transfer used to carry **no payload** — only the routing (`transfer_to`)
   survived, so the delegating agent's instructions were lost and a
   tool-calls-only turn polluted the shared conversation as `[agent]: []`.
2. When the LLM emitted **multiple transfer calls in one turn**, all but the
   first were **silently dropped** — the model's fan-out intent vanished with no
   trace in any task output.

The server compiler (conductor `agentspan-server` `MultiAgentCompiler`) now
generates transfer tools with a required `message` argument ("hand-off note"),
records honored hand-offs in the conversation as
`[source -> target]: <message>`, drops `[]`/`{}` tool-call-only results from
the transcript, and round-trips the structured `context` (`_agent_state`)
through every swarm agent sub-workflow. The SDK's side of the contract is the
two workers:

**Transfer worker (`{source}_transfer_to_{target}`)**
- MUST accept an optional string input `message` (the hand-off note the LLM
  wrote for the receiving agent).
- MUST echo it back — output `{"message": "<message>"}` when non-empty, `{}`
  otherwise — so the note is visible in the task output / UI. The worker
  remains otherwise a no-op: the hand-off itself is detected by
  `check_transfer`, not by this task.
- The unreachable-target variant (targets excluded by `allowed_transitions`)
  is unchanged: return an error string telling the model to pick another tool.

**`{name}_check_transfer` worker**
- Input: `tool_calls` — the LLM task's `toolCalls` output; a list of objects
  with at least `name` and `inputParameters`.
- Scan in emission order for names containing `_transfer_to_`. Selection is
  **first-wins** (the swarm loop can only hand off to one agent per turn).
- Output contract:

  ```json
  {
    "is_transfer": true,
    "transfer_to": "engineering_lead",
    "transfer_message": "Design the REST API",
    "dropped_transfers": [                     // ONLY when >1 transfer call
      {"transfer_to": "marketing_lead", "message": "Plan the launch"}
    ]
  }
  ```

  - `transfer_to` — text after the first `_transfer_to_` in the winning call's
    name.
  - `transfer_message` — the winning call's `inputParameters.message`,
    stringified; `""` when absent (older tool schema) or null.
  - `dropped_transfers` — every non-winning transfer call, in order, with the
    same `{transfer_to, message}` shape. MUST be omitted when there is a
    single transfer. Log a warning naming the honored target and the dropped
    ones — the drop must never be silent.
  - No transfer call at all → `{"is_transfer": false, "transfer_to": "",
    "transfer_message": ""}`.

**Acceptance criteria**
- [ ] Transfer worker echoes `message`; returns `{}` when called without one
      (backward compatible with pre-`message` tool schemas).
- [ ] `check_transfer` returns `transfer_message` from the first transfer
      call's `inputParameters.message`; `""` when the argument is missing.
- [ ] With two transfer calls in one turn: first wins, second appears in
      `dropped_transfers`, and a warning is logged.
- [ ] With no transfer calls (or `tool_calls` null): `is_transfer=false`,
      empty `transfer_to`/`transfer_message`, no `dropped_transfers` key.

---

## 3. Wire contracts appendix

### 3.1 Authentication

```
POST {server}/token
Body:     {"keyId": "<authKey>", "keySecret": "<authSecret>"}
Response: {"token": "<jwt>"}
Header on all subsequent calls:  X-Authorization: <jwt>
```
Anonymous servers: no mint; send no auth header. A 404 from `/token` means an
open (auth-disabled) server — treat as anonymous.

### 3.2 Agent control-plane endpoints

`{server}` ends in `/api` (e.g. `http://localhost:8080/api`).

| Method + path | Body | Response |
|---|---|---|
| `POST /agent/start` | start payload (3.3) | `{"executionId": "...", "requiredWorkers": ["taskName", ...]?}` |
| `POST /agent/deploy` | `{"agentConfig": {...}}` or `{"framework": "...", "rawConfig": {...}}` | `{"agentName": "..."}` |
| `POST /agent/compile` | `{"agentConfig": {...}}` | compiled workflow def |
| `GET /agent/{executionId}/status` | — | status object |
| `GET /agent/execution/{executionId}` | — | execution object |
| `GET /agent/executions?…` | — | list object |
| `POST /agent/{executionId}/respond` | free-form JSON (HITL answer) | — |
| `POST /agent/{executionId}/stop` | — | — |
| `POST /agent/{executionId}/signal` | message | — |
| `GET /agent/stream/{executionId}` | SSE; headers `Accept: text/event-stream`, `X-Authorization`, `Last-Event-ID?` | `event:`/`data:`/`id:` frames |
| `POST /agent/events/{executionId}` | event object (worker-side push) | — |
| `POST /agent/execution` | `{"workflowName", "input", "parentWorkflowId"?, "parentWorkflowTaskId"?}` | `{"executionId": "..."}` |
| `POST /agent/{executionId}/tasks` | `{"taskDefName", "referenceTaskName", "type", "inputData", "subWorkflowParam"?}` | 2xx = injected |
| `POST /agent/tasks/{executionId}/{refTaskName}/{status}` | output data | — |
| `POST /agent/execution/{executionId}/complete` | output data | — |

### 3.3 Start payload

```json
{
  "agentConfig":   { "...serialized agent (3.4)..." },
  "prompt":        "user input",
  "sessionId":     "",
  "media":         [],
  "context":        { },            // optional
  "idempotencyKey": "…",            // optional
  "timeoutSeconds": 120,            // optional
  "credentials":   ["GH_TOKEN"],    // optional — names to resolve for this run
  "runId":         "…",             // optional — stateful worker-domain routing
  "static_plan":   { }              // optional — PLAN_EXECUTE fixed plan
}
```

### 3.4 `agentConfig` LLM wire keys (subset relevant to RunSettings)

Top level of the serialized agent config:

```json
{
  "name": "…",
  "model": "provider/model",
  "temperature": 0.2,
  "maxTokens": 512,
  "reasoningEffort": "high",
  "thinkingConfig": { "enabled": true, "budgetTokens": 2048 }
}
```
Keys are absent when unset (serializers strip nulls); an override simply sets the
key.

### 3.5 Credential models

```json
// TaskDef (declaration — names only)
{ "name": "my_tool", "runtimeMetadata": ["GH_TOKEN", "DB_PASSWORD"], ... }

// Task (delivery — wire-only, poll-time)
{ "taskId": "…", "taskDefName": "my_tool",
  "runtimeMetadata": { "GH_TOKEN": "ghp_…", "DB_PASSWORD": "…" }, ... }
```

---

## 4. Acceptance test matrix

Port these as integration-style tests against an in-process HTTP stub server
(preferred; count mints, capture headers/bodies) or mocks where that is the
repo's convention.

| # | Test | Requirement |
|---|---|---|
| T1 | Token minted once per (serverUrl, authKey); cached across calls; TTL renewal | R1, R2, R7 |
| T2 | `X-Authorization` present on every control-plane and worker-side call | R1, R7 |
| T3 | 401 triggers one forced refresh + retry (then surfaces) | R1 |
| T4 | SSE request reuses the API-client token; no separate mint | R1, R2 |
| T5 | 404 → `AgentNotFoundError`; 5xx → `AgentAPIError` (control plane); worker-side posts degrade to null | R1, R7 |
| T6 | Host env fallback order; log level param/env order | R3 |
| T7 | `AgentConfig` rejects connection/auth fields; liveness env parsing | R4 |
| T8 | Runtime has no bespoke `/agent/*` transport; `runtime.client` identity | R5 |
| T9 | TaskDef.runtimeMetadata stamped with declared names; survives re-registration | R6 |
| T10 | Delivered secret injected per-call; missing secret fails task; ambient env NEVER read | R6 |
| T11 | `agentPost` mint-once, anonymous no-header, 500/404→null, readResponse→object | R7 |
| T12 | run_settings full/partial/zero-value override in start payload; none→agent's own | R8 |
| T13 | run/start forward runSettings; async variants too | R8 |
| T14 | deploy registers, starts nothing; serve deploys each agent before worker start; serve(blocking=false) returns | R9 |
| T15 | Closure/lambda tool registration fails fast (spawn runtimes) | R10 |
| T16 | Killed worker → `WorkerStallError` from join within stall+interval | R11 |
| T17 | Grep: no `workers/secrets`, no execution token, no parallel `/token` mint, no server auto-start | R6, R12 |
| T18 | Transfer worker echoes `message` / `{}` without one; `check_transfer` extracts `transfer_message`, first-wins with `dropped_transfers` + warning on multi-transfer, `is_transfer=false` on none | R13 |

---

## 5. Implementation order & definition of done

Dependency-ordered phases:

1. **Phase A — core client:** R2 (auth-header accessor), R3 (Configuration).
2. **Phase B — control plane:** R1 (`AgentClient` + Orkes impl + factory),
   R5 (runtime on the client; delete bespoke transports & auto-start).
3. **Phase C — credentials:** R6 (models, stamping, fail-closed dispatch; retire
   fetcher).
4. **Phase D — worker-side token unification:** R7 (`agentHttp`; delete parallel
   cache).
5. **Phase E — ergonomics:** R8 (`RunSettings`), R9 (verb contract, serve=deploy+serve).
6. **Phase F — hardening:** R10 (callable safety), R11 (liveness), R12 (deletion
   sweep), R13 (swarm transfer contract).

**Definition of done:** all R1–R13 acceptance criteria hold; the T1–T18 matrix is
implemented and green; the full SDK test suite passes; a repo-wide search finds no
references to the removed components (R12); and a live smoke test against an agent
server demonstrates: `deploy` (registered, no workers) → `serve(blocking=false)`
(registered + polling) → `start` with a `runSettings` override (override visible in
the execution's LLM task input) → `run` to completion.
