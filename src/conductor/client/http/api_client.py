from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.adapters.rest_adapter import RESTClientObjectAdapter

ApiClient = ApiClientAdapter
RESTClientObject = RESTClientObjectAdapter

__all__ = ["ApiClient", "RESTClientObject"]
