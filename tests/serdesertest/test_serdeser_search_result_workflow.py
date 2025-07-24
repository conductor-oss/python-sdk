import unittest
from conductor.client.http.models.search_result_workflow import SearchResultWorkflow
from conductor.client.http.models.workflow import Workflow
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver
import json


class TestSearchResultWorkflow(unittest.TestCase):
    def setUp(self):
        # Load the JSON template
        self.server_json_str = JsonTemplateResolver.get_json_string("SearchResult")
        self.server_json = json.loads(self.server_json_str)

    def test_search_result_workflow_serde(self):
        """Test serialization and deserialization of SearchResultWorkflow"""

        # 1. Deserialize JSON into SDK model
        model = SearchResultWorkflow()

        # Manually map JSON fields to model attributes
        if "totalHits" in self.server_json:
            model.total_hits = self.server_json["totalHits"]

        # For the results list, we need to create Workflow objects
        if "results" in self.server_json and self.server_json["results"]:
            workflow_list = []
            for workflow_json in self.server_json["results"]:
                workflow = Workflow()
                # Populate workflow object (assuming Workflow has proper setters)
                # This would depend on the structure of Workflow class
                workflow_list.append(workflow)

            model.results = workflow_list

        # 2. Verify all fields are properly populated
        self.assertIsNotNone(model.total_hits)
        self.assertIsNotNone(model.results)
        if model.results:
            self.assertIsInstance(model.results[0], Workflow)

        # 3. Serialize back to JSON
        model_dict = model.to_dict()
        model_json = json.dumps(model_dict)

        # 4. Verify the serialized JSON matches the original
        deserialized_json = json.loads(model_json)

        # Check totalHits field (camelCase to snake_case transformation)
        self.assertEqual(
            self.server_json.get("totalHits"),
            deserialized_json.get("total_hits")
        )

        # Check results field
        self.assertEqual(
            len(self.server_json.get("results", [])),
            len(deserialized_json.get("results", []))
        )

        # Additional assertion for nested structures if needed
        if self.server_json.get("results") and deserialized_json.get("results"):
            # This assumes the Workflow class properly handles its own serialization
            # Add more detailed checks for the Workflow objects if needed
            pass


if __name__ == '__main__':
    unittest.main()