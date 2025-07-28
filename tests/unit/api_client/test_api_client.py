import uuid

from conductor.client.http.api_client import ApiClient


def test_sanitize_for_serialization_with_uuid():
    api_client = ApiClient()
    obj = uuid.uuid4()
    sanitized = api_client.sanitize_for_serialization(obj)
    assert str(obj) == sanitized
