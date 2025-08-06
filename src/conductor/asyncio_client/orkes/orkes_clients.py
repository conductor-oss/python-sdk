from __future__ import annotations

from typing import Optional

from conductor.asyncio_client.http.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_authorization_client import (
    OrkesAuthorizationClient,
)
from conductor.asyncio_client.orkes.orkes_integration_client import (
    OrkesIntegrationClient,
)
from conductor.asyncio_client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.asyncio_client.orkes.orkes_prompt_client import OrkesPromptClient
from conductor.asyncio_client.orkes.orkes_scheduler_client import OrkesSchedulerClient
from conductor.asyncio_client.orkes.orkes_schema_client import OrkesSchemaClient
from conductor.asyncio_client.orkes.orkes_secret_client import OrkesSecretClient
from conductor.asyncio_client.orkes.orkes_task_client import OrkesTaskClient
from conductor.asyncio_client.orkes.orkes_workflow_client import OrkesWorkflowClient


class OrkesClients:
    """
    Central factory class for creating and managing Orkes Conductor client instances.

    This class provides a unified interface for accessing all available Orkes Conductor
    client services including workflow management, task operations, metadata handling,
    user authorization, secret management, and more.

    The OrkesClients class acts as a factory that creates client instances on demand,
    ensuring that all clients share the same configuration while providing access to
    different aspects of the Conductor platform.

    Example:
    --------
    ```python
    from conductor.asyncio_client.http.configuration import Configuration
    from conductor.asyncio_client.orkes.orkes_clients import OrkesClients

    # Create with default configuration
    orkes = OrkesClients()

    # Or with custom configuration
    config = Configuration(
        server_api_url='https://api.orkes.io',
        authentication_settings=authentication_settings
    )
    orkes = OrkesClients(config)

    # Access different services
    workflow_client = orkes.get_workflow_client()
    task_client = orkes.get_task_client()
    auth_client = orkes.get_authorization_client()
    ```

    Attributes:
    -----------
    configuration : Configuration
        The HTTP configuration used by all client instances
    """

    def __init__(self, configuration: Optional[Configuration] = None):
        """
        Initialize the OrkesClients factory with the provided configuration.

        Parameters:
        -----------
        configuration : Configuration, optional
            HTTP configuration containing server URL, authentication settings,
            and other connection parameters. If None, a default Configuration
            instance will be created.
        """
        if configuration is None:
            configuration = Configuration()
        self.configuration = configuration

    def get_workflow_client(self) -> OrkesWorkflowClient:
        """
        Create and return a workflow management client.

        The workflow client provides comprehensive workflow orchestration capabilities
        including starting, stopping, pausing, resuming workflows, as well as
        querying workflow status and managing workflow execution state.

        Returns:
        --------
        OrkesWorkflowClient
            Client for workflow operations including:
            - Starting and executing workflows
            - Controlling workflow lifecycle (pause, resume, terminate)
            - Querying workflow status and execution history
            - Managing workflow state and variables
        """
        return OrkesWorkflowClient(self.configuration)

    def get_authorization_client(self) -> OrkesAuthorizationClient:
        """
        Create and return an authorization and user management client.

        The authorization client handles user authentication, authorization,
        group management, application management, and permission controls
        within the Orkes Conductor platform.

        Returns:
        --------
        OrkesAuthorizationClient
            Client for authorization operations including:
            - User creation, modification, and deletion
            - Group management and user-group associations
            - Application management and access control
            - Permission granting and revocation
        """
        return OrkesAuthorizationClient(self.configuration)

    def get_metadata_client(self) -> OrkesMetadataClient:
        """
        Create and return a metadata management client.

        The metadata client manages workflow and task definitions, allowing you
        to register, update, retrieve, and delete workflow and task metadata
        that defines the structure and behavior of your workflows.

        Returns:
        --------
        OrkesMetadataClient
            Client for metadata operations including:
            - Task definition management
            - Workflow definition management
            - Schema validation and versioning
            - Metadata querying and retrieval
        """
        return OrkesMetadataClient(self.configuration)

    def get_scheduler_client(self) -> OrkesSchedulerClient:
        """
        Create and return a workflow scheduling client.

        The scheduler client manages workflow schedules, allowing you to create
        recurring workflows, manage scheduling policies, and control when
        workflows are automatically triggered.

        Returns:
        --------
        OrkesSchedulerClient
            Client for scheduling operations including:
            - Creating and managing workflow schedules
            - Setting up recurring workflow executions
            - Managing schedule policies and triggers
            - Querying schedule execution history
        """
        return OrkesSchedulerClient(self.configuration)

    def get_secret_client(self) -> OrkesSecretClient:
        """
        Create and return a secret management client.

        The secret client provides secure storage and retrieval of sensitive
        information such as API keys, passwords, and configuration values
        that your workflows and tasks need to access securely.

        Returns:
        --------
        OrkesSecretClient
            Client for secret operations including:
            - Storing and retrieving secrets securely
            - Managing secret lifecycle and expiration
            - Controlling access to sensitive information
            - Organizing secrets with tags and metadata
        """
        return OrkesSecretClient(self.configuration)

    def get_task_client(self) -> OrkesTaskClient:
        """
        Create and return a task management client.

        The task client manages individual task executions within workflows,
        providing capabilities to poll for tasks, update task status, and
        manage task queues and worker interactions.

        Returns:
        --------
        OrkesTaskClient
            Client for task operations including:
            - Polling for available tasks
            - Updating task execution status
            - Managing task queues and worker assignments
            - Retrieving task execution history and logs
        """
        return OrkesTaskClient(self.configuration)

    def get_integration_client(self) -> OrkesIntegrationClient:
        """
        Create and return an integration management client.

        The integration client manages external system integrations,
        allowing you to configure and control how Conductor interacts
        with third-party services and APIs.

        Returns:
        --------
        OrkesIntegrationClient
            Client for integration operations including:
            - Managing integration configurations
            - Setting up external service connections
            - Controlling integration authentication
            - Managing integration providers and APIs
        """
        return OrkesIntegrationClient(self.configuration)

    def get_prompt_client(self) -> OrkesPromptClient:
        """
        Create and return a prompt template management client.

        The prompt client manages AI/LLM prompt templates used in workflows,
        allowing you to create, test, and manage reusable prompt templates
        for AI-powered workflow tasks.

        Returns:
        --------
        OrkesPromptClient
            Client for prompt operations including:
            - Creating and managing prompt templates
            - Testing prompt templates with sample data
            - Versioning and organizing prompts
            - Managing prompt template metadata and tags
        """
        return OrkesPromptClient(self.configuration)

    def get_schema_client(self) -> OrkesSchemaClient:
        """
        Create and return a schema management client.

        The schema client manages data schemas and validation rules
        used throughout the Conductor platform to ensure data consistency
        and validate workflow inputs, outputs, and configurations.

        Returns:
        --------
        OrkesSchemaClient
            Client for schema operations including:
            - Creating and managing data schemas
            - Validating data against schemas
            - Versioning schema definitions
            - Managing schema metadata and documentation
        """
        return OrkesSchemaClient(self.configuration)
