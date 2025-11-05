from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.api.token_resource_api import TokenResourceApi
from conductor.client.http.models.generate_token_request import GenerateTokenRequest
from conductor.client.http.models.response import Response


class TokenResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = TokenResourceApi(api_client)

    def generate_token(self, body: GenerateTokenRequest, **kwargs) -> Response:
        """Generate a JWT token"""
        return self._api.generate_token(body, **kwargs)

    def get_user_info(self, **kwargs) -> object:
        """Get user information"""
        return self._api.get_user_info(**kwargs)
