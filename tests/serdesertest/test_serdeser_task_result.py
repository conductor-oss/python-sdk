import unittest
import json
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_exec_log import TaskExecLog
from conductor.client.http.models.task_result_status import TaskResultStatus
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestTaskResultSerDeser(unittest.TestCase):
    def setUp(self):
        self.server_json_str = JsonTemplateResolver.get_json_string("TaskResult")

    def test_task_result_serdeser(self):
        # Step 1: Deserialize JSON into TaskResult object
        server_json_dict = json.loads(self.server_json_str)
        task_result = TaskResult(
            workflow_instance_id=server_json_dict.get("workflowInstanceId"),
            task_id=server_json_dict.get("taskId"),
            reason_for_incompletion=server_json_dict.get("reasonForIncompletion"),
            callback_after_seconds=server_json_dict.get("callbackAfterSeconds"),
            worker_id=server_json_dict.get("workerId"),
            status=server_json_dict.get("status"),
            output_data=server_json_dict.get("outputData"),
            logs=[TaskExecLog(log.get("log")) for log in server_json_dict.get("logs", [])],
            external_output_payload_storage_path=server_json_dict.get("externalOutputPayloadStoragePath"),
            sub_workflow_id=server_json_dict.get("subWorkflowId"),
            extend_lease=server_json_dict.get("extendLease", False)
        )

        # Step 2: Verify all fields are properly populated
        self.assertEqual(server_json_dict.get("workflowInstanceId"), task_result.workflow_instance_id)
        self.assertEqual(server_json_dict.get("taskId"), task_result.task_id)
        self.assertEqual(server_json_dict.get("reasonForIncompletion"), task_result.reason_for_incompletion)
        self.assertEqual(server_json_dict.get("callbackAfterSeconds"), task_result.callback_after_seconds)
        self.assertEqual(server_json_dict.get("workerId"), task_result.worker_id)

        # Verify enum status is correctly converted
        if server_json_dict.get("status"):
            self.assertIsInstance(task_result.status, TaskResultStatus)
            self.assertEqual(server_json_dict.get("status"), task_result.status.name)

        # Verify output_data map
        self.assertEqual(server_json_dict.get("outputData"), task_result.output_data)

        # Verify logs list
        if server_json_dict.get("logs"):
            self.assertEqual(len(server_json_dict.get("logs")), len(task_result.logs))
            for i, log in enumerate(server_json_dict.get("logs", [])):
                self.assertEqual(log.get("log"), task_result.logs[i].log)

        self.assertEqual(server_json_dict.get("externalOutputPayloadStoragePath"),
                         task_result.external_output_payload_storage_path)
        self.assertEqual(server_json_dict.get("subWorkflowId"), task_result.sub_workflow_id)
        self.assertEqual(server_json_dict.get("extendLease", False), task_result.extend_lease)

        # Step 3: Serialize back to JSON
        serialized_json_dict = task_result.to_dict()

        # Step 4: Verify the resulting JSON matches the original
        # Check field by field to ensure no data is lost
        self.assertEqual(server_json_dict.get("workflowInstanceId"),
                         serialized_json_dict.get("workflow_instance_id"))
        self.assertEqual(server_json_dict.get("taskId"),
                         serialized_json_dict.get("task_id"))
        self.assertEqual(server_json_dict.get("reasonForIncompletion"),
                         serialized_json_dict.get("reason_for_incompletion"))
        self.assertEqual(server_json_dict.get("callbackAfterSeconds"),
                         serialized_json_dict.get("callback_after_seconds"))
        self.assertEqual(server_json_dict.get("workerId"),
                         serialized_json_dict.get("worker_id"))

        # Check status - need to convert enum to string when comparing
        if server_json_dict.get("status"):
            self.assertEqual(server_json_dict.get("status"),
                             serialized_json_dict.get("status").name)

        # Check output_data map
        self.assertEqual(server_json_dict.get("outputData"),
                         serialized_json_dict.get("output_data"))

        # Check logs list - in serialized version, logs are returned as dictionaries
        if server_json_dict.get("logs"):
            self.assertEqual(len(server_json_dict.get("logs")),
                             len(serialized_json_dict.get("logs")))
            for i, orig_log in enumerate(server_json_dict.get("logs", [])):
                serialized_log = serialized_json_dict.get("logs")[i]
                # Check that the serialized log dictionary has the expected structure
                self.assertEqual(orig_log.get("log"), serialized_log.get("log"))

        self.assertEqual(server_json_dict.get("externalOutputPayloadStoragePath"),
                         serialized_json_dict.get("external_output_payload_storage_path"))
        self.assertEqual(server_json_dict.get("subWorkflowId"),
                         serialized_json_dict.get("sub_workflow_id"))
        self.assertEqual(server_json_dict.get("extendLease", False),
                         serialized_json_dict.get("extend_lease"))


if __name__ == "__main__":
    unittest.main()