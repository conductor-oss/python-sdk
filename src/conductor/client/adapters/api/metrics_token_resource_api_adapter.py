from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.api.metrics_token_resource_api import MetricsTokenResourceApi
from conductor.client.http.models.metrics_token import MetricsToken


class MetricsTokenResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = MetricsTokenResourceApi(api_client)

    def token(self, **kwargs) -> MetricsToken:
        """Returns the metrics token"""
        return self._api.token(**kwargs)
