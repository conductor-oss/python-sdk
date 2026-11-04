# Python SDK Docker Harness

Two Docker targets built from the root `Dockerfile`: an **SDK build** and a **long-running worker harness**.

## Worker Harness

A self-feeding worker that runs indefinitely. On startup it registers five simulated tasks (`python_worker_0` through `python_worker_4`) and the `python_simulated_tasks_workflow`, then runs two background services:

- **WorkflowGovernor** -- starts a configurable number of `python_simulated_tasks_workflow` instances per second (default 2), indefinitely.
- **SimulatedTaskWorkers** -- five task handlers, each with a codename and a default sleep duration. Each worker supports configurable delay types, failure simulation, and output generation via task input parameters. The workflow chains them in sequence: quickpulse (1s) → whisperlink (2s) → shadowfetch (3s) → ironforge (4s) → deepcrawl (5s).

### Building Locally

```bash
docker build --target harness -t python-sdk-harness .
```

### Multiplatform Build and Push

To build for both `linux/amd64` and `linux/arm64` and push to GHCR:

```bash
# One-time: create a buildx builder if you don't have one
docker buildx create --name multiarch --use --bootstrap

# Build and push
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --target harness \
  -t ghcr.io/conductor-oss/python-sdk/harness-worker:latest \
  --push .
```

> **Note:** Multi-platform builds require `docker buildx` and a builder that supports cross-compilation. On macOS this works out of the box with Docker Desktop. On Linux you may need to install QEMU user-space emulators:
>
> ```bash
> docker run --privileged --rm tonistiigi/binfmt --install all
> ```

### Running

```bash
docker run -d \
  -e CONDUCTOR_SERVER_URL=https://your-cluster.example.com/api \
  -e CONDUCTOR_AUTH_KEY=$CONDUCTOR_AUTH_KEY \
  -e CONDUCTOR_AUTH_SECRET=$CONDUCTOR_AUTH_SECRET \
  -e HARNESS_WORKFLOWS_PER_SEC=4 \
  python-sdk-harness
```

You can also run the harness locally without Docker (from the repo root).
A virtual environment keeps dependencies isolated from your system Python:

```bash
# Check if a .venv already exists
ls .venv/bin/activate 2>/dev/null && echo "venv exists" || echo "no venv found"

# Create one if needed (one-time)
python3 -m venv .venv

# Activate it (required every time you open a new terminal)
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# Verify you're in the venv (should print the .venv path)
which python3

# Install the SDK in development mode (one-time, or after pulling new deps)
pip3 install -e .

# When you're done, deactivate the venv to restore your normal shell
deactivate
```

Once the venv is active and the SDK is installed:

```bash
export CONDUCTOR_SERVER_URL=https://your-cluster.example.com/api
export CONDUCTOR_AUTH_KEY=$CONDUCTOR_AUTH_KEY
export CONDUCTOR_AUTH_SECRET=$CONDUCTOR_AUTH_SECRET

python3 harness/main.py
```

Override defaults with environment variables as needed:

```bash
HARNESS_WORKFLOWS_PER_SEC=4 HARNESS_BATCH_SIZE=10 python3 harness/main.py
```

All resource names use a `python_` prefix so multiple SDK harnesses (C#, JS, Go, Java, etc.) can coexist on the same cluster.

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `CONDUCTOR_SERVER_URL` | yes | -- | Conductor API base URL |
| `CONDUCTOR_AUTH_KEY` | no | -- | Orkes auth key |
| `CONDUCTOR_AUTH_SECRET` | no | -- | Orkes auth secret |
| `HARNESS_WORKFLOWS_PER_SEC` | no | 2 | Workflows to start per second |
| `HARNESS_BATCH_SIZE` | no | 20 | Number of tasks each worker polls per batch |
| `HARNESS_POLL_INTERVAL_MS` | no | 100 | Milliseconds between poll cycles |
| `HARNESS_SDK_TESTING_ENABLED` | no | true | Run the simulated-task workflows described above |
| `HARNESS_AGENTIC_TESTING_ENABLED` | no | false | Run the agentic storyteller described below |

## Agentic Testing

Off by default. When enabled, the harness also exercises the agent runtime. It compiles a `python_storyteller` agent from a randomly chosen story concept (protagonist, conflict, resolution, constraint, tone), serves the agent's `python_storyteller_stop_when` worker from this process, and starts a run on an interval, each in a randomly chosen setting.

Each run adds one sentence per turn. After every sentence the storyteller calls a `python_story_critic` sub-agent, which returns a JSON verdict: whether the story meets the concept, and what is still missing. The `stop_when` worker ends the loop once the critic approves. If the critic never approves, `HARNESS_AGENTIC_MAX_TURNS` ends it. Either way the run completes. After `HARNESS_AGENTIC_RUNS_PER_CONCEPT` runs, the harness invents a new concept and redeploys over the same name, which replaces version 1 in place rather than adding versions.

By default the harness edits the deployed definition so that `stop_when` sees each verdict on the turn the critic gives it, the same edit as `try_agentic.py run --stop-same-turn` (see [below](#--stop-same-turn)). Every deploy undoes the edit, so the governor re-applies it after the first deploy and after each concept rotation, before it starts the next run. If the edit fails, the governor logs a warning, does not start that run, and tries again at the next interval. Set `HARNESS_AGENTIC_STOP_SAME_TURN=false` to run with the definition as compiled. The proper fix is described under [`--stop-same-turn`](#--stop-same-turn).

The concept is compiled into the agent's instructions and the critic's rubric, so changing it means redeploying. The setting is only in each run's prompt, so it varies every run without a redeploy.

The worker logs each verdict it sees:

```text
[python_storyteller] turn 3: latest verdict done=False missing=['introduce the conflict']
[python_storyteller] turn 7: latest verdict done=True missing=[]
```

Between starts, the governor checks the last run every 15 seconds and reports it as soon as it has finished, read from its execution record. The outcome is followed by the story:

```text
AgenticGovernor: run <id> COMPLETED after 10 turn(s): stopped on the approving turn 10; stop_when rewired; 10 critic call(s); storyteller tokens 27,163 in / 1,825 out https://<ui>/execution/<id>
  story (approved by the critic on turn 10):
    Twelve-year-old Maya clutched her canvas bag of lost keys as the ferry horn wailed through the
    suffocating fog. ...
AgenticGovernor: run <id> FAILED after 0 turn(s): No such model configured or enabled. integration: chatbotsxz, model: claude-haiku-4-5 https://<ui>/execution/<id>
```

The story is read from the execution, not the workflow output: a run that stops on the approving turn has no story in its output (see [Known Issues](#known-issues)).

With the compiled wiring, a 6-turn story's run says `COMPLETED after 7 turn(s): approved on turn 6, stopped 1 turn(s) later; stop_when as compiled; 6 critic call(s); storyteller tokens 14,034 in / 1,089 out`: the extra turn cost 3,201 input tokens.

Each run is reported once. Checks that find it still running are silent. If it hasn't finished by the next start, that start reports it as still running and stops checking it.

A run can't finish correctly once the harness that started it stops: its `stop_when` worker is gone, and the next harness deploys a new concept, which gives the run a different critic from its next turn on. So on shutdown the governor terminates its last run if it hasn't finished, and on startup, before deploying, the harness terminates any `python_storyteller` run still RUNNING (one left by a crash). Run only one agentic harness per cluster: each one deploys `python_storyteller` and `python_story_critic` with its own concept.

### Requirements

So far this has been tested only against Orkes Conductor 5.6.0-rc4 and 5.6.0-rc6, with both `try_agentic.py` and the harness.

The LLM calls run on the Conductor server, so the harness needs no provider key. The key is stored in an AI integration on the Orkes cluster:

- The cluster needs an AI integration for the provider, holding its API key, with the model enabled.
- `HARNESS_AGENTIC_MODEL` takes the form `<integration name>/<model>`. The default, `anthropic/claude-haiku-4-5`, works only if the integration is named `anthropic`.
- If the integration or the model is missing, the server fails the storyteller's first LLM task with a terminal error when it schedules it.

### Running Against Orkes Conductor

```bash
export CONDUCTOR_SERVER_URL=https://your-cluster.example.com/api
export CONDUCTOR_AUTH_KEY=$CONDUCTOR_AUTH_KEY
export CONDUCTOR_AUTH_SECRET=$CONDUCTOR_AUTH_SECRET

# Agentic testing only
HARNESS_SDK_TESTING_ENABLED=false \
HARNESS_AGENTIC_TESTING_ENABLED=true \
HARNESS_AGENTIC_MODEL=<integration name>/claude-haiku-4-5 \
  python3 harness/main.py
```

Open the execution in the Orkes UI to see each storyteller turn and critic call.

### Trying One Run

`try_agentic.py` runs the storyteller once, without the governors or the simulated-task workflows. It reads the same `CONDUCTOR_SERVER_URL`, `CONDUCTOR_AUTH_KEY` and `CONDUCTOR_AUTH_SECRET` variables; everything else is a flag.

```bash
# Ask the server to compile the agent. Nothing runs and no LLM is called.
# Confirms the agent API is on and shows the compiled workflow.
python3 harness/try_agentic.py plan

# Run one story, then report each turn's sentence and critic verdict, tokens, and the story.
python3 harness/try_agentic.py run

# Repeat a concept and setting, with a shorter limit
python3 harness/try_agentic.py run --seed 3f9a1c2e --setting "a flooded library" --max-turns 10

# Stop on the turn the critic approves, saving one storyteller call (see below)
python3 harness/try_agentic.py run --stop-same-turn
```

The report is built from the execution record after the run, not from streamed events: Orkes 5.6.0-rc4 streams no tool-call events, so live per-turn lines appear only on servers that do. The story it prints is the text the critic approved, exactly as the critic judged it. The storyteller's own final reply can add commentary such as a checklist of the requirements.

`run` prints a link to the execution in the UI as soon as it starts (Cmd-click it in VS Code or iTerm2), and `--open` opens it in your browser. The link is the server URL without `/api`, which is where Orkes serves the UI.

A run is cancelled on Ctrl-C or after `--timeout` seconds (default 600), so it doesn't keep calling the LLM.

`run` starts things the way the harness does: `serve()` saves the agent and starts every worker it declares, then the run starts the saved agent by name.

Passing the agent object straight to `start()` doesn't work for this agent. The SDK then starts worker processes only if `_has_worker_tools()` is true, and that check ignores `stop_when`. The storyteller's only tool is the critic, which runs on the server, so its `stop_when` worker is registered but never started, and the run waits forever.

`run` registers the agent as `python_storyteller`, the name the harness uses, so don't run it against a cluster where the harness's agentic testing is enabled. `--model` takes the AI integration's name before the slash, as `HARNESS_AGENTIC_MODEL` does.

#### `--stop-same-turn`

`stop_when` decides whether the loop ends, and that decision depends on the critic's verdict: the result of a tool call. As compiled, `stop_when` reads the storyteller LLM call's input messages, a snapshot taken before that turn's critic call, so it sees each verdict one turn late and the loop runs one extra storyteller call after the critic approves. That call carries the whole conversation, so it is the most expensive turn.

`--stop-same-turn` edits the stored workflow definition after `serve()` deploys it and before the run starts: it points `stop_when` at `_last_tool_results`, a workflow variable that already holds every tool result so far and is updated after the critic and before `stop_when`. The loop then stops on the approving turn. The edit is made on the raw JSON so no field is lost, it refuses to write a definition without its agent markers in `metadata`, and it re-reads the definition to confirm. Every deploy regenerates the definition, so the edit has to be re-applied each time; the report's `stop_when:` line says which wiring the run actually used. The harness applies the same edit by default; see `HARNESS_AGENTIC_STOP_SAME_TURN`. The edit reuses the `messages` input because the Python SDK's `stop_when` worker passes only `result`, `messages` and `iteration` to the function and drops any other input. See `agentic/stop_wiring.py`.

The proper fix: single-agent `stop_when` can't see this turn's tool results; add a `tool_results` input in the server's compiler and expose it in each SDK's `stop_when` context. SWARM handoff checks already receive `${workflow.variables._last_tool_results}` under that name, so the server has precedent for this wiring.

### Known Issues

Problems found while building agentic testing, and how the harness works around them. Observed on Orkes Conductor 5.6.0-rc4 and 5.6.0-rc6, which both use Conductor OSS 3.32.1.

**Server**

- **`stop_when` sees tool results one turn late.** See [`--stop-same-turn`](#--stop-same-turn). Worked around by the stop_when edit, which is on by default.
- **A run that ends on a tool call loses its output.** When the loop stops on a turn where the LLM called a tool, the `synth_output` step builds the workflow output from that turn's tool calls, and their inputs come out empty: `[{"name":"story_critic","inputs":{}}]`. The step's script calls `JSON.stringify` on the inputs, which arrive as Java maps, and GraalJS serializes a Java map as `{}`. Reproduced with the server's own `GraalJSEvaluator`. With the stop_when edit every approved run ends this way, so the harness and `try_agentic.py` read the story from the execution record.
- **Orkes 5.6.0-rc4 streams no tool-call events**, so reports are built from the execution record.

**Python SDK**

- **`start(agent)` and `run(agent)` never start the `stop_when` worker** of an agent with no local tools: `_has_worker_tools()` ignores `stop_when`, so the run waits at `stop_when` forever. Workaround: `serve()`, then start by name.
- **The `stop_when` worker drops every task input except `result`, `messages` and `iteration`**, which is why the stop_when edit reuses `messages`.
- **`run(on_event=...)` ignores `timeout`.** `try_agentic.py` reads the event stream on a thread with its own deadline.
- **Raw responses (`_preload_content=False`) crash on the httpx transport**, which has `status_code` where the SDK reads `status`. Workaround: `call_api(..., response_type="object")`.
- **`examples/agents/kitchen_sink.py`'s `stop_when` predicate never stops the loop.** Its first parameter is `messages`, but it receives the context dict, so `messages[-1]` raises `KeyError`, which the worker logs and treats as "continue".
- Found while reading the code, not hit by the harness: `output_type` with a dataclass produces no schema, and `_type_to_json_schema(str | None)` returns `{}`.

**Conductor CLI**

- **It drops `metadata` from workflow definitions**, so round-tripping an agent definition through it would remove the agent markers and make the server treat it as a plain workflow. `agentic/stop_wiring.py` edits the raw JSON instead.

### Agentic Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HARNESS_AGENTIC_MODEL` | `anthropic/claude-haiku-4-5` | Model for the storyteller and the critic, in `<integration name>/<model>` form |
| `HARNESS_AGENTIC_INTERVAL_SECONDS` | 300 | Seconds between run starts |
| `HARNESS_AGENTIC_RUNS_PER_CONCEPT` | 3 | Runs per concept before a new one is invented and redeployed |
| `HARNESS_AGENTIC_MAX_TURNS` | 20 | Turn limit for a run whose story the critic never approves |
| `HARNESS_AGENTIC_STOP_SAME_TURN` | true | Edit the deployed definition so `stop_when` sees the critic's verdict on the same turn. A run is not started while the edit fails |
| `HARNESS_AGENTIC_SEED` | random | Fixed seed for a reproducible concept and setting sequence |
| `HARNESS_AGENTIC_DEBUG` | false | Print the raw message history when the worker finds no verdict |

**Cost:** each run makes two LLM calls per turn, one for the storyteller and one for the critic. Because every turn resends the growing story, input tokens grow faster than linearly with turn count. On Claude Haiku 4.5 a 15-turn run costs roughly $0.04. At the default 300-second interval that is about $10 per day. Lower the cadence before you leave it running.
