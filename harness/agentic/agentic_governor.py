from __future__ import annotations

import random
import threading

from conductor.ai.agents import AgentRuntime

from agentic.story_agents import STORYTELLER_NAME, build_storyteller, story_prompt
from agentic.story_concepts import StoryConcept, invent_concept, pick_setting


class AgenticGovernor:
    """Starts one storyteller run per interval, each in a randomly picked setting.

    After ``runs_per_concept`` runs it invents a new concept and redeploys the
    storyteller under the same name. The server upserts agent definitions on
    (name, version) and the compiler always emits version 1, so a redeploy
    overwrites the previous concept in place -- definitions never accumulate.
    Redeploying is plain HTTP and registers no workers, so it is safe from this
    thread; starting by name likewise skips worker registration.
    """

    def __init__(
        self,
        runtime: AgentRuntime,
        rng: random.Random,
        concept: StoryConcept,
        model: str,
        max_turns: int,
        interval_seconds: int,
        runs_per_concept: int,
    ) -> None:
        self._runtime = runtime
        self._rng = rng
        self._concept = concept
        self._model = model
        self._max_turns = max_turns
        self._interval_seconds = interval_seconds
        self._runs_per_concept = runs_per_concept
        self._runs_left = runs_per_concept
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        print(
            f"AgenticGovernor started: agent={STORYTELLER_NAME}, "
            f"interval={self._interval_seconds}s, runs_per_concept={self._runs_per_concept}"
        )
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="AgenticGovernor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        print("AgenticGovernor stopped")

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._start_run()
            self._stop_event.wait(timeout=self._interval_seconds)

    def _start_run(self) -> None:
        try:
            if self._runs_left <= 0:
                self._rotate_concept()
            setting = pick_setting(self._rng)
            handle = self._runtime.start(
                STORYTELLER_NAME, story_prompt(setting), version=1,
            )
            self._runs_left -= 1
            print(f"AgenticGovernor: started {handle.execution_id} (setting: {setting})")
        except Exception as e:
            print(f"AgenticGovernor: error starting storyteller run: {e}")

    def _rotate_concept(self) -> None:
        concept = invent_concept(self._rng)
        self._runtime.deploy(build_storyteller(concept, self._model, self._max_turns))
        self._concept = concept
        self._runs_left = self._runs_per_concept
        print(f"AgenticGovernor: deployed new concept: {concept.summary()}")
