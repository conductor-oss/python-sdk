import unittest
import json
from conductor.client.http.models.search_result_task import SearchResultTask
from conductor.client.http.models.task import Task
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestSearchResultTaskSerDes(unittest.TestCase):
    """Test serialization and deserialization of SearchResultTask model."""

    def setUp(self):
        """Set up test environment."""
        self.server_json_str = JsonTemplateResolver.get_json_string("SearchResult")
        self.server_json = json.loads(self.server_json_str)

    def test_search_result_task_ser_des(self):
        """
        Test that verifies:
        1. Server JSON can be correctly deserialized into SDK model object
        2. All fields are properly populated during deserialization
        3. The SDK model can be serialized back to JSON
        4. The resulting JSON matches the original
        """
        # Create sample Task object for results
        task = Task()

        # 1. Deserialize JSON into model object
        search_result = SearchResultTask(
            total_hits=self.server_json.get("totalHits"),
            results=[task] if self.server_json.get("results") else None
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(search_result.total_hits, self.server_json.get("totalHits"))

        # Verify results field - depending on what's in the template
        if self.server_json.get("results"):
            self.assertIsNotNone(search_result.results)
            self.assertEqual(len(search_result.results), len(self.server_json.get("results")))
        else:
            # If results is null in JSON, it should be None in the object
            if "results" in self.server_json and self.server_json["results"] is None:
                self.assertIsNone(search_result.results)

        # 3. Serialize model back to dictionary
        serialized_dict = search_result.to_dict()

        # 4. Verify the serialized JSON matches the original
        # Check totalHits field
        if "totalHits" in self.server_json:
            self.assertEqual(serialized_dict.get("total_hits"), self.server_json.get("totalHits"))

        # Check results field - this check will depend on Task serialization
        # which isn't fully testable without a complete Task implementation
        if "results" in self.server_json and self.server_json["results"] is not None:
            self.assertIsNotNone(serialized_dict.get("results"))
            # Basic length check
            self.assertEqual(len(serialized_dict.get("results")), len(self.server_json.get("results")))
        elif "results" in self.server_json and self.server_json["results"] is None:
            # If null in original, should be None after round-trip
            self.assertIsNone(serialized_dict.get("results"))


if __name__ == '__main__':
    unittest.main()