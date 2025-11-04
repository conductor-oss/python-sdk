from typing import Dict

from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.api.metrics_resource_api import MetricsResourceApi
from conductor.client.http.models.json_node import JsonNode


class MetricsResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = MetricsResourceApi(api_client)

    def prometheus_task_metrics(
        self, task_name: str, start: str, end: str, step: str, **kwargs
    ) -> Dict[str, JsonNode]:
        """Returns prometheus task metrics"""
        return self._api.prometheus_task_metrics(task_name, start, end, step, **kwargs)
