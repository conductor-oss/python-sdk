import unittest

from conductor.client.http.api_client import ApiClient
from conductor.client.http.models import Task


class TestTaskRuntimeMetadata(unittest.TestCase):
    """
    The server delivers host-resolved secret values on Task.runtimeMetadata (wire-only, never
    persisted) when a worker's TaskDef.runtimeMetadata declares secret names (conductor-oss PR #1255).
    Verify the client model round-trips the field and omits it when empty.
    """

    def setUp(self):
        self.client = ApiClient()

    def test_runtime_metadata_round_trips(self):
        task = Task(task_id="t1", runtime_metadata={"GITHUB_TOKEN": "ghp_secret", "GH_APP_ID": "42"})

        wire = self.client.sanitize_for_serialization(task)
        self.assertIn("runtimeMetadata", wire, "field must serialize under the wire key")
        self.assertEqual({"GITHUB_TOKEN": "ghp_secret", "GH_APP_ID": "42"}, wire["runtimeMetadata"])

        back = self.client.deserialize_class(wire, Task)
        self.assertEqual("ghp_secret", back.runtime_metadata["GITHUB_TOKEN"])
        self.assertEqual("42", back.runtime_metadata["GH_APP_ID"])

    def test_runtime_metadata_omitted_when_empty(self):
        wire = self.client.sanitize_for_serialization(Task(task_id="t1"))
        self.assertNotIn("runtimeMetadata", wire, "absent map must not appear on the wire")


if __name__ == "__main__":
    unittest.main()
