import unittest

from conductor.client.workflow.task.dynamic_fork_task import DynamicForkTask
from conductor.client.workflow.task.join_task import JoinTask


class TestDynamicForkTask(unittest.TestCase):
    def test_to_workflow_task_uses_dynamic_fork_tasks_param(self):
        task = DynamicForkTask(
            task_ref_name="fork",
            tasks_param="myTasks",
            tasks_input_param_name="myTasksInput",
        )
        tasks = task.to_workflow_task()
        wf_task = tasks[0]
        self.assertEqual(wf_task.dynamic_fork_tasks_param, "myTasks")
        self.assertEqual(wf_task.dynamic_fork_tasks_input_param_name, "myTasksInput")
        self.assertIsNone(wf_task.dynamic_fork_join_tasks_param)

    def test_to_workflow_task_with_join(self):
        join = JoinTask("join", join_on=[])
        task = DynamicForkTask(task_ref_name="fork", join_task=join)
        tasks = task.to_workflow_task()
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].dynamic_fork_tasks_param, "dynamicTasks")
        self.assertEqual(tasks[0].dynamic_fork_tasks_input_param_name, "dynamicTasksInputs")
        self.assertIsNone(tasks[0].dynamic_fork_join_tasks_param)
        self.assertEqual(tasks[1].task_reference_name, "join")


if __name__ == "__main__":
    unittest.main()
