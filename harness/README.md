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

The worker logs each verdict it sees:

```text
[python_storyteller] turn 3: latest verdict done=False missing=['introduce the conflict']
[python_storyteller] turn 7: latest verdict done=True missing=[]
```

### Requirements

The LLM call runs on the Conductor server, so the provider key belongs in the **server's** environment, not the harness's. Conductor OSS enables the AI integration by default and reads `ANTHROPIC_API_KEY` into `conductor.ai.anthropic.api-key`.

### Running Locally Against Conductor OSS

```bash
# Terminal 1: start the server with the provider key in its environment
export ANTHROPIC_API_KEY=...
npm install -g @conductor-oss/conductor-cli
conductor server start

# Terminal 2: agentic testing only
export CONDUCTOR_SERVER_URL=http://localhost:8080/api
HARNESS_SDK_TESTING_ENABLED=false \
HARNESS_AGENTIC_TESTING_ENABLED=true \
HARNESS_AGENTIC_INTERVAL_SECONDS=60 \
  python3 harness/main.py
```

Open the execution in the Conductor UI to see each storyteller turn and critic call.

### Trying One Run

`try_agentic.py` runs the storyteller once, without the governors or the simulated-task workflows. It reads the same `CONDUCTOR_SERVER_URL`, `CONDUCTOR_AUTH_KEY` and `CONDUCTOR_AUTH_SECRET` variables; everything else is a flag.

```bash
# Ask the server to compile the agent. Nothing runs and no LLM is called.
# Confirms the agent API is on and shows the compiled workflow.
python3 harness/try_agentic.py plan

# Run one story: one line per sentence and critic verdict, then a report.
python3 harness/try_agentic.py run

# Repeat a concept and setting, with a shorter limit
python3 harness/try_agentic.py run --seed 3f9a1c2e --setting "a flooded library" --max-turns 10
```

`run` prints a link to the execution in the UI as soon as it starts (Cmd-click it in VS Code or iTerm2), and `--open` opens it in your browser. The link assumes the UI is served at the server URL without `/api`; if it isn't, pass `--ui-url` or set `HARNESS_UI_URL`.

A run is cancelled on Ctrl-C or after `--timeout` seconds (default 600), so it doesn't keep calling the LLM.

`run` starts things the way the harness does: `serve()` saves the agent and starts every worker it declares, then the run starts the saved agent by name.

Passing the agent object straight to `start()` doesn't work for this agent. The SDK then starts worker processes only if `_has_worker_tools()` is true, and that check ignores `stop_when`. The storyteller's only tool is the critic, which runs on the server, so its `stop_when` worker is registered but never started, and the run waits forever. It registers the agent as `python_storyteller`, the name the harness uses, so don't run it against a cluster where the harness's agentic testing is enabled. On Orkes, `--model` takes the AI integration's name before the slash.

### Agentic Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HARNESS_AGENTIC_MODEL` | `anthropic/claude-haiku-4-5` | Model for the storyteller and the critic, in `provider/model` form |
| `HARNESS_AGENTIC_INTERVAL_SECONDS` | 300 | Seconds between run starts |
| `HARNESS_AGENTIC_RUNS_PER_CONCEPT` | 3 | Runs per concept before a new one is invented and redeployed |
| `HARNESS_AGENTIC_MAX_TURNS` | 20 | Turn limit for a run whose story the critic never approves |
| `HARNESS_AGENTIC_SEED` | random | Fixed seed for a reproducible concept and setting sequence. Required to replay recordings through `mock/mockLLM` |
| `HARNESS_AGENTIC_DEBUG` | false | Print the raw message history when the worker finds no verdict |

**Cost:** each run makes two LLM calls per turn, one for the storyteller and one for the critic. Because every turn resends the growing story, input tokens grow faster than linearly with turn count. On Claude Haiku 4.5 a 15-turn run costs roughly $0.04. At the default 300-second interval that is about $10 per day. Lower the cadence before you leave it running.
