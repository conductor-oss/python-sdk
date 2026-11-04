import unittest

from conductor.client.http.api_client import ApiClient
from conductor.client.workflow.task.exclusive_join_task import ExclusiveJoinTask
from conductor.client.workflow.task.join_task import JoinTask


class TestExclusiveJoinTask(unittest.TestCase):
    def test_serializes_join_candidates_and_fallback(self):
        task = ExclusiveJoinTask("merge", ["branch_a", "branch_b"], ["fallback"])
        wire = ApiClient().sanitize_for_serialization(task.to_workflow_task())
        self.assertEqual(wire["type"], "EXCLUSIVE_JOIN")
        self.assertEqual(wire["taskReferenceName"], "merge")
        self.assertEqual(wire["joinOn"], ["branch_a", "branch_b"])
        self.assertEqual(wire["defaultExclusiveJoinTask"], ["fallback"])
        self.assertEqual(JoinTask("normal", ["branch_a"]).to_workflow_task().type, "JOIN")

    def test_fallback_is_optional(self):
        for fallback in (None, []):
            with self.subTest(fallback=fallback):
                task = ExclusiveJoinTask("merge", ["branch_a"], fallback)
                wire = ApiClient().sanitize_for_serialization(task.to_workflow_task())
                self.assertEqual(wire["joinOn"], ["branch_a"])
                if fallback is None:
                    self.assertNotIn("defaultExclusiveJoinTask", wire)
                else:
                    self.assertEqual(wire["defaultExclusiveJoinTask"], [])

    def test_copies_caller_owned_lists(self):
        candidates = ["branch_a"]
        fallback = ["fallback"]
        task = ExclusiveJoinTask("merge", candidates, fallback)
        candidates.append("branch_b")
        fallback.clear()
        workflow_task = task.to_workflow_task()
        self.assertEqual(workflow_task.join_on, ["branch_a"])
        self.assertEqual(workflow_task.default_exclusive_join_task, ["fallback"])
