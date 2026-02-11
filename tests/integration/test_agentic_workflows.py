"""
E2E tests for agentic workflow examples.

Runs all examples in examples/agentic_workflows/ against a live Conductor server
and validates workflow completion, task outputs, and expected behavior.

Requirements:
    - Conductor server with AI/LLM support
    - LLM provider named 'openai' with model 'gpt-4o-mini' configured
    - export CONDUCTOR_SERVER_URL=http://localhost:7001/api

Run:
    python tests/integration/test_agentic_workflows.py
    python -m pytest tests/integration/test_agentic_workflows.py -v
"""

import importlib.util
import os
import sys
import time
import unittest

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.orkes_clients import OrkesClients


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_example(module_name: str, file_path: str):
    """Import an example module by file path without executing main()."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _poll_workflow(workflow_client, workflow_id: str, timeout: int = 120, interval: int = 2):
    """Poll a workflow until it reaches a terminal state or times out.

    Returns the final workflow run object.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        run = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)
        if run.status in ("COMPLETED", "FAILED", "TIMED_OUT", "TERMINATED"):
            return run
        time.sleep(interval)
    # One final fetch
    return workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)


def _wait_for_task(workflow_client, workflow_id: str, task_ref: str,
                   expected_status: str = "IN_PROGRESS", timeout: int = 30):
    """Wait until a specific task reaches the expected status."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        run = workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)
        for task in (run.tasks or []):
            if (task.reference_task_name == task_ref and
                    task.status == expected_status):
                return run
        time.sleep(1)
    return workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)


def _task_map(run):
    """Build a dict mapping reference_task_name -> task for easy lookup."""
    result = {}
    for task in (run.tasks or []):
        result[task.reference_task_name] = task
    return result


def _cleanup_workflow(workflow_client, workflow_id: str):
    """Best-effort delete a workflow."""
    try:
        workflow_client.delete_workflow(workflow_id=workflow_id)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "examples", "agentic_workflows")


class AgenticWorkflowTests(unittest.TestCase):
    """E2E tests for all agentic workflow examples."""

    @classmethod
    def setUpClass(cls):
        cls.config = Configuration()
        cls.clients = OrkesClients(configuration=cls.config)
        cls.workflow_executor = cls.clients.get_workflow_executor()
        cls.workflow_client = cls.clients.get_workflow_client()
        cls.task_client = cls.clients.get_task_client()

        # Discover workers from ALL example modules so one TaskHandler covers them all.
        # We import each module here so @worker_task decorators fire and register.
        cls._modules = {}
        for name in ("llm_chat", "llm_chat_human_in_loop", "multiagent_chat",
                      "function_calling_example"):
            path = os.path.join(EXAMPLES_DIR, f"{name}.py")
            cls._modules[name] = _load_example(name, path)

        cls.task_handler = TaskHandler(
            workers=[],
            configuration=cls.config,
            scan_for_annotated_workers=True,
        )
        cls.task_handler.start_processes()

    @classmethod
    def tearDownClass(cls):
        cls.task_handler.stop_processes()

    # ------------------------------------------------------------------
    # 1. LLM Multi-Turn Chat (fully automated)
    # ------------------------------------------------------------------
    def test_llm_chat(self):
        """llm_chat.py: 3-iteration automated science Q&A completes with no failures."""
        mod = self._modules["llm_chat"]
        wf = mod.create_chat_workflow(self.workflow_executor)
        wf.register(overwrite=True)

        run = wf.execute(wait_until_task_ref="collect_history_ref", wait_for_seconds=10)
        workflow_id = run.workflow_id
        self.addCleanup(_cleanup_workflow, self.workflow_client, workflow_id)

        run = _poll_workflow(self.workflow_client, workflow_id, timeout=120)
        self.assertEqual(run.status, "COMPLETED",
                         f"llm_chat workflow did not complete: {run.status}")

        tasks = _task_map(run)
        failed = [t for t in (run.tasks or []) if t.status == "FAILED"]
        self.assertEqual(len(failed), 0,
                         f"Failed tasks: {[(t.reference_task_name, t.reason_for_incompletion) for t in failed]}")

        # Verify all 3 loop iterations produced answers and follow-ups
        for i in range(1, 4):
            ref = f"chat_complete_ref__{i}"
            self.assertIn(ref, tasks, f"Missing iteration {i} chat_complete")
            self.assertEqual(tasks[ref].status, "COMPLETED")
            result = (tasks[ref].output_data or {}).get("result", "")
            self.assertTrue(len(str(result)) > 10,
                            f"chat_complete iteration {i} has empty result")

            ref = f"followup_question_ref__{i}"
            self.assertIn(ref, tasks, f"Missing iteration {i} followup")
            self.assertEqual(tasks[ref].status, "COMPLETED")

        print(f"  llm_chat PASSED (workflow_id={workflow_id})")

    # ------------------------------------------------------------------
    # 2. LLM Chat Human-in-the-Loop (simulated user input)
    # ------------------------------------------------------------------
    def test_llm_chat_human_in_loop(self):
        """llm_chat_human_in_loop.py: send 2 questions via API, verify LLM responses."""
        mod = self._modules["llm_chat_human_in_loop"]
        wf = mod.create_human_chat_workflow(self.workflow_executor)
        wf.register(overwrite=True)

        run = wf.execute(wait_until_task_ref="user_input_ref", wait_for_seconds=1)
        workflow_id = run.workflow_id
        self.addCleanup(_cleanup_workflow, self.workflow_client, workflow_id)

        questions = [
            "What is photosynthesis?",
            "How does it relate to climate change?",
        ]

        for i, question in enumerate(questions, 1):
            run = _wait_for_task(self.workflow_client, workflow_id,
                                "user_input_ref", "IN_PROGRESS", timeout=30)

            # Complete the WAIT task with our question
            self.task_client.update_task_sync(
                workflow_id=workflow_id,
                task_ref_name="user_input_ref",
                status=TaskResultStatus.COMPLETED,
                output={"question": question},
            )

            # Wait for LLM to respond
            time.sleep(8)

        # Terminate after 2 rounds (don't wait for all 5 loop iterations)
        try:
            self.workflow_client.terminate_workflow(workflow_id=workflow_id,
                                                   reason="e2e test complete")
        except Exception:
            pass

        run = self.workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)
        tasks = _task_map(run)

        # Verify at least 2 chat completions succeeded
        for i in range(1, 3):
            ref = f"chat_complete_ref__{i}"
            self.assertIn(ref, tasks, f"Missing chat_complete for question {i}")
            self.assertEqual(tasks[ref].status, "COMPLETED",
                             f"chat_complete__{i} status={tasks[ref].status}")
            result = str((tasks[ref].output_data or {}).get("result", ""))
            self.assertTrue(len(result) > 10,
                            f"chat_complete__{i} has empty result")

        print(f"  llm_chat_human_in_loop PASSED (workflow_id={workflow_id})")

    # ------------------------------------------------------------------
    # 3. Multi-Agent Chat (fully automated)
    # ------------------------------------------------------------------
    def test_multiagent_chat(self):
        """multiagent_chat.py: moderator alternates between 2 agents across 4 rounds."""
        mod = self._modules["multiagent_chat"]
        wf = mod.create_multiagent_workflow(self.workflow_executor)
        wf.register(overwrite=True)

        wf_input = {
            "topic": "The role of open-source software in modern technology",
            "agent1_name": "a software engineer",
            "agent2_name": "a business strategist",
        }

        run = wf.execute(
            wait_until_task_ref="build_mod_msgs_ref",
            wait_for_seconds=1,
            workflow_input=wf_input,
        )
        workflow_id = run.workflow_id
        self.addCleanup(_cleanup_workflow, self.workflow_client, workflow_id)

        run = _poll_workflow(self.workflow_client, workflow_id, timeout=180)
        self.assertEqual(run.status, "COMPLETED",
                         f"multiagent_chat workflow did not complete: {run.status}")

        tasks = _task_map(run)
        failed = [t for t in (run.tasks or []) if t.status == "FAILED"]
        self.assertEqual(len(failed), 0,
                         f"Failed tasks: {[(t.reference_task_name, t.reason_for_incompletion) for t in failed]}")

        # Verify all 4 moderator rounds completed
        for i in range(1, 5):
            ref = f"moderator_ref__{i}"
            self.assertIn(ref, tasks, f"Missing moderator round {i}")
            self.assertEqual(tasks[ref].status, "COMPLETED")
            result = (tasks[ref].output_data or {}).get("result", {})
            self.assertIsInstance(result, dict, f"moderator__{i} result should be dict (json_output)")
            self.assertIn("user", result, f"moderator__{i} missing 'user' field in JSON output")

        # Verify at least one agent from each side spoke
        agent_refs = [t.reference_task_name for t in (run.tasks or [])
                      if t.reference_task_name.startswith(("agent1_ref", "agent2_ref"))
                      and t.status == "COMPLETED"]
        self.assertTrue(any(r.startswith("agent1_ref") for r in agent_refs),
                        "Agent 1 never spoke")
        self.assertTrue(any(r.startswith("agent2_ref") for r in agent_refs),
                        "Agent 2 never spoke")

        print(f"  multiagent_chat PASSED (workflow_id={workflow_id})")

    # ------------------------------------------------------------------
    # 4. Function Calling (simulated user input)
    # ------------------------------------------------------------------
    def test_function_calling(self):
        """function_calling_example.py: LLM routes 3 queries to correct tool functions."""
        mod = self._modules["function_calling_example"]
        wf = mod.create_function_calling_workflow(self.workflow_executor)
        wf.register(overwrite=True)

        run = wf.execute(wait_until_task_ref="get_user_input", wait_for_seconds=1)
        workflow_id = run.workflow_id
        self.addCleanup(_cleanup_workflow, self.workflow_client, workflow_id)

        test_cases = [
            {
                "question": "What is the weather in Tokyo?",
                "expected_fn": "get_weather",
                "validate": lambda r: r.get("result", {}).get("city", "").lower() == "tokyo",
            },
            {
                "question": "How much does a laptop cost?",
                "expected_fn": "get_price",
                "validate": lambda r: r.get("result", {}).get("price") is not None,
            },
            {
                "question": "Calculate sqrt(144) + 8",
                "expected_fn": "calculate",
                "validate": lambda r: r.get("result", {}).get("result") == 20.0,
            },
        ]

        for i, tc in enumerate(test_cases, 1):
            run = _wait_for_task(self.workflow_client, workflow_id,
                                "get_user_input", "IN_PROGRESS", timeout=30)

            self.task_client.update_task_sync(
                workflow_id=workflow_id,
                task_ref_name="get_user_input",
                status=TaskResultStatus.COMPLETED,
                output={"question": tc["question"]},
            )

            # Wait for LLM + dispatch
            time.sleep(10)

            run = self.workflow_client.get_workflow(workflow_id=workflow_id, include_tasks=True)
            tasks = _task_map(run)

            fn_ref = f"fn_call_ref__{i}"
            self.assertIn(fn_ref, tasks, f"Missing fn_call for query {i}: {tc['question']}")
            self.assertEqual(tasks[fn_ref].status, "COMPLETED",
                             f"fn_call__{i} status={tasks[fn_ref].status}, "
                             f"reason={getattr(tasks[fn_ref], 'reason_for_incompletion', '')}")

            fn_output = tasks[fn_ref].output_data or {}

            # Worker returns {"function": "get_weather", "parameters": {...}, "result": {...}}
            # The output_data IS the worker return dict directly.
            called_fn = fn_output.get("function", "")
            self.assertEqual(called_fn, tc["expected_fn"],
                             f"Query '{tc['question']}' called '{called_fn}' "
                             f"instead of '{tc['expected_fn']}'")

            # Verify output makes sense
            self.assertTrue(tc["validate"](fn_output),
                            f"Validation failed for '{tc['question']}': {fn_output}")

        # Terminate (don't wait for all 5 loop iterations)
        try:
            self.workflow_client.terminate_workflow(workflow_id=workflow_id,
                                                   reason="e2e test complete")
        except Exception:
            pass

        print(f"  function_calling PASSED (workflow_id={workflow_id})")


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

def main():
    """Run all tests and print a summary."""
    print("=" * 70)
    print("Agentic Workflow E2E Tests")
    print("=" * 70)
    print(f"Server: {os.environ.get('CONDUCTOR_SERVER_URL', 'http://localhost:8080/api')}")
    print()

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(AgenticWorkflowTests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
        for test, traceback in result.failures + result.errors:
            print(f"  FAIL: {test}")
    print("=" * 70)

    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
