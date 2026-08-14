"""Agent Message Bus — two agents communicating via Workflow Message Queue.

Demonstrates:
    - Agent-to-agent messaging: one running agent sending messages directly
      into another running agent's WMQ via runtime.send_message()
    - Module-level tools that pick up runtime values from the environment:
      forward_to_writer reads the Writer's execution id from
      MESSAGE_BUS_WRITER_EXECUTION_ID, since a tool that closed over it could not
      be pickled to its spawned worker process
    - Parallel agent pipelines: researcher → writer running concurrently
    - Filesystem-based IPC between the main process and worker processes:
      forward_to_writer and publish each write sentinel files, so the main process
      can tell forwarding from publishing.  The barrier waits on publish — the
      Researcher forwards the last topic while the Writer is still mid-turn on it,
      so stopping at "all forwarded" would cut the final paragraph.
    - Deterministic stop: handle.stop() exits each agent's loop gracefully

How this differs from 06_sequential_pipeline:
    The >> operator in example 06 compiles a static DAG upfront — the workflow
    is defined before execution starts and the runtime automatically passes the
    output of agent A as input to agent B.  Here, both agents are independent
    running workflows.  The Researcher decides at runtime when and what to
    forward, and could in theory send to multiple Writers or skip forwarding
    conditionally.  For the basic "A feeds B" pattern example 06 is simpler;
    use this pattern when you need dynamic, conditional, or fan-out routing
    between concurrently running agents.

Scenario:
    A Researcher agent receives topics, produces bullet-point research notes,
    then forwards them to a Writer agent that turns the notes into a polished
    paragraph.  The main script only sends topics to the Researcher — the
    Researcher autonomously drives the Writer.

Requirements:
    - Conductor server with WMQ support (conductor.workflow-message-queue.enabled=true)
    - CONDUCTOR_SERVER_URL=http://localhost:8080/api as environment variable
    - CONDUCTOR_AGENT_LLM_MODEL=openai/gpt-4o-mini as environment variable
"""

import os
import shutil
import tempfile
import time
from pathlib import Path

os.environ.setdefault("CONDUCTOR_LOG_LEVEL", "WARNING")

from conductor.ai.agents import Agent, AgentRuntime, tool, wait_for_message_tool
from settings import settings

_IPC_DIR_ENV = "MESSAGE_BUS_IPC_DIR"
if _IPC_DIR_ENV in os.environ:
    _ipc_dir = Path(os.environ[_IPC_DIR_ENV])
else:
    _ipc_dir = Path(tempfile.mkdtemp(prefix="message_bus_"))
    os.environ[_IPC_DIR_ENV] = str(_ipc_dir)
_FORWARDED_DIR = _ipc_dir / "forwarded"  # one file per topic forwarded by the Researcher
_FORWARDED_DIR.mkdir(exist_ok=True)
_PUBLISHED_DIR = _ipc_dir / "published"  # one file per paragraph published by the Writer
_PUBLISHED_DIR.mkdir(exist_ok=True)

TOPICS = [
    "the impact of edge computing on cloud infrastructure",
    "why Rust is gaining adoption in systems programming",
    "how vector databases work",
]

_WRITER_EXECUTION_ID_ENV = "MESSAGE_BUS_WRITER_EXECUTION_ID"


@tool
def forward_to_writer(topic: str, notes: str) -> str:
    """Forward research notes to the Writer and signal the main process."""
    print(f"  [researcher → writer] forwarding notes on {topic!r}")
    writer_execution_id = os.environ[_WRITER_EXECUTION_ID_ENV]
    with AgentRuntime() as rt:
        rt.send_message(writer_execution_id, {"topic": topic, "notes": notes})
    (_FORWARDED_DIR / f"{time.time_ns()}.done").touch()
    return "forwarded"


def build_researcher() -> Agent:
    """Build the Researcher agent with a forward tool wired to the Writer's queue."""

    receive_topic = wait_for_message_tool(
        name="wait_for_topic",
        description="Wait for the next research topic.",
    )

    return Agent(
        name="researcher",
        model=settings.llm_model,
        tools=[receive_topic, forward_to_writer],
        max_turns=10000,
        stateful=True,
        instructions=(
            "You are a Researcher agent. Repeat indefinitely:\n"
            "1. Call wait_for_topic to receive the next message.\n"
            "2. Write three concise bullet-point research notes on the topic "
            "   using your own knowledge.\n"
            "3. Call forward_to_writer(topic, notes) with the topic and your bullet points.\n"
            "4. Return to step 1 immediately."
        ),
    )


@tool
def publish(topic: str, paragraph: str) -> str:
    """Publish the finished paragraph."""
    print(f"\n  [writer] ── {topic} ──")
    print(f"  {paragraph}\n")
    (_PUBLISHED_DIR / f"{time.time_ns()}.done").touch()
    return "published"


def build_writer() -> Agent:
    """Build the Writer agent that polishes research notes into paragraphs."""

    receive_notes = wait_for_message_tool(
        name="wait_for_notes",
        description=(
            "Wait for research notes from the Researcher agent. "
            "The payload contains 'topic' and 'notes' fields."
        ),
    )

    return Agent(
        name="writer",
        model=settings.llm_model,
        tools=[receive_notes, publish],
        max_turns=10000,
        stateful=True,
        instructions=(
            "You are a Writer agent. Repeat indefinitely:\n"
            "1. Call wait_for_notes to receive the next message.\n"
            "2. Turn the notes into a single polished paragraph (3–4 sentences).\n"
            "3. Call publish(topic, paragraph) with the topic and your paragraph.\n"
            "4. Return to step 1 immediately."
        ),
    )


def main() -> None:
    try:
        with AgentRuntime() as runtime:
            # Start the Writer first so its execution_id is available to the Researcher
            writer_handle = runtime.start(build_writer(), "Begin. Wait for research notes.")
            writer_id = writer_handle.execution_id
            print(f"Writer  started: {writer_id}")

            os.environ[_WRITER_EXECUTION_ID_ENV] = writer_id

            researcher = build_researcher()
            researcher_handle = runtime.start(researcher, "Begin. Wait for your first topic.")
            researcher_id = researcher_handle.execution_id
            print(f"Researcher started: {researcher_id}\n")

            time.sleep(4)
            print("Sending topics to Researcher...\n")
            for topic in TOPICS:
                print(f"  → {topic!r}")
                runtime.send_message(researcher_id, {"topic": topic})

            # Wait until the Writer has published every paragraph.  Gating on
            # _FORWARDED_DIR is not enough: the Researcher forwards the last topic
            # while the Writer is still mid-turn on it, so stopping there would cut
            # the final paragraph and can leave the Researcher's stop() racing an
            # in-flight iteration.
            deadline = time.monotonic() + 180
            while len(list(_PUBLISHED_DIR.iterdir())) < len(TOPICS):
                if time.monotonic() > deadline:
                    raise TimeoutError(
                        f"Writer published {len(list(_PUBLISHED_DIR.iterdir()))} of "
                        f"{len(TOPICS)} paragraphs before the deadline."
                    )
                time.sleep(0.1)

            # Deterministic stop — no stop-handling instructions needed.
            researcher_handle.stop()
            writer_handle.stop()
            researcher_handle.join(timeout=30)
            writer_handle.join(timeout=30)

            print("Done.")
    finally:
        shutil.rmtree(_ipc_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
