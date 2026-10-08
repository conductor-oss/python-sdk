import unittest

from conductor.client.workflow.task.task_type import TaskType


class TestTaskType(unittest.TestCase):
    def test_agent_task_types(self):
        self.assertEqual(TaskType.AGENT.value, "AGENT")
        self.assertEqual(TaskType.GET_AGENT_CARD.value, "GET_AGENT_CARD")
        self.assertEqual(TaskType.CANCEL_AGENT.value, "CANCEL_AGENT")


if __name__ == "__main__":
    unittest.main()
