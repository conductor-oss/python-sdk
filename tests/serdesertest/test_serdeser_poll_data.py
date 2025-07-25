import json
import unittest
from conductor.client.http.models.poll_data import PollData
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestPollDataSerDes(unittest.TestCase):
    def setUp(self):
        # Load JSON template using the utility
        self.server_json_str = JsonTemplateResolver.get_json_string("PollData")
        self.server_json = json.loads(self.server_json_str)

    def test_poll_data_serdes(self):
        # 1. Test deserialization from JSON to PollData object
        poll_data = PollData(
            queue_name=self.server_json.get("queueName"),
            domain=self.server_json.get("domain"),
            worker_id=self.server_json.get("workerId"),
            last_poll_time=self.server_json.get("lastPollTime")
        )

        # 2. Verify all fields are correctly populated
        self.assertEqual(poll_data.queue_name, self.server_json.get("queueName"))
        self.assertEqual(poll_data.domain, self.server_json.get("domain"))
        self.assertEqual(poll_data.worker_id, self.server_json.get("workerId"))
        self.assertEqual(poll_data.last_poll_time, self.server_json.get("lastPollTime"))

        # 3. Test serialization back to JSON
        serialized_json = poll_data.to_dict()

        # Convert to server JSON format (camelCase)
        result_json = {
            "queueName": serialized_json.get("queue_name"),
            "domain": serialized_json.get("domain"),
            "workerId": serialized_json.get("worker_id"),
            "lastPollTime": serialized_json.get("last_poll_time")
        }

        # 4. Verify resulting JSON matches the original
        self.assertEqual(result_json.get("queueName"), self.server_json.get("queueName"))
        self.assertEqual(result_json.get("domain"), self.server_json.get("domain"))
        self.assertEqual(result_json.get("workerId"), self.server_json.get("workerId"))
        self.assertEqual(result_json.get("lastPollTime"), self.server_json.get("lastPollTime"))

        # Additional verifications
        # Ensure no data loss by comparing keys
        self.assertEqual(set(result_json.keys()), set(self.server_json.keys()))


if __name__ == '__main__':
    unittest.main()