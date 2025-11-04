from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.api.version_resource_api import VersionResourceApi


class VersionResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = VersionResourceApi(api_client)

    def get_version(self, **kwargs) -> str:
        """Get the server's version"""
        return self._api.get_version(**kwargs)
