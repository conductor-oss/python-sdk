from __future__ import annotations

import os
import random
import threading

from conductor.ai.agents import AgentRuntime
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api.metadata_resource_api import MetadataResourceApi
from conductor.client.http.api.workflow_resource_api import WorkflowResourceApi
from conductor.client.http.api_client import ApiClient

from agentic.agentic_governor import AgenticGovernor, terminate_running_runs
from agentic.story_agents import STORYTELLER_NAME, build_storyteller
from agentic.story_concepts import invent_concept
from harness_env import env_bool_or_default, env_int_or_default, env_str_or_default


class AgenticTesting:
    """Exercises the agent runtime: compiles a randomized storyteller agent, serves its
    stop_when worker from this process, and periodically starts runs that add one
    sentence per turn until a critic agent approves the story or max_turns runs out.
    Either way the run completes."""

    def __init__(self, configuration: Configuration) -> None:
        self._configuration = configuration
        self._model = env_str_or_default("HARNESS_AGENTIC_MODEL", "anthropic/claude-haiku-4-5")
        self._max_turns = env_int_or_default("HARNESS_AGENTIC_MAX_TURNS", 20)
        self._interval_seconds = env_int_or_default("HARNESS_AGENTIC_INTERVAL_SECONDS", 300)
        self._runs_per_concept = env_int_or_default("HARNESS_AGENTIC_RUNS_PER_CONCEPT", 3)
        # Rewire stop_when so it sees the critic's verdict on the turn the critic gives it,
        # saving one storyteller call per run. See agentic/stop_wiring.py.
        self._stop_same_turn = env_bool_or_default("HARNESS_AGENTIC_STOP_SAME_TURN", True)
        # A fixed seed reproduces the same concept and setting sequence, which is what
        # recording once and replaying through mock/mockLLM requires.
        self._rng = random.Random(os.environ.get("HARNESS_AGENTIC_SEED") or None)
        self._runtime: AgentRuntime | None = None
        self._governor: AgenticGovernor | None = None
        self._stopped = threading.Event()

    def prepare(self) -> None:
        """Deploy the first concept and fork the storyteller's worker processes. Starts no threads."""
        self._runtime = AgentRuntime(configuration=self._configuration)
        api_client = ApiClient(self._configuration)
        # serve() deploys a new concept, and a run left by a previous harness would get its
        # critic from the next turn on, so end any such run first.
        terminate_running_runs(WorkflowResourceApi(api_client))
        concept = invent_concept(self._rng)
        self._runtime.serve(
            build_storyteller(concept, self._model, self._max_turns), blocking=False,
        )
        print(f"AgenticTesting: serving {STORYTELLER_NAME} on {self._model}, "
              f"first concept: {concept.summary()}")
        self._governor = AgenticGovernor(
            self._runtime, self._rng, concept, self._model, self._max_turns,
            self._interval_seconds, self._runs_per_concept,
            api_client=api_client,
            server_url=self._configuration.host,
            metadata_api=MetadataResourceApi(api_client) if self._stop_same_turn else None,
        )

    def start(self) -> None:
        """Start the governor thread. Call only after every module's prepare()."""
        self._governor.start()

    def stop(self) -> None:
        if self._governor is not None:
            self._governor.stop()
        if self._runtime is not None:
            self._runtime.shutdown()
        self._stopped.set()

    def wait(self) -> None:
        """Block until stop() is called."""
        self._stopped.wait()
