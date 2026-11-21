"""Deep agent — build a small module from a specification until its tests pass.

A coding agent of the kind people use every day, built from the deep agent
harness. The main agent plans, delegates the tests to a test-writer sub-agent
that never sees the implementation, writes the code, runs the tests and fixes
the code until they pass, then asks a reviewer sub-agent for a review.

Demonstrates:
    - A plan the main agent keeps up to date with write_todos
    - Sub-agents with their own context: the test writer sees only the
      specification, the reviewer sees only the code
    - One shared workspace stored through Conductor's file API: the tests run in
      a separate worker process that pulls the code and the tests from the
      server, not from a local disk
    - Ownership by structure: the tests live in the test writer's directory, and
      the main agent cannot change them, only make them pass
    - Long output kept out of the conversation: the full test log goes to a file
      and the model gets a short summary

Requirements:
    - Conductor server with LLM support
    - conductor.file-storage.enabled=true on the server, and its GET /api/files listing
    - CONDUCTOR_SERVER_URL=http://localhost:8080/api as environment variable
    - CONDUCTOR_AGENT_LLM_MODEL=openai/gpt-4o-mini as environment variable
    - pytest installed in the Python environment that runs this script

The tests run in a local subprocess with no sandbox. Use a container-based
executor before running code you do not trust.
"""

import os
import posixpath
import subprocess
import sys
import tempfile
from pathlib import Path

from conductor.ai.agents import Agent, AgentRuntime, EventType, tool
from conductor.ai.agents import deep_files
from conductor.ai.agents.deep import deep_agent, export_run, list_run_files, read_run_file
from conductor.ai.agents.tool import ToolContext
from settings import settings

SPECIFICATION = """\
Implement a Python module named `semver` in /src/semver.py with three functions.

parse(text: str) -> tuple
    Parse a semantic version such as "1.2.3", "1.2.3-alpha.1" or "1.2.3+build.5".
    Return (major, minor, patch, prerelease), where major, minor and patch are
    ints and prerelease is a tuple of identifiers: an identifier made only of
    digits is an int, any other identifier is a str. prerelease is () when there
    is none. Build metadata after "+" is accepted and ignored.
    Raise ValueError when the text is not a valid version: missing or extra
    numeric parts, an empty identifier, a numeric part or numeric prerelease
    identifier with a leading zero (such as "01"), or characters other than
    ASCII letters, digits, "-" and ".".

compare(a: str, b: str) -> int
    Return -1, 0 or 1 by semantic version precedence. Compare major, minor and
    patch numerically. A version with a prerelease is lower than the same
    version without one. Compare prerelease identifiers left to right: numeric
    identifiers numerically, other identifiers in ASCII order, and a numeric
    identifier is lower than a non-numeric one. When all compared identifiers
    are equal, the version with fewer identifiers is lower. Build metadata does
    not affect precedence.

bump(text: str, part: str) -> str
    part is "major", "minor" or "patch". Increment that part, set the parts to
    its right to 0, and drop the prerelease and build metadata.
    bump("1.2.3-rc.1", "minor") == "1.3.0". Raise ValueError for any other part.
"""


@tool
def run_tests(context: ToolContext = None) -> dict:
    """Run the project's tests: every test_*.py file in the workspace, against the code in /src.

    Returns:
        Whether every test passed, pytest's summary line, the end of the output
        when something failed, and the path of the file with the full log.
    """
    with tempfile.TemporaryDirectory() as tmp:
        exported = deep_files.export_files(context, tmp)
        tests = [
            p
            for p in exported
            if posixpath.basename(p).startswith("test_") and p.endswith(".py")
        ]
        if not tests:
            return {"passed": False, "error": "no test_*.py files in the workspace yet"}
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider",
             "--import-mode=importlib", *tests],
            cwd=tmp,
            env={**os.environ, "PYTHONPATH": str(Path(tmp) / "src")},
            capture_output=True,
            text=True,
            timeout=120,
        )
    log = proc.stdout + proc.stderr
    lines = [line for line in log.splitlines() if line.strip()]
    log_path = f"test-runs/run-{(context.task_id if context else 'local')[:8]}.log"
    deep_files.backend().write(context, log_path, log.encode("utf-8"))
    result = {
        "passed": proc.returncode == 0,
        "summary": lines[-1] if lines else "",
        "tests": ["/" + t for t in tests],
        "log": "/" + log_path,
    }
    if proc.returncode != 0:
        result["output_tail"] = log[-2500:]
    return result


test_writer = Agent(
    name="test_writer",
    model=settings.llm_model,
    instructions=(
        "You write pytest tests from a specification. You never see the "
        "implementation, so test the behaviour the specification promises, "
        "including its edge cases and its errors. Import the module under test "
        "with `from semver import parse, compare, bump`. Write 15 to 25 focused "
        "tests to test_semver.py with write_file. Do not implement the module."
    ),
    metadata={
        "description": (
            "Writes pytest tests for a specification without seeing the "
            "implementation. Give it the full specification."
        )
    },
)

code_reviewer = Agent(
    name="code_reviewer",
    model=settings.llm_model,
    instructions=(
        "You review code against a specification. Read the file you are given "
        "with read_file. Look for behaviour that contradicts the specification, "
        "cases the code does not handle, and code that is hard to follow. Write "
        "your findings to review.md, most important first, and reply with the "
        "three most important findings and the path of review.md."
    ),
    metadata={
        "description": (
            "Reviews a source file against a specification. Give it the path of "
            "the file and the full specification."
        )
    },
)

agent = deep_agent(
    name="coding_agent",
    model=settings.llm_model,
    instructions=(
        "You are a software engineer. Build what the user's specification "
        "describes, in this order:\n"
        "1. Ask test_writer for the tests, giving it the full specification.\n"
        "2. Write the implementation to the path the specification names.\n"
        "3. Call run_tests. While tests fail, read the failures, fix the "
        "implementation, and run them again. You cannot change the tests. If you "
        "are certain a test contradicts the specification, stop fixing and say "
        "which test and why.\n"
        "4. Ask code_reviewer to review the implementation against the "
        "specification. Apply fixes for real defects it finds and run the tests "
        "again.\n"
        "5. Reply with the final test result, what you changed after review, and "
        "anything you left open."
    ),
    tools=[run_tests],
    subagents=[test_writer, code_reviewer],
    max_turns=40,
)


if __name__ == "__main__":
    with AgentRuntime() as runtime:
        handle = runtime.start(agent, f"Build this.\n\n{SPECIFICATION}")
        print(f"Started: {handle.execution_id}\n")

        for event in handle.stream():
            if event.type == EventType.TOOL_CALL:
                print(f"  [tool_call] {event.tool_name}({str(event.args)[:100]})")
            elif event.type == EventType.TOOL_RESULT:
                print(f"  [tool_result] {event.tool_name} -> {str(event.result)[:160]}")
            elif event.type == EventType.DONE:
                print(f"\nDone: {event.output}")

        print("\nWorkspace files:")
        for path, entry in list_run_files(handle.execution_id).items():
            print(f"  /{path}  {entry.size} bytes  written by {entry.owner[:8]}")

        out = Path("workspace") / f"coding-{handle.execution_id}"
        export_run(handle.execution_id, out)
        print(f"\nExported the workspace to {out.resolve()}")
        try:
            print("--- /src/semver.py ---")
            print(read_run_file(handle.execution_id, "/src/semver.py"))
        except FileNotFoundError:
            print("(no /src/semver.py)")
