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
