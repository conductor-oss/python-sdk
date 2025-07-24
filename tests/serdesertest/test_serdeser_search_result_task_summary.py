import unittest
from conductor.client.http.models.search_result_task_summary import SearchResultTaskSummary
from conductor.client.http.models.task_summary import TaskSummary
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver
import json


class TestSearchResultTaskSummarySerDeser(unittest.TestCase):
    """Test serialization and deserialization of SearchResultTaskSummary model"""

    def setUp(self):
        """Set up test fixtures"""
        self.server_json_str = JsonTemplateResolver.get_json_string("SearchResult")
        self.server_json = json.loads(self.server_json_str)

    def test_search_result_task_summary_serdeser(self):
        """Test serialization and deserialization of SearchResultTaskSummary"""
        task_summary = TaskSummary()
        # 1. Test deserialization of server JSON into SDK model
        model = SearchResultTaskSummary(
            total_hits=self.server_json.get("totalHits"),
            results=[task_summary] if self.server_json.get("results") else None
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(model.total_hits, self.server_json.get("totalHits"))
        self.assertEqual(len(model.results), len(self.server_json.get("results", [])))

        # Verify each TaskSummary in results list
        for i, task_summary in enumerate(model.results):
            original_task = self.server_json.get("results")[i]
            # Assuming TaskSummary has properties that correspond to the JSON fields
            # Add specific assertions for TaskSummary fields here
            self.assertTrue(isinstance(task_summary, TaskSummary))

        # 3. Test serialization back to JSON
        model_dict = model.to_dict()

        # 4. Verify the resulting JSON matches the original
        self.assertEqual(model_dict.get("total_hits"), self.server_json.get("totalHits"))
        self.assertEqual(len(model_dict.get("results", [])), len(self.server_json.get("results", [])))

        # Check field transformation from snake_case to camelCase
        serialized_json = {}
        for attr, json_key in model.attribute_map.items():
            if attr in model_dict:
                serialized_json[json_key] = model_dict[attr]

        # Compare serialized JSON with original (considering camelCase transformation)
        for key in self.server_json:
            if key == "results":
                # For lists, compare length
                self.assertEqual(len(serialized_json.get(key, [])), len(self.server_json.get(key, [])))
            else:
                self.assertEqual(serialized_json.get(key), self.server_json.get(key))


if __name__ == '__main__':
    unittest.main()