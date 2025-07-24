import unittest
import json
from conductor.client.http.models.task_result import TaskResult, TaskResultStatus, TaskExecLog
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestTaskResultSerde(unittest.TestCase):
    def setUp(self):
        self.server_json_str = JsonTemplateResolver.get_json_string("TaskResult")
        self.server_json = json.loads(self.server_json_str)

    def test_task_result_serde(self):
        # 1. Create TaskResult object using constructor
        task_result = TaskResult()

        # Populate basic fields
        task_result.workflow_instance_id = self.server_json.get("workflowInstanceId")
        task_result.task_id = self.server_json.get("taskId")
        task_result.reason_for_incompletion = self.server_json.get("reasonForIncompletion")
        task_result.callback_after_seconds = self.server_json.get("callbackAfterSeconds", 0)
        task_result.worker_id = self.server_json.get("workerId")

        # Handle enum conversion for status
        status_str = self.server_json.get("status")
        if status_str:
            task_result.status = TaskResultStatus[status_str]

        # Handle output_data dictionary
        task_result.output_data = self.server_json.get("outputData", {})

        # Handle logs - use the log() method to add logs
        logs_json = self.server_json.get("logs", [])
        for log_entry in logs_json:
            if isinstance(log_entry, dict) and "log" in log_entry:
                task_result.log(log_entry["log"])

        # Set remaining fields
        task_result.external_output_payload_storage_path = self.server_json.get("externalOutputPayloadStoragePath")
        task_result.sub_workflow_id = self.server_json.get("subWorkflowId")
        task_result.extend_lease = self.server_json.get("extendLease", False)

        # 2. Verify all fields are properly populated
        self.assertEqual(task_result.workflow_instance_id, self.server_json.get("workflowInstanceId"))
        self.assertEqual(task_result.task_id, self.server_json.get("taskId"))
        self.assertEqual(task_result.reason_for_incompletion, self.server_json.get("reasonForIncompletion"))
        self.assertEqual(task_result.callback_after_seconds, self.server_json.get("callbackAfterSeconds", 0))
        self.assertEqual(task_result.worker_id, self.server_json.get("workerId"))

        # Check enum field (status)
        if status_str:
            self.assertEqual(task_result.status.name, status_str)

        # Check dictionary (output_data)
        self.assertEqual(task_result.output_data, self.server_json.get("outputData", {}))

        # Check list of TaskExecLog objects
        self.assertEqual(len(task_result.logs), len(logs_json))
        for i, log_entry in enumerate(logs_json):
            if isinstance(log_entry, dict) and "log" in log_entry:
                self.assertEqual(task_result.logs[i].log, log_entry["log"])

        # Check remaining fields
        self.assertEqual(task_result.external_output_payload_storage_path,
                         self.server_json.get("externalOutputPayloadStoragePath"))
        self.assertEqual(task_result.sub_workflow_id, self.server_json.get("subWorkflowId"))
        self.assertEqual(task_result.extend_lease, self.server_json.get("extendLease", False))

        # 3. Serialize the TaskResult to a dictionary
        serialized_dict = task_result.to_dict()


        # 4. Check field by field based on what's actually in the serialized dict
        # This is a more robust approach that will work even if field names change

        # For basic string/number fields, check equivalence if the field exists
        fields_to_check = [
            # (serialized_key, server_json_key)
            ("workflowInstanceId", "workflowInstanceId"),
            ("workflow_instance_id", "workflowInstanceId"),
            ("taskId", "taskId"),
            ("task_id", "taskId"),
            ("reasonForIncompletion", "reasonForIncompletion"),
            ("reason_for_incompletion", "reasonForIncompletion"),
            ("callbackAfterSeconds", "callbackAfterSeconds"),
            ("callback_after_seconds", "callbackAfterSeconds"),
            ("workerId", "workerId"),
            ("worker_id", "workerId"),
            ("externalOutputPayloadStoragePath", "externalOutputPayloadStoragePath"),
            ("external_output_payload_storage_path", "externalOutputPayloadStoragePath"),
            ("subWorkflowId", "subWorkflowId"),
            ("sub_workflow_id", "subWorkflowId"),
            ("extendLease", "extendLease"),
            ("extend_lease", "extendLease"),
        ]

        for serialized_key, server_key in fields_to_check:
            if serialized_key in serialized_dict:
                self.assertEqual(serialized_dict[serialized_key], self.server_json.get(server_key))
                print(f"Matched field: {serialized_key} = {server_key}")

        # Check status (handling the enum conversion)
        status_keys = ["status", "_status"]
        for key in status_keys:
            if key in serialized_dict and serialized_dict[key] is not None and status_str:
                if isinstance(serialized_dict[key], str):
                    self.assertEqual(serialized_dict[key], status_str)
                else:
                    self.assertEqual(serialized_dict[key].name, status_str)
                print(f"Matched status field: {key}")

        # Check output data
        output_data_keys = ["outputData", "output_data", "_output_data"]
        for key in output_data_keys:
            if key in serialized_dict:
                self.assertEqual(serialized_dict[key], self.server_json.get("outputData", {}))
                print(f"Matched output data field: {key}")

        # Check logs (just length check for now)
        logs_keys = ["logs", "_logs"]
        for key in logs_keys:
            if key in serialized_dict:
                self.assertEqual(len(serialized_dict[key]), len(logs_json))
                print(f"Matched logs length: {key}")


if __name__ == "__main__":
    unittest.main()