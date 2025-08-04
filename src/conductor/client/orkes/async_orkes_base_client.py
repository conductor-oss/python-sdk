import logging

from conductor.client.my_aiohttp_client import Configuration, ApiClient, ApplicationResourceApi


class AsyncOrkesBaseClient:
    def __init__(self, configuration: Configuration):
        self.api_client = ApiClient(configuration)
        self.logger = logging.getLogger(__name__)
        self.application_resource_api = ApplicationResourceApi(self.api_client)
