from __future__ import annotations

import random
import textwrap
import threading
import time

from conductor.ai.agents import AgentRuntime
from conductor.client.http.api.metadata_resource_api import MetadataResourceApi
from conductor.client.http.api_client import ApiClient

from agentic.run_report import RunSummary, execution_url, fetch_execution, summarize
from agentic.stop_wiring import rewire_stop_when
from agentic.story_agents import STORYTELLER_NAME, build_storyteller, story_prompt
from agentic.story_concepts import StoryConcept, invent_concept, pick_setting

_TERMINAL_STATUSES = ("COMPLETED", "FAILED", "TERMINATED", "TIMED_OUT")
# How often the governor checks whether the last run has finished, between starts.
_POLL_SECONDS = 15


class AgenticGovernor:
    """Starts one storyteller run per interval, each in a randomly picked setting.

    After ``runs_per_concept`` runs it invents a new concept and redeploys the
    storyteller under the same name. The server upserts agent definitions on
    (name, version) and the compiler always emits version 1, so a redeploy
    overwrites the previous concept in place -- definitions never accumulate.
    Redeploying is plain HTTP and registers no workers, so it is safe from this
    thread; starting by name likewise skips worker registration.

    With a ``metadata_api``, it also rewires stop_when so it sees the critic's verdict on
    the same turn (see agentic/stop_wiring.py). Every deploy regenerates the definition and
    undoes the edit, so the edit is due after the initial deploy and after each rotation,
    and is applied before the next run starts. If it fails, that run is not started and the
    edit is tried again at the next interval.

    Between starts it checks the last run every ``_POLL_SECONDS`` and reports it as soon as it
    has finished, read from its execution record: the outcome and the story. Checks that find
    it still running are silent. If it hasn't finished by the next start, that start reports
    it as still running and stops tracking it. Each run is reported once.
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
        api_client: ApiClient,
        server_url: str,
        metadata_api: MetadataResourceApi | None = None,
    ) -> None:
        self._runtime = runtime
        self._rng = rng
        self._concept = concept
        self._model = model
        self._max_turns = max_turns
        self._interval_seconds = interval_seconds
        self._runs_per_concept = runs_per_concept
        self._runs_left = runs_per_concept
        self._api_client = api_client
        self._server_url = server_url
        self._last_run: str | None = None
        self._metadata_api = metadata_api
        # The caller deployed the first concept just before creating the governor.
        self._rewire_due = metadata_api is not None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        print(
            f"AgenticGovernor started: agent={STORYTELLER_NAME}, "
            f"interval={self._interval_seconds}s, runs_per_concept={self._runs_per_concept}, "
            f"stop_same_turn={self._metadata_api is not None}"
        )
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="AgenticGovernor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        if self._last_run is not None:
            # Its stop_when worker stops with this process, so a run still in progress
            # waits at stop_when until a harness serves it again.
            print(f"AgenticGovernor: last run not yet reported, possibly still running: "
                  f"{self._last_run}")
        print("AgenticGovernor stopped")

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._start_run()
            self._wait_for_next_start()

    def _wait_for_next_start(self) -> None:
        """Wait out the interval, reporting the last run as soon as a check finds it finished."""
        deadline = time.monotonic() + self._interval_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or self._stop_event.wait(timeout=min(_POLL_SECONDS, remaining)):
                return
            if self._last_run is not None:
                self._report_last_run(final=False)

    def _start_run(self) -> None:
        self._report_last_run()
        try:
            if self._runs_left <= 0:
                self._rotate_concept()
            if self._rewire_due and not self._rewire_stop_when():
                return
            setting = pick_setting(self._rng)
            handle = self._runtime.start(
                STORYTELLER_NAME, story_prompt(setting), version=1,
            )
            self._runs_left -= 1
            self._last_run = handle.execution_id
            print(f"AgenticGovernor: started {handle.execution_id} (setting: {setting}) "
                  f"{execution_url(self._server_url, handle.execution_id)}")
        except Exception as e:
            print(f"AgenticGovernor: error starting storyteller run: {e}")

    def _report_last_run(self, final: bool = True) -> None:
        """Report the last run and forget it if it has finished. Between starts (``final`` False)
        say nothing otherwise, so it is checked again; before a start, also report a run that is
        still going or can't be fetched, and forget it."""
        execution_id = self._last_run
        if execution_id is None:
            return
        link = execution_url(self._server_url, execution_id)
        try:
            summary = summarize(fetch_execution(self._api_client, execution_id))
        except Exception as e:
            if final:
                self._last_run = None
                print(f"AgenticGovernor: could not fetch run {execution_id} to report on it: {e} {link}")
            return
        if summary.status.upper() in _TERMINAL_STATUSES:
            self._last_run = None
            print(f"AgenticGovernor: run {execution_id} {_describe_outcome(summary)} {link}")
            if summary.story:
                # From the execution, not the workflow output: a run that stops on the approving
                # turn ends on a critic call, so its output holds no story text.
                print(f"  story ({summary.story_source}):")
                print(textwrap.fill(summary.story, 100, initial_indent="    ", subsequent_indent="    "))
        elif final:
            self._last_run = None
            print(f"AgenticGovernor: run {execution_id} still {summary.status} "
                  f"after {len(summary.turns)} turn(s); not reporting it again {link}")

    def _rotate_concept(self) -> None:
        concept = invent_concept(self._rng)
        self._runtime.deploy(build_storyteller(concept, self._model, self._max_turns))
        self._concept = concept
        self._runs_left = self._runs_per_concept
        self._rewire_due = self._metadata_api is not None
        print(f"AgenticGovernor: deployed new concept: {concept.summary()}")

    def _rewire_stop_when(self) -> bool:
        """Apply the stop_when edit. Returns False, after logging why, if the run must not start."""
        try:
            changed = rewire_stop_when(self._metadata_api, STORYTELLER_NAME)
        except Exception as e:
            print(f"AgenticGovernor: WARNING: could not rewire stop_when, not starting this run; "
                  f"retrying at the next interval: {e}")
            return False
        self._rewire_due = False
        print("AgenticGovernor: rewired stop_when to see the critic's verdict on the same turn"
              + ("" if changed else " (it already was)"))
        return True


def _describe_outcome(summary: RunSummary) -> str:
    """One line: status and turns, then the failure reason or the approval details."""
    turns = len(summary.turns)
    outcome = f"{summary.status} after {turns} turn(s)"
    if summary.status.upper() != "COMPLETED":
        return f"{outcome}: {summary.reason or 'no reason given'}"
    if summary.approved_on is None:
        approval = "critic never approved"
    elif summary.approved_on == summary.turns[-1].number:
        approval = f"stopped on the approving turn {summary.approved_on}"
    else:
        extra = summary.turns[-1].number - summary.approved_on
        approval = f"approved on turn {summary.approved_on}, stopped {extra} turn(s) later"
    wiring = {True: "rewired", False: "as compiled", None: "unknown"}[summary.stop_when_same_turn]
    tokens_in, tokens_out = summary.storyteller_tokens
    return (f"{outcome}: {approval}; stop_when {wiring}; "
            f"{len(summary.critic_execution_ids)} critic call(s); "
            f"storyteller tokens {tokens_in:,} in / {tokens_out:,} out")
