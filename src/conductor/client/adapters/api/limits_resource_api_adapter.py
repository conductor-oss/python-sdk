from typing import Dict

from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.api.limits_resource_api import LimitsResourceApi


class LimitsResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = LimitsResourceApi(api_client)

    def get2(self, **kwargs) -> Dict[str, object]:
        """Get Limits"""
        return self._api.get2(**kwargs)
