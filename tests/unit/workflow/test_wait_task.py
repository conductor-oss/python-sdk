import unittest

from conductor.client.workflow.task.wait_task import WaitTask, WaitForDurationTask, WaitUntilTask


class TestWaitTask(unittest.TestCase):
    def test_wait_until_uses_correct_key(self):
        """WaitTask(wait_until=...) must set the 'until' key, not 'wait_until'.

        The Conductor server reads the 'until' inputParameter (see Wait.java:
        UNTIL_INPUT = "until").  Using the wrong key causes the task to stay
        IN_PROGRESS indefinitely because the server never evaluates the
        condition.  See: https://github.com/conductor-oss/python-sdk/issues/426
        """
        task = WaitTask("my_wait_ref", wait_until="2025-01-01 00:00 UTC")
        self.assertIn("until", task.input_parameters)
        self.assertNotIn("wait_until", task.input_parameters)
        self.assertEqual(task.input_parameters["until"], "2025-01-01 00:00 UTC")

    def test_wait_for_seconds_uses_duration_key(self):
        task = WaitTask("my_wait_ref", wait_for_seconds=30)
        self.assertIn("duration", task.input_parameters)
        self.assertEqual(task.input_parameters["duration"], "30s")

    def test_both_params_raises(self):
        with self.assertRaises(Exception):
            WaitTask("my_wait_ref", wait_until="2025-01-01 00:00 UTC", wait_for_seconds=30)

    def test_wait_for_duration_task(self):
        task = WaitForDurationTask("dur_ref", duration_time_seconds=60)
        self.assertEqual(task.input_parameters["duration"], "60s")

    def test_wait_until_task_uses_until_key(self):
        task = WaitUntilTask("until_ref", date_time="2025-06-01 12:00 UTC")
        self.assertIn("until", task.input_parameters)
        self.assertEqual(task.input_parameters["until"], "2025-06-01 12:00 UTC")


if __name__ == "__main__":
    unittest.main()
