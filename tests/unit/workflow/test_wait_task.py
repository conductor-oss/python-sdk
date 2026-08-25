import unittest

from conductor.client.workflow.task.wait_task import (
    WaitForDurationTask,
    WaitTask,
    WaitUntilTask,
)


class TestWaitTask(unittest.TestCase):
    def test_wait_until_uses_server_recognized_until_key(self):
        task = WaitTask("wait_until", wait_until="2026-08-05 12:00 UTC")

        self.assertEqual(task.input_parameters, {"until": "2026-08-05 12:00 UTC"})
        self.assertNotIn("wait_until", task.input_parameters)

    def test_wait_for_seconds_uses_duration_key(self):
        task = WaitTask("wait_for_seconds", wait_for_seconds=60)

        self.assertEqual(task.input_parameters, {"duration": "60s"})

    def test_wait_for_duration_task_uses_duration_key(self):
        task = WaitForDurationTask("wait_for_duration", duration_time_seconds=30)

        self.assertEqual(task.input_parameters, {"duration": "30s"})

    def test_wait_until_task_uses_until_key(self):
        task = WaitUntilTask("wait_until_task", date_time="2026-08-05 12:00 UTC")

        self.assertEqual(task.input_parameters, {"until": "2026-08-05 12:00 UTC"})


if __name__ == "__main__":
    unittest.main()
