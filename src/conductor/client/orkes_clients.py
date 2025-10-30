from __future__ import annotations

from typing import Optional

from conductor.client.authorization_client import AuthorizationClient
from conductor.client.configuration.configuration import Configuration
from conductor.client.integration_client import IntegrationClient
from conductor.client.metadata_client import MetadataClient
from conductor.client.orkes.orkes_authorization_client import OrkesAuthorizationClient
from conductor.client.orkes.orkes_integration_client import OrkesIntegrationClient
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.client.orkes.orkes_prompt_client import OrkesPromptClient
from conductor.client.orkes.orkes_scheduler_client import OrkesSchedulerClient
from conductor.client.orkes.orkes_schema_client import OrkesSchemaClient
from conductor.client.orkes.orkes_secret_client import OrkesSecretClient
from conductor.client.orkes.orkes_task_client import OrkesTaskClient
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient
from conductor.client.orkes.orkes_event_client import OrkesEventClient
from conductor.client.prompt_client import PromptClient
from conductor.client.scheduler_client import SchedulerClient
from conductor.client.schema_client import SchemaClient
from conductor.client.secret_client import SecretClient
from conductor.client.task_client import TaskClient
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from conductor.client.workflow_client import WorkflowClient


class OrkesClients:
    def __init__(self, configuration: Optional[Configuration] = None):
        if configuration is None:
            configuration = Configuration()
        self.configuration = configuration

    def get_workflow_client(self) -> WorkflowClient:
        return OrkesWorkflowClient(self.configuration)

    def get_authorization_client(self) -> AuthorizationClient:
        return OrkesAuthorizationClient(self.configuration)

    def get_metadata_client(self) -> MetadataClient:
        return OrkesMetadataClient(self.configuration)

    def get_scheduler_client(self) -> SchedulerClient:
        return OrkesSchedulerClient(self.configuration)

    def get_secret_client(self) -> SecretClient:
        return OrkesSecretClient(self.configuration)

    def get_task_client(self) -> TaskClient:
        return OrkesTaskClient(self.configuration)

    def get_integration_client(self) -> IntegrationClient:
        return OrkesIntegrationClient(self.configuration)

    def get_workflow_executor(self) -> WorkflowExecutor:
        return WorkflowExecutor(self.configuration)

    def get_prompt_client(self) -> PromptClient:
        return OrkesPromptClient(self.configuration)

    def get_schema_client(self) -> SchemaClient:
        return OrkesSchemaClient(self.configuration)

    def get_event_client(self) -> OrkesEventClient:
        return OrkesEventClient(self.configuration)
