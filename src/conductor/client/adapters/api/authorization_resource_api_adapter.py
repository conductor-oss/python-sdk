from conductor.client.codegen.api.authorization_resource_api import AuthorizationResourceApi
from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.http.models.response import Response
from conductor.client.http.models.authorization_request import AuthorizationRequest


class AuthorizationResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = AuthorizationResourceApi(api_client)

    def get_permissions(self, type: str, id: str, **kwargs) -> object:
        """Get the access that have been granted over the given object"""
        return self._api.get_permissions(type, id, **kwargs)

    def grant_permissions(self, body: AuthorizationRequest, **kwargs) -> Response:
        """Grant permissions to the given object"""
        return self._api.grant_permissions(body, **kwargs)

    def remove_permissions(self, body: AuthorizationRequest, **kwargs) -> Response:
        """Remove permissions from the given object"""
        return self._api.remove_permissions(body, **kwargs)
