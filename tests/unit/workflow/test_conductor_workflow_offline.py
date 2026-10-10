import unittest
from unittest.mock import MagicMock

from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.simple_task import SimpleTask


class TestConductorWorkflowWithoutExecutor(unittest.TestCase):
    def test_build_definition_without_executor(self):
        workflow = ConductorWorkflow(name="offline_wf", version=2)
        workflow.add(SimpleTask(task_def_name="task_a", task_reference_name="a"))

        workflow_def = workflow.to_workflow_def()
        self.assertEqual(workflow_def.name, "offline_wf")
        self.assertEqual(workflow_def.version, 2)
        self.assertEqual([t.task_reference_name for t in workflow_def.tasks], ["a"])

    def test_name_is_still_required(self):
        with self.assertRaises(TypeError):
            ConductorWorkflow()

    def test_register_without_executor_raises(self):
        with self.assertRaisesRegex(RuntimeError, "executor="):
            ConductorWorkflow(name="offline_wf").register(overwrite=True)

    def test_start_workflow_with_input_without_executor_raises(self):
        with self.assertRaises(RuntimeError):
            ConductorWorkflow(name="offline_wf").start_workflow_with_input({})

    def test_execute_without_executor_raises(self):
        with self.assertRaises(RuntimeError):
            ConductorWorkflow(name="offline_wf").execute({})

    def test_positional_executor_still_used(self):
        executor = MagicMock()
        workflow = ConductorWorkflow(executor, "wf", 1)

        workflow.register(overwrite=True)

        executor.register_workflow.assert_called_once()
        self.assertEqual(executor.register_workflow.call_args.kwargs["workflow"].name, "wf")


if __name__ == "__main__":
    unittest.main()
