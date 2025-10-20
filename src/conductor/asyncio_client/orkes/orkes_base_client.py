import logging

from conductor.asyncio_client.adapters.api.application_resource_api import (
    ApplicationResourceApiAdapter,
)
from conductor.asyncio_client.adapters.api.authorization_resource_api import (
    AuthorizationResourceApiAdapter,
)
from conductor.asyncio_client.adapters.api.group_resource_api import GroupResourceApiAdapter
from conductor.asyncio_client.adapters.api.integration_resource_api import (
    IntegrationResourceApiAdapter,
)
from conductor.asyncio_client.adapters.api.metadata_resource_api import MetadataResourceApiAdapter
from conductor.asyncio_client.adapters.api.prompt_resource_api import PromptResourceApiAdapter
from conductor.asyncio_client.adapters.api.scheduler_resource_api import SchedulerResourceApiAdapter
from conductor.asyncio_client.adapters.api.schema_resource_api import SchemaResourceApiAdapter
from conductor.asyncio_client.adapters.api.secret_resource_api import SecretResourceApiAdapter
from conductor.asyncio_client.adapters.api.tags_api import TagsApiAdapter
from conductor.asyncio_client.adapters.api.task_resource_api import TaskResourceApiAdapter
from conductor.asyncio_client.adapters.api.user_resource_api import UserResourceApiAdapter
from conductor.asyncio_client.adapters.api.workflow_resource_api import WorkflowResourceApiAdapter
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.adapters import ApiClient


class OrkesBaseClient:
    """
    Base client class for all Orkes Conductor clients.

    This class provides common functionality and API client initialization
    for all Orkes clients, including environment variable support and
    worker properties configuration.
    """

    def __init__(self, configuration: Configuration, api_client: ApiClient):
        """
        Initialize the base client with configuration.

        Parameters:
        -----------
        configuration : Configuration
            Configuration adapter with environment variable support
        """
        # Access the underlying HTTP configuration for API client initialization
        self.api_client = api_client
        self.configuration = configuration

        self.logger = logging.getLogger(__name__)

        # Initialize all API clients
        self.metadata_api = MetadataResourceApiAdapter(self.api_client)
        self.task_api = TaskResourceApiAdapter(self.api_client)
        self.workflow_api = WorkflowResourceApiAdapter(self.api_client)
        self.application_api = ApplicationResourceApiAdapter(self.api_client)
        self.secret_api = SecretResourceApiAdapter(self.api_client)
        self.user_api = UserResourceApiAdapter(self.api_client)
        self.group_api = GroupResourceApiAdapter(self.api_client)
        self.authorization_api = AuthorizationResourceApiAdapter(self.api_client)
        self.scheduler_api = SchedulerResourceApiAdapter(self.api_client)
        self.tags_api = TagsApiAdapter(self.api_client)
        self.integration_api = IntegrationResourceApiAdapter(self.api_client)
        self.prompt_api = PromptResourceApiAdapter(self.api_client)
        self.schema_api = SchemaResourceApiAdapter(self.api_client)
