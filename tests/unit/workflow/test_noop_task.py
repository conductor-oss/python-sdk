import unittest

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api_client import ApiClient
from conductor.client.workflow.task.noop_task import NoopTask
from conductor.client.workflow.task.switch_task import SwitchTask
from conductor.client.workflow.task.task_type import TaskType


class TestNoopTask(unittest.TestCase):
    def setUp(self):
        self.client = ApiClient(configuration=Configuration())

    def test_serializes_as_builtin_task_without_inputs(self):
        task = NoopTask(task_ref_name="do_nothing")
        self.assertEqual(task.task_type, TaskType.NOOP)
        wire = self.client.sanitize_for_serialization(task.to_workflow_task())
        self.assertEqual(wire["name"], "do_nothing")
        self.assertEqual(wire["taskReferenceName"], "do_nothing")
        self.assertEqual(wire["type"], "NOOP")
        self.assertEqual(wire["inputParameters"], {})

    def test_serializes_in_switch_default_branch(self):
        switch = SwitchTask("route", "${workflow.input.action}").default_case(
            [NoopTask("skip_action")]
        )
        wire = self.client.sanitize_for_serialization(switch.to_workflow_task())
        self.assertEqual(wire["type"], "SWITCH")
        self.assertEqual(len(wire["defaultCase"]), 1)
        fallback = wire["defaultCase"][0]
        self.assertEqual(fallback["type"], "NOOP")
        self.assertEqual(fallback["taskReferenceName"], "skip_action")
        self.assertEqual(fallback["inputParameters"], {})
