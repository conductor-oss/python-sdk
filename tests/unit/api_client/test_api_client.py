import unittest
import uuid
from conductor.client.http.api_client import ApiClient


class TestApiClient(unittest.TestCase):

    def test_sanitize_for_serialization_with_uuid(self):
        api_client = ApiClient()
        obj = uuid.uuid4()
        sanitized = api_client.sanitize_for_serialization(obj)
        self.assertEqual(str(obj), sanitized)
