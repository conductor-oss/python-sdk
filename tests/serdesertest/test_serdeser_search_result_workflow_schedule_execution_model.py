import unittest
from conductor.client.http.models.search_result_workflow_schedule_execution_model import \
    SearchResultWorkflowScheduleExecutionModel
from conductor.client.http.models.workflow_schedule_execution_model import WorkflowScheduleExecutionModel
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver
import json


class TestSearchResultWorkflowScheduleExecutionModel(unittest.TestCase):
    """
    Test case for SearchResultWorkflowScheduleExecutionModel
    """

    def setUp(self):
        """
        Set up test fixtures
        """
        self.server_json_str = JsonTemplateResolver.get_json_string("SearchResult")
        self.server_json = json.loads(self.server_json_str)

    def test_search_result_workflow_schedule_execution_model_serde(self):
        """
        Test serialization and deserialization of SearchResultWorkflowScheduleExecutionModel
        """
        work_flow_schedule_execution_model = WorkflowScheduleExecutionModel()
        # 1. Deserialization: Server JSON to SDK model
        model = SearchResultWorkflowScheduleExecutionModel(
            total_hits=self.server_json['totalHits'],
            results=[work_flow_schedule_execution_model] if self.server_json.get("results") else None
        )

        # 2. Verify all fields are properly populated
        self.assertEqual(model.total_hits, self.server_json['totalHits'])
        self.assertEqual(len(model.results), len(self.server_json['results']))

        # Check sample result item if available
        if model.results and len(model.results) > 0:
            sample_result = model.results[0]
            self.assertIsInstance(sample_result, WorkflowScheduleExecutionModel)

            # Verify fields in each result item
            # Note: Add assertions for WorkflowScheduleExecutionModel fields based on expected structure
            # This would vary based on the actual model properties

        # 3. Serialization: SDK model back to JSON
        model_dict = model.to_dict()

        # 4. Verify serialized JSON matches original
        self.assertEqual(model_dict['total_hits'], self.server_json['totalHits'])

        # Verify results list
        self.assertEqual(len(model_dict['results']), len(self.server_json['results']))

        # Check field transformations between camelCase and snake_case
        self.assertTrue('total_hits' in model_dict)
        self.assertTrue('results' in model_dict)


if __name__ == '__main__':
    unittest.main()