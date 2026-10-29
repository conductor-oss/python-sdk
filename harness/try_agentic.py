"""Run the agentic storyteller once, locally, without the harness governors.

    python3 harness/try_agentic.py plan    # server compiles the agent; nothing runs
    python3 harness/try_agentic.py run     # one story, live progress, then a report

Server and auth come from CONDUCTOR_SERVER_URL, CONDUCTOR_AUTH_KEY and
CONDUCTOR_AUTH_SECRET. Everything else is a flag; see --help on each command.

Runs register the agent under the same name the harness uses (python_storyteller),
so don't point this at a cluster where the harness's agentic testing is running.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import secrets
import sys
import textwrap
import threading
import webbrowser
from typing import Any, Optional

from conductor.ai.agents import AgentRuntime
from conductor.client.configuration.configuration import Configuration

from agentic.story_agents import (
    CRITIC_TOOL_NAME,
    STORYTELLER_NAME,
    build_storyteller,
    find_verdict,
    story_prompt,
)
from agentic.story_concepts import StoryConcept, invent_concept, pick_setting
from harness_env import env_str_or_default

DEFAULT_MODEL = "anthropic/claude-haiku-4-5"
WRAP = 88


def main() -> int:
    args = parse_args()
    if args.verbose:
        # Only the SDK's loggers: HTTP-library logs are noisy at INFO, and at DEBUG
        # they can print request headers, which carry the auth token.
        logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
        logging.getLogger("conductor").setLevel(logging.INFO)
    if getattr(args, "debug", False):
        # Read by the stop_when worker, which runs in a separate process.
        os.environ["HARNESS_AGENTIC_DEBUG"] = "true"

    seed = args.seed or secrets.token_hex(4)
    rng = random.Random(seed)
    concept = invent_concept(rng)
    configuration = Configuration()
    args.server = configuration.host

    print(f"server:  {configuration.host}")
    print(f"model:   {args.model}")
    print(f"seed:    {seed}   (repeat this concept with --seed {seed})")
    print(f"concept:\n{textwrap.indent(concept.rubric(), '  ')}")

    runtime = AgentRuntime(configuration=configuration)
    try:
        return args.handler(args, runtime, rng, concept)
    finally:
        runtime.shutdown()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--model", default=env_str_or_default("HARNESS_AGENTIC_MODEL", DEFAULT_MODEL),
                        help="provider/model; on Orkes the provider is the AI integration's name "
                             f"(default: $HARNESS_AGENTIC_MODEL or {DEFAULT_MODEL})")
    common.add_argument("--seed", help="seed for the concept and setting (default: random, printed)")
    common.add_argument("--max-turns", type=int, default=20, help="turn limit (default: 20)")
    common.add_argument("--verbose", action="store_true",
                        help="show the SDK's INFO logs, e.g. which workers the server asked for")

    plan = commands.add_parser("plan", parents=[common],
                               help="compile the storyteller on the server and show the result")
    plan.add_argument("--out", help="also write the full compile response to this JSON file")
    plan.set_defaults(handler=run_plan)

    run = commands.add_parser("run", parents=[common], help="run one story and report the result")
    run.add_argument("--setting", help="story setting (default: random pick)")
    run.add_argument("--timeout", type=int, default=600,
                     help="seconds before the run is cancelled (default: 600)")
    run.add_argument("--quiet", action="store_true", help="no live progress, just the report")
    run.add_argument("--open", action="store_true",
                     help="open the execution in your browser as soon as the run starts")
    run.add_argument("--ui-url", default=os.environ.get("HARNESS_UI_URL"),
                     help="UI address for execution links (default: $HARNESS_UI_URL, else the "
                          "server URL without /api)")
    run.add_argument("--debug", action="store_true",
                     help="the stop_when worker prints raw message history when it finds no verdict")
    run.set_defaults(handler=run_story)

    return parser.parse_args()


# ── plan ────────────────────────────────────────────────────────────────


def run_plan(args: argparse.Namespace, runtime: AgentRuntime, rng: random.Random,
             concept: StoryConcept) -> int:
    agent = build_storyteller(concept, args.model, args.max_turns)
    try:
        response = runtime.plan(agent)
    except Exception as e:
        print(f"\nThe server did not compile the agent: {type(e).__name__}: {e}")
        if "404" in str(e):
            print("A 404 usually means the agent API is off (conductor.integrations.ai.enabled).")
        elif "Connection" in str(e):
            print("Nothing answered at that address. Check CONDUCTOR_SERVER_URL.")
        return 1

    workflow = _field(response, "workflowDef", "workflow_def") or {}
    workers = _field(response, "requiredWorkers", "required_workers") or []
    print(f"\nagent API: OK, compiled {_field(workflow, 'name')} v{_field(workflow, 'version')}")
    print(f"workers this process must serve: {', '.join(workers) or '(none)'}\n")
    _print_tasks(_field(workflow, "tasks") or [], depth=0)

    if args.out:
        with open(args.out, "w") as f:
            json.dump(response, f, indent=2, default=str)
        print(f"\nfull compile response written to {args.out}")
    return 0


def _print_tasks(tasks: list, depth: int) -> None:
    pad = "  " * depth
    for task in tasks:
        task_type = _field(task, "type") or "?"
        line = f"{pad}- {task_type:<22} {_field(task, 'taskReferenceName') or ''}"
        if task_type == "LLM_CHAT_COMPLETE":
            line += _describe_llm_task(_field(task, "inputParameters") or {})
        print(line)
        for case, branch in (_field(task, "decisionCases") or {}).items():
            print(f"{pad}    case {case}:")
            _print_tasks(branch, depth + 3)
        if _field(task, "defaultCase"):
            print(f"{pad}    default:")
            _print_tasks(_field(task, "defaultCase"), depth + 3)
        _print_tasks(_field(task, "loopOver") or [], depth + 1)
        for branch in _field(task, "forkTasks") or []:
            _print_tasks(branch, depth + 1)
        sub = (_field(task, "subWorkflowParam") or {}).get("workflowDefinition")
        if isinstance(sub, dict):
            print(f"{pad}    sub-workflow {sub.get('name')}:")
            _print_tasks(sub.get("tasks") or [], depth + 3)


def _describe_llm_task(inputs: dict) -> str:
    text = (f"  [{inputs.get('llmProvider')}/{inputs.get('model')}"
            f"  jsonOutput={bool(inputs.get('jsonOutput'))}"
            f"  outputSchema={'yes' if inputs.get('outputSchema') else 'no'}")
    tools = inputs.get("tools")
    if isinstance(tools, list) and tools:
        text += "  tools=" + ", ".join(f"{t.get('name')}({t.get('type')})" for t in tools)
    return text + "]"


# ── run ─────────────────────────────────────────────────────────────────


def run_story(args: argparse.Namespace, runtime: AgentRuntime, rng: random.Random,
              concept: StoryConcept) -> int:
    setting = args.setting or pick_setting(rng)
    print(f"setting: {setting}\n")

    agent = build_storyteller(concept, args.model, args.max_turns)
    # The harness's way: serve() saves the agent and starts every worker the agent declares,
    # then the run starts the saved agent by name. Don't pass the agent object to start():
    # the SDK then starts worker processes only if _has_worker_tools() is true, which
    # ignores stop_when, so this agent's stop_when worker would never run.
    runtime.serve(agent, blocking=False)
    handle = runtime.start(STORYTELLER_NAME, story_prompt(setting), version=1)
    link = _execution_url(args.ui_url or args.server, handle.execution_id)
    print(f"execution: {handle.execution_id}")
    print(f"view:      {link}")
    if args.open and not webbrowser.open(link):
        print("           (could not open a browser; Cmd-click the link instead)")
    print()

    # handle.stream() has no timeout of its own (and run(on_event=...) ignores the one it
    # accepts), so read it on a thread and enforce the deadline here.
    stream = handle.stream()
    progress = _Progress(quiet=args.quiet)
    finished = threading.Event()

    def consume() -> None:
        try:
            for event in stream:
                progress.on_event(event)
        except Exception as e:
            print(f"  event stream failed: {type(e).__name__}: {e}")
        finally:
            finished.set()

    threading.Thread(target=consume, name="try-agentic-stream", daemon=True).start()
    try:
        if not finished.wait(timeout=args.timeout):
            handle.cancel(f"try_agentic.py: no result after {args.timeout}s")
            print(f"\nNo result after {args.timeout}s; cancelled {handle.execution_id}.")
            return 1
    except KeyboardInterrupt:
        handle.cancel("try_agentic.py: interrupted")
        print(f"\nInterrupted; cancelled {handle.execution_id}.")
        return 130

    return _report(handle, stream, progress, link)


class _Progress:
    """Turns stream events into one line per sentence and one per critic verdict."""

    def __init__(self, quiet: bool) -> None:
        self.quiet = quiet
        self.story = ""
        self.verdicts: list[Optional[dict]] = []

    def on_event(self, event: Any) -> None:
        kind = str(getattr(event.type, "value", event.type))
        is_critic = CRITIC_TOOL_NAME in (event.tool_name or "")
        if kind == "tool_call" and is_critic:
            story = str((event.args or {}).get("request", ""))
            added = story[len(self.story):].strip() if story.startswith(self.story) else story
            self.story = story
            self._say(f"  turn {len(self.verdicts) + 1:>2}  + {added}")
        elif kind == "tool_result" and is_critic:
            verdict = find_verdict(event.result)
            self.verdicts.append(verdict)
            self._say(f"           critic: {_describe_verdict(verdict)}")
        elif kind == "error":
            self._say(f"  error: {event.content}")

    def _say(self, line: str) -> None:
        if not self.quiet:
            limit = WRAP + 40
            print(line if len(line) <= limit else line[:limit - 4] + " ...")


def _report(handle: Any, stream: Any, progress: _Progress, link: str) -> int:
    try:
        result = stream.get_result()
        status = str(getattr(result.status, "value", result.status))
        output, usage, error = result.output, result.token_usage, result.error
    except Exception:
        snapshot = handle.get_status()
        status, output, usage, error = snapshot.status, snapshot.output, None, snapshot.reason

    approved = any(v is not None and v.get("done") is True for v in progress.verdicts)
    print("\n" + "=" * WRAP)
    print(f"status:       {status}")
    print(f"execution:    {handle.execution_id}")
    print(f"view:         {link}")
    print(f"critic calls: {len(progress.verdicts)}   approved: "
          f"{'yes' if approved else 'no (stopped at the turn limit, or failed)'}")
    if usage is not None:
        print(f"tokens:       {usage.prompt_tokens} in, {usage.completion_tokens} out, "
              f"{usage.total_tokens} total")
    if error:
        print(f"error:        {error}")

    story = output if isinstance(output, str) and output.strip() else progress.story
    print("\nstory:\n")
    print(textwrap.fill(story, WRAP) if story else "(no story text came back)")
    return 0 if status.upper() == "COMPLETED" else 1


def _describe_verdict(verdict: Optional[dict]) -> str:
    if verdict is None:
        return "no JSON verdict found in its reply"
    if verdict.get("done") is True:
        return "done"
    return f"not done, missing: {verdict.get('missing')}"


def _execution_url(base: str, execution_id: str) -> str:
    """UI link for an execution. Agent runs use the normal execution page in both the
    OSS and Orkes UIs; the agent view is a tab on it. Printed as a plain URL, which
    VS Code's terminal and iTerm2 make Cmd-clickable and which survives logs and
    copy-paste."""
    base = base.rstrip("/")
    if base.endswith("/api"):
        base = base[: -len("/api")]
    return f"{base}/execution/{execution_id}"


def _field(obj: Any, *names: str) -> Any:
    """Read a key from a dict response, or an attribute from a model object."""
    for name in names:
        value = obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)
        if value is not None:
            return value
    return None


if __name__ == "__main__":
    # The guard is required: on macOS worker processes are spawned, and each one
    # re-imports this file as a module.
    sys.exit(main())
