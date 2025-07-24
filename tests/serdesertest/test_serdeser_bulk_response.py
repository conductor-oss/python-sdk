import unittest
import json

from conductor.client.http.models import BulkResponse
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestBulkResponseSerDeser(unittest.TestCase):
    """Test serialization and deserialization for BulkResponse class"""

    def setUp(self):
        """Set up test fixtures"""
        # Load test data from template
        self.server_json_str = JsonTemplateResolver.get_json_string("BulkResponse")
        # Parse into dictionary for comparisons
        self.server_json_dict = json.loads(self.server_json_str)

    def test_bulk_response_serialization_deserialization(self):
        """Comprehensive test for serialization and deserialization of BulkResponse"""
        # 1. Deserialize JSON into model object
        bulk_response = BulkResponse(
            bulk_error_results=self.server_json_dict['bulkErrorResults'],
            bulk_successful_results=self.server_json_dict['bulkSuccessfulResults'],
            message=self.server_json_dict['message']
        )

        # 2. Verify BulkResponse object properties and types
        self.assertIsInstance(bulk_response, BulkResponse)
        self.assertIsInstance(bulk_response.bulk_error_results, dict)
        self.assertIsInstance(bulk_response.bulk_successful_results, list)

        # 3. Validate content of properties
        for key, value in bulk_response.bulk_error_results.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, str)

        # Validate the structure of items in bulk_successful_results
        # This adapts to the actual structure found in the template
        for item in bulk_response.bulk_successful_results:
            # If the items are dictionaries with 'value' keys
            if isinstance(item, dict) and 'value' in item:
                self.assertIsInstance(item['value'], str)
            # If the items are strings
            elif isinstance(item, str):
                pass
            else:
                self.fail(f"Unexpected item type in bulk_successful_results: {type(item)}")

        # 4. Verify values match original source
        self.assertEqual(bulk_response.bulk_error_results, self.server_json_dict['bulkErrorResults'])
        self.assertEqual(bulk_response.bulk_successful_results, self.server_json_dict['bulkSuccessfulResults'])

        # 5. Test serialization back to dictionary
        result_dict = bulk_response.to_dict()
        self.assertIn('bulk_error_results', result_dict)
        self.assertIn('bulk_successful_results', result_dict)
        self.assertEqual(result_dict['bulk_error_results'], self.server_json_dict['bulkErrorResults'])
        self.assertEqual(result_dict['bulk_successful_results'], self.server_json_dict['bulkSuccessfulResults'])

        # 6. Test serialization to JSON-compatible dictionary (with camelCase keys)
        json_compatible_dict = {
            'bulkErrorResults': result_dict['bulk_error_results'],
            'bulkSuccessfulResults': result_dict['bulk_successful_results'],
            'message': result_dict['message']
        }

        # 7. Normalize dictionaries for comparison (handles differences in ordering)
        normalized_original = json.loads(json.dumps(self.server_json_dict, sort_keys=True))
        normalized_result = json.loads(json.dumps(json_compatible_dict, sort_keys=True))
        self.assertEqual(normalized_original, normalized_result)

        # 8. Test full serialization/deserialization round trip
        bulk_response_2 = BulkResponse(
            bulk_error_results=result_dict['bulk_error_results'],
            bulk_successful_results=result_dict['bulk_successful_results'],
            message=self.server_json_dict['message']
        )
        self.assertEqual(bulk_response.bulk_error_results, bulk_response_2.bulk_error_results)
        self.assertEqual(bulk_response.bulk_successful_results, bulk_response_2.bulk_successful_results)

        # 9. Test with missing fields
        bulk_response_errors_only = BulkResponse(
            bulk_error_results={"id1": "error1"}
        )
        self.assertEqual(bulk_response_errors_only.bulk_error_results, {"id1": "error1"})
        self.assertEqual(bulk_response_errors_only.bulk_successful_results, [])

        # Create a structure similar to what's in the template
        sample_successful_result = [{"value": "success1"}]
        bulk_response_success_only = BulkResponse(
            bulk_successful_results=sample_successful_result
        )
        self.assertEqual(bulk_response_success_only.bulk_error_results, {})
        self.assertEqual(bulk_response_success_only.bulk_successful_results, sample_successful_result)

        # 10. Test with empty fields
        bulk_response_empty = BulkResponse(
            bulk_error_results={},
            bulk_successful_results=[]
        )
        self.assertEqual(bulk_response_empty.bulk_error_results, {})
        self.assertEqual(bulk_response_empty.bulk_successful_results, [])


if __name__ == '__main__':
    unittest.main()