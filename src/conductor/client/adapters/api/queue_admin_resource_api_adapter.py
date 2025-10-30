from conductor.client.codegen.api.queue_admin_resource_api import QueueAdminResourceApi
from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from typing import Dict


class QueueAdminResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = QueueAdminResourceApi(api_client)

    def names(self, **kwargs) -> Dict[str, str]:
        """Get Queue Names"""
        return self._api.names(**kwargs)

    def size1(self, **kwargs) -> Dict[str, Dict[str, int]]:
        """Get Queue Size"""
        return self._api.size1(**kwargs)
