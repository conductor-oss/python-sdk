import unittest
import json
from conductor.client.http.models.rate_limit import RateLimit
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class RateLimitTest(unittest.TestCase):
    def setUp(self):
        self.server_json_str = JsonTemplateResolver.get_json_string("RateLimitConfig")
        self.server_json = json.loads(self.server_json_str)

    def test_serialization_deserialization(self):
        # 1. Server JSON can be correctly deserialized into SDK model object
        rate_limit = RateLimit(
            rate_limit_key=self.server_json.get("rateLimitKey"),
            concurrent_exec_limit=self.server_json.get("concurrentExecLimit"),
            tag=self.server_json.get("tag"),
            concurrent_execution_limit=self.server_json.get("concurrentExecutionLimit")
        )

        # 2. All fields are properly populated during deserialization
        self.assertEqual(self.server_json.get("rateLimitKey"), rate_limit.rate_limit_key)
        self.assertEqual(self.server_json.get("concurrentExecLimit"), rate_limit.concurrent_exec_limit)
        self.assertEqual(self.server_json.get("tag"), rate_limit.tag)
        self.assertEqual(self.server_json.get("concurrentExecutionLimit"), rate_limit.concurrent_execution_limit)

        # 3. The SDK model can be serialized back to JSON
        model_dict = rate_limit.to_dict()

        # 4. The resulting JSON matches the original, ensuring no data is lost
        for key, value in self.server_json.items():
            snake_key = self._camel_to_snake(key)
            self.assertIn(snake_key, model_dict)
            self.assertEqual(value, model_dict[snake_key])

    def _camel_to_snake(self, name):
        """
        Convert camelCase to snake_case
        """
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


if __name__ == '__main__':
    unittest.main()