import logging

from conductor.client.configuration.configuration import Configuration
from conductor.client.adapters.api.application_resource_api_adapter import ApplicationResourceApiAdapter as ApplicationResourceApi
from conductor.client.adapters.api.authorization_resource_api_adapter import AuthorizationResourceApiAdapter as AuthorizationResourceApi
from conductor.client.adapters.api.group_resource_api_adapter import GroupResourceApiAdapter as GroupResourceApi
from conductor.client.adapters.api.integration_resource_api_adapter import IntegrationResourceApiAdapter as IntegrationResourceApi
from conductor.client.adapters.api.metadata_resource_api_adapter import MetadataResourceApiAdapter as MetadataResourceApi
from conductor.client.adapters.api.prompt_resource_api_adapter import PromptResourceApiAdapter as PromptResourceApi
from conductor.client.adapters.api.scheduler_resource_api_adapter import SchedulerResourceApiAdapter as SchedulerResourceApi
from conductor.client.adapters.api.schema_resource_api_adapter import SchemaResourceApiAdapter as SchemaResourceApi
from conductor.client.adapters.api.secret_resource_api_adapter import SecretResourceApiAdapter as SecretResourceApi
from conductor.client.adapters.api.service_registry_resource_api_adapter import ServiceRegistryResourceApiAdapter as ServiceRegistryResourceApi
from conductor.client.adapters.api.task_resource_api_adapter import TaskResourceApiAdapter as TaskResourceApi
from conductor.client.adapters.api.user_resource_api_adapter import UserResourceApiAdapter as UserResourceApi
from conductor.client.adapters.api.workflow_resource_api_adapter import WorkflowResourceApiAdapter as WorkflowResourceApi
from conductor.client.http.api_client import ApiClient
from conductor.client.adapters.api.tags_api_adapter import TagsApiAdapter as TagsApi


class OrkesBaseClient(object):
    def __init__(self, configuration: Configuration):
        self.api_client = ApiClient(configuration)
        self.logger = logging.getLogger(
            Configuration.get_logging_formatted_name(__name__)
        )
        self.metadataResourceApi = MetadataResourceApi(self.api_client)
        self.taskResourceApi = TaskResourceApi(self.api_client)
        self.workflowResourceApi = WorkflowResourceApi(self.api_client)
        self.applicationResourceApi = ApplicationResourceApi(self.api_client)
        self.secretResourceApi = SecretResourceApi(self.api_client)
        self.userResourceApi = UserResourceApi(self.api_client)
        self.groupResourceApi = GroupResourceApi(self.api_client)
        self.authorizationResourceApi = AuthorizationResourceApi(self.api_client)
        self.schedulerResourceApi = SchedulerResourceApi(self.api_client)
        self.tagsApi = TagsApi(self.api_client)
        self.integrationApi = IntegrationResourceApi(self.api_client)
        self.promptApi = PromptResourceApi(self.api_client)
        self.schemaApi = SchemaResourceApi(self.api_client)
        self.serviceRegistryResourceApi = ServiceRegistryResourceApi(self.api_client)
