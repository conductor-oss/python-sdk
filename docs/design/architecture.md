# Agent Worker Callable Transport Architecture

**Status:** Authoritative

**Last updated:** 2026-08-09

**Scope:** Python agent-framework tool registration across multiprocessing
`spawn` and `forkserver` executors.

This document is the source of truth for the complete file layout, shared
contracts, exact types, data model, and naming conventions used to transport
agent tool callables into worker processes. It resolves GitHub issue #448
without changing the SDK multiprocessing start method or weakening
registration-time validation.

## Problem Statement

Python workers use `spawn` on every supported operating system. A worker
callable must cross a standard-`pickle` boundary and be reconstructible after
the child imports its defining module.

Some decorators replace the module global that originally named the function:

- LangChain `@tool` binds the global to a `StructuredTool` and exposes the
  original through `func` or `coroutine`.
- OpenAI Agents SDK `@function_tool` binds the global to a `FunctionTool`. In
  the issue's reproduced `openai-agents==0.18.2` shape, the original function
  is reachable through nested invocation state and a closure rather than a
  supported public attribute.

The original function is module-level, but normal function pickling fails
because importing `module.get_inventory` returns the decorator container, not
the same function object. This differs from issue #443: a true local contains
`<locals>` in its qualified name and remains unsupported by this focused fix.

## Compatibility Boundary

The regression contract is pinned to `openai-agents==0.18.2`, the version from
issue #448. The pin is test-fixture-only:

```text
tests/requirements/openai_agents_0_18_2.txt
```

contains exactly:

```text
openai-agents==0.18.2
```

The targeted regression environment MUST be installed with:

```bash
python -m pip install -e ".[openai-agents]" \
  -c tests/requirements/openai_agents_0_18_2.txt
```

The regression test MUST also assert
`importlib.metadata.version("openai-agents") == "0.18.2"` before constructing
the fixture. This makes an incorrectly prepared environment fail explicitly
rather than silently testing another framework shape.

This fixture does not change `pyproject.toml`, `poetry.lock`, the existing
`.[agents]` install path, or any GitHub Actions workflow. The package's public
optional dependency remains `openai-agents>=0.12.2`; the existing lockfile may
continue selecting its current version. Newer OpenAI Agents SDK versions MAY
resolve through a simpler `__wrapped__` path, but they must not replace the
`0.18.2` regression fixture.

This design intentionally keeps standard `pickle`. It does not add
`cloudpickle` transport for local functions, closures, or lambdas.

## Authoritative File Layout

```text
src/conductor/ai/agents/
├── frameworks/
│   └── serializer.py
│       ├── discovers framework tools
│       └── emits WorkerInfo.func as the original plain function
└── runtime/
    ├── _worker_entries.py
    │   ├── SpawnSafetyError
    │   ├── FunctionKey
    │   ├── FunctionRef
    │   ├── ToolWorkerEntry
    │   ├── _iter_embedded_functions
    │   ├── wrap_callable / unwrap_callable
    │   └── probe_spawn_safety
    └── runtime.py
        └── _register_framework_workers

src/conductor/client/automator/
└── task_handler.py
    └── establishes the multiprocessing start method used by workers

tests/unit/
├── ai/
│   ├── test_worker_entries.py
│   └── test_openai_agents_spawn_registration.py
└── resources/
    └── openai_agents_entry_helpers.py

tests/requirements/
└── openai_agents_0_18_2.txt
```

`frameworks/serializer.py` and `runtime/_worker_entries.py` MUST call the same
`_iter_embedded_functions` implementation. Parent-side extraction and
child-side reconstruction MUST NOT have parallel traversal implementations.

## Data Model

### `FunctionKey`

`FunctionKey` identifies a plain function across parent and spawned-child
imports without depending on object identity or a framework-private attribute
path.

```python
@dataclass(frozen=True)
class FunctionKey:
    module: str
    qualname: str
    code_sha256: str
```

`code_sha256` is the lowercase SHA-256 hex digest of
`marshal.dumps(fn.__code__)`. `FunctionKey.of(fn)` accepts only
`inspect.isfunction(fn)` values. The code digest distinguishes an original
function from wrappers that copied its `__module__` and `__qualname__` with
`functools.wraps`.

### `FunctionRef`

`FunctionRef` is an immutable, pickle-safe recipe for recovering one plain
function after importing its module.

```python
@dataclass(frozen=True)
class FunctionRef:
    module: str
    qualname: str
    unwrap_depth: int = 0
    attr_hop: str = ""
    deep_extract: bool = False
    expected_key: FunctionKey | None = None
```

| Field | Contract |
|---|---|
| `module` | Importable module containing the public global. |
| `qualname` | Attribute path from the module to the public global. It MUST NOT contain `<locals>` or `<lambda>`. |
| `unwrap_depth` | Number of `__wrapped__` hops after resolving the public global or `attr_hop`. Range: `0..32`. |
| `attr_hop` | One stable container attribute. Supported values are `""`, `"func"`, and `"coroutine"`. |
| `deep_extract` | Whether reconstruction uses bounded embedded-function traversal. |
| `expected_key` | Required only for deep extraction; identifies the exact candidate selected in the parent. |

Invariants:

- `attr_hop` and `deep_extract` MUST NOT both be active.
- `deep_extract=True` requires `unwrap_depth=0` and a non-null `expected_key`.
- `deep_extract=False` requires `expected_key=None`.

### `ToolWorkerEntry`

`ToolWorkerEntry` transports a tool target plus plain worker metadata:

```python
ToolWorkerEntry(
    tool_name: str,
    fn_ref: FunctionRef | None = None,
    fn_direct: Callable | None = None,
    guardrails: list | None = None,
    credential_names: list[str] | None = None,
    framework_callable: bool = False,
)
```

Exactly one of `fn_ref` or `fn_direct` MUST be set.

- `fn_ref` is mandatory for every plain Python function, including a function
  recovered from a decorator container.
- `fn_direct` is reserved for non-function callable objects that pass the
  direct-object round-trip contract below. Putting a plain function in
  `fn_direct` is forbidden because standard `pickle` still serializes it by
  module and qualified name.

## Deterministic Embedded-Function Traversal

`_iter_embedded_functions(root, max_depth=2)` yields candidate plain functions
in a deterministic breadth-first traversal. It is framework-agnostic and MUST
NOT hardcode OpenAI private attribute names or closure-cell positions.

The algorithm is exact:

1. Maintain a FIFO queue of `(object, attribute_depth)`, initialized with
   `(root, 0)`, plus `visited_object_ids` and `yielded_function_ids` sets.
2. Pop FIFO. If its identity was visited, skip it; otherwise mark it visited.
3. If the object is a plain function:
   1. Read `__closure__` without evaluating descriptors.
   2. Visit closure cells in numeric index order. Ignore empty cells
      (`ValueError`). For each cell containing a plain function, emit it first
      if it is an eligible candidate and has not already been emitted.
   3. Emit the function itself if eligible and not already emitted.
   4. Do not enqueue arbitrary function attributes.
4. If the object is not a function and `attribute_depth < max_depth`, obtain
   `vars(object)`. If `vars` raises `Exception` (but not `BaseException`), treat
   the object as a leaf. Iterate the resulting mapping's keys in
   lexicographic order; read values directly from the mapping, never with
   `getattr`, so properties and descriptors cannot execute. Enqueue non-scalar,
   non-module, non-type values at `attribute_depth + 1`.
5. Scalars (`None`, booleans, numbers, strings, bytes), modules, and classes are
   leaves. Cycles are harmless because identities are visited once.

A function is an eligible candidate when all of these hold:

- `inspect.isfunction(candidate)` is true;
- `candidate.__module__` is a non-empty string;
- `candidate.__qualname__` is a non-empty string containing neither `<locals>`
  nor `<lambda>`.

Traversal MUST NOT inspect a candidate's signature or exclude it based on
parameter names. In particular, `ctx` and `context` are valid first-parameter
names for context-aware tools and MUST remain in the candidate set.

Closure inspection does not consume attribute depth. Therefore the reproduced
`0.18.2` shape may use two object-attribute edges and then inspect the reached
wrapper function's closure.

### Candidate selection and proof

Traversal never means "take the first plausible function."

- In the parent, framework serializer extraction retains every eligible
  candidate and deduplicates repeated references to the same object. It selects
  by the existing tool-name/uniqueness contract only: first filter by exact
  `candidate.__name__ == tool.name`; exactly one match selects that candidate.
  If there are no name matches, the sole eligible candidate may be selected.
  More than one name match, or more than one eligible candidate when there is
  no name match, is ambiguous and raises `SpawnSafetyError` listing candidate
  keys in traversal order. Signatures, annotations, parameter names, and
  `FunctionKey` values MUST NOT rank, filter, or select parent-side candidates.
- `FunctionRef.of(target)` uses object identity to confirm that deep traversal
  of the rebound public global contains `target`, then stores
  `expected_key=FunctionKey.of(target)`.
- In the child, `FunctionRef.resolve()` repeats the same traversal and selects
  candidates whose `FunctionKey` equals `expected_key`. Exactly one distinct
  candidate object must match. Zero matches means the imported definition
  changed; multiple matches mean reconstruction is ambiguous. Both cases raise
  `SpawnSafetyError` before invocation.

`FunctionKey` is used only after parent-side selection, to prove that child
reconstruction recovered the same source callable rather than a neighboring
closure or framework wrapper. It is not a discovery or selection heuristic.

## `FunctionRef` Resolution Contract

`FunctionRef.of(fn)` accepts only a plain function and selects the first
successful deterministic strategy in this order:

1. **Direct identity:** resolving `module + qualname` returns `fn`.
2. **Wrapped function:** following at most 32 `__wrapped__` hops from the public
   global reaches `fn`; record `unwrap_depth`.
3. **Stable container attribute:** `func` then `coroutine`, in that order,
   reaches `fn`, optionally followed by at most 32 `__wrapped__` hops; record
   `attr_hop` and `unwrap_depth`.
4. **Deep extraction:** deterministic traversal of the public global contains
   `fn`; set `deep_extract=True` and record `expected_key`.
5. **Failure:** raise `SpawnSafetyError` saying the public name resolves to a
   rebound container but no supported path reconstructs the requested function.

The OpenAI `FunctionTool` acceptance condition is strategy-neutral. Depending
on the exact framework object shape, a module-level `@function_tool` MAY encode
as a positive `unwrap_depth` or as `deep_extract=True`; tests MUST assert
successful deterministic reconstruction, not require one contradictory flag.

`FunctionRef.resolve()` imports `module`, walks `qualname`, performs only the
encoded strategy, validates the final object is a plain function, and caches it
per process. Attribute and unwrap failures are converted to `SpawnSafetyError`
that names the module, qualified name, and failed strategy.

## `ToolWorkerEntry.for_callable` Contract

`ToolWorkerEntry.for_callable(fn, tool_name, ...)` follows these rules exactly:

1. If `inspect.isfunction(fn)`, call `FunctionRef.of(fn)`. On failure, propagate
   its `SpawnSafetyError`. A plain function MUST NOT fall back to `fn_direct`.
   This covers module-level rebound functions, true locals, and lambdas.
2. If `inspect.ismethod(fn)`, reject it with `SpawnSafetyError`: bound methods
   are unsupported because their instance transport and rebinding semantics are
   not the callable-object contract. The error instructs the user to expose a
   module-level function or a module-level callable class instance.
3. If `fn` is any other callable object, validate direct transport by running
   `payload = pickle.dumps(fn)` and `clone = pickle.loads(payload)` with standard
   `pickle`. The clone MUST be callable, and `pickle.dumps(clone)` MUST also
   succeed. Only then construct `fn_direct=fn`.
4. Non-callable values are rejected with `SpawnSafetyError`.

Direct-object validation catches and wraps the original exception. Its message
MUST name `tool_name`, the callable type, and state that standard-pickle
round-trip validation failed. It MUST NOT recommend module scope when the
actual failure is unpickleable object state.

Required error behavior:

| Input | Result |
|---|---|
| Module-level plain function, directly importable | `fn_ref` |
| Module-level decorator-rebound function with a supported path | `fn_ref` |
| Local function | `SpawnSafetyError` naming `<locals>`; no direct fallback |
| Lambda | `SpawnSafetyError` naming `<lambda>`; no direct fallback |
| Bound method | `SpawnSafetyError` naming bound methods as unsupported |
| Module-level callable instance with pickle-safe state | `fn_direct` after two serialization passes and one load |
| Callable instance with unpickleable state | `SpawnSafetyError` with the round-trip cause |
| Rebound decorator container that cannot reconstruct the requested function | `SpawnSafetyError` explaining the container mismatch, not "move it to module level" |

Framework serialization MUST emit the extracted original plain function in
`WorkerInfo.func`; it MUST NOT pass the `FunctionTool`/`StructuredTool`
container itself to `for_callable` as a way to bypass reconstruction.

## Registration Contract

`AgentRuntime._register_framework_workers` remains the production path:

1. `frameworks.serializer.serialize_agent()` emits `WorkerInfo` records.
2. `make_tool_worker()` creates a `ToolWorkerEntry` through `for_callable`.
3. `probe_spawn_safety(wrapper, worker_info.name, group="tools")` constructs a
   throwaway Conductor `Worker` around that exact `ToolWorkerEntry` and
   standard-pickles the complete `Worker` whenever the active start method is
   `spawn` or `forkserver`.
4. Only after the probe succeeds does `worker_task(...)(wrapper)` call
   `register_decorated_fn`, which stores the exact entry at
   `_decorated_functions[(worker_info.name, None)]["func"]`.
5. `get_registered_workers()` materializes the production Conductor `Worker`
   from that registry record. Tests use this accessor instead of reconstructing
   a lookalike `Worker` themselves.

This applies on Linux and macOS. The fix MUST NOT force `fork`, add platform
checks, or restore a multiprocessing start-method override.

Errors for an unreconstructible rebound global MUST state that the already
module-level public name resolves to a decorator container without a supported
`__wrapped__`, `func`/`coroutine`, or deterministic embedded-function match.

## Verification Contract

The regression suite MUST use real `openai-agents==0.18.2` objects defined in
the importable `tests/unit/resources/openai_agents_entry_helpers.py` module:

- one synchronous module-level `@function_tool` matching the issue's
  `get_inventory(sku: str) -> str` reproduction;
- one valid module-level decorated context-aware tool whose first parameter is
  named exactly `context`;
- one valid module-level decorated context-aware tool whose first parameter is
  named exactly `ctx`;
- the decorated global left bound to the real `FunctionTool` container;
- a module-level spawn-child target that unpickles a complete Conductor
  `Worker`, creates a real `Task` with the fixture's input, calls
  `Worker.execute(task)`, and returns status plus output through a queue.

`tests/unit/ai/test_openai_agents_spawn_registration.py` MUST exercise the
production path rather than isolated `FunctionRef` construction:

1. Assert the installed distribution version is exactly `0.18.2`.
2. Put the real tool on a real OpenAI Agents SDK `Agent` and call
   `frameworks.serializer.serialize_agent()`, producing
   `(raw_config, workers: list[WorkerInfo])`.
3. Assert `len(workers) == 1`, `workers[0].name == "get_inventory"`, and
   `inspect.isfunction(workers[0].func)`. The value passed to registration is
   this serialized `WorkerInfo` list, never the `Agent` object.
4. Create a minimal `AgentRuntime` receiver with
   `AgentConfig(auto_start_workers=False)`. This disables worker-manager polling
   only; it does not replace registration. Remove any stale
   `_decorated_functions[("get_inventory", None)]` record before the call.
5. Call `runtime._register_framework_workers(workers)`. Do not patch
   `worker_task`, `register_decorated_fn`, `make_tool_worker`, or
   `probe_spawn_safety`. Optional spies may wrap the latter two with
   `unittest.mock.patch(..., wraps=real_function)` solely to assert each real
   implementation ran once.
6. Read `_decorated_functions[("get_inventory", None)]["func"]` and assert it
   is the actual `ToolWorkerEntry` registered by `worker_task`, with `fn_ref`
   set and `fn_direct is None`. Then call `get_registered_workers()` and select
   the `Worker` whose `task_definition_name == "get_inventory"`; assert its
   `execute_function` is that same entry. This is the precise capture point for
   the production Conductor worker.
7. Standard-pickle round-trip that complete `Worker`, then pass its bytes to a
   real `multiprocessing.get_context("spawn")` child using the helper target.
   Assert exit code zero, `COMPLETED`, and
   `output_data == {"result": "SKU ABC-123: 42 units"}`.
8. Delete `_decorated_functions[("get_inventory", None)]` in `finally` so the
   process-wide registry cannot leak into other unit tests.

Repeat the same serializer-to-registration-to-real-spawn-child path for the
decorated `context` and `ctx` fixtures. Each fixture MUST return a distinct
sentinel result, and the assertion MUST prove that the intended named callable
executed. These tests are regression guards against signature-name filtering
and against selecting a neighboring closure candidate. They MUST fail if
either first-parameter name is excluded, ignored in favor of another embedded
function, or reconstructed as a different callable.

The executable targeted verification command is:

```bash
python -m pytest tests/unit/ai/test_openai_agents_spawn_registration.py -q
```

It is run after the constrained install above. Existing broad unit-test
commands remain unchanged and are not responsible for selecting `0.18.2`.

The suite MUST retain negative coverage for locals, lambdas, bound methods,
callable instances with unpickleable state, ambiguous deep traversal, changed
child definitions (zero key matches), direct references, `__wrapped__`, and
LangChain `func`/`coroutine` reconstruction.

The Conductor UI OpenAI quickstart lives in the separate
`conductor-oss/conductor` repository. Adding a tool to that sample is a
cross-repository follow-up and is outside this repository's change scope.
