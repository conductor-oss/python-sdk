import logging

from conductor.asyncio_client.adapters.api.application_resource_api import \
    ApplicationResourceApi
from conductor.asyncio_client.adapters.api.authorization_resource_api import \
    AuthorizationResourceApi
from conductor.asyncio_client.adapters.api.group_resource_api import \
    GroupResourceApi
from conductor.asyncio_client.adapters.api.integration_resource_api import \
    IntegrationResourceApi
from conductor.asyncio_client.adapters.api.metadata_resource_api import \
    MetadataResourceApi
from conductor.asyncio_client.adapters.api.prompt_resource_api import \
    PromptResourceApi
from conductor.asyncio_client.adapters.api.scheduler_resource_api import \
    SchedulerResourceApi
from conductor.asyncio_client.adapters.api.schema_resource_api import \
    SchemaResourceApi
from conductor.asyncio_client.adapters.api.secret_resource_api import \
    SecretResourceApi
from conductor.asyncio_client.adapters.api.tags_api import TagsApi
from conductor.asyncio_client.adapters.api.task_resource_api import \
    TaskResourceApi
from conductor.asyncio_client.adapters.api.user_resource_api import \
    UserResourceApi
from conductor.asyncio_client.adapters.api.workflow_resource_api import \
    WorkflowResourceApi
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.http.api_client import ApiClient


class OrkesBaseClient:
    """
    Base client class for all Orkes Conductor clients.

    This class provides common functionality and API client initialization
    for all Orkes clients, including environment variable support and
    worker properties configuration.
    """

    def __init__(self, configuration: Configuration):
        """
        Initialize the base client with configuration.

        Parameters:
        -----------
        configuration : Configuration
            Configuration adapter with environment variable support
        """
        # Access the underlying HTTP configuration for API client initialization
        self.api_client = ApiClient(configuration._http_config)
        self.configuration = configuration

        self.logger = logging.getLogger(__name__)

        # Initialize all API clients
        self.metadata_api = MetadataResourceApi(self.api_client)
        self.task_api = TaskResourceApi(self.api_client)
        self.workflow_api = WorkflowResourceApi(self.api_client)
        self.application_api = ApplicationResourceApi(self.api_client)
        self.secret_api = SecretResourceApi(self.api_client)
        self.user_api = UserResourceApi(self.api_client)
        self.group_api = GroupResourceApi(self.api_client)
        self.authorization_api = AuthorizationResourceApi(self.api_client)
        self.scheduler_api = SchedulerResourceApi(self.api_client)
        self.tags_api = TagsApi(self.api_client)
        self.integration_api = IntegrationResourceApi(self.api_client)
        self.prompt_api = PromptResourceApi(self.api_client)
        self.schema_api = SchemaResourceApi(self.api_client)
