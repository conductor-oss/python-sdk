import logging
import warnings
from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated

from conductor.asyncio_client.adapters import ApiClient
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
from conductor.asyncio_client.adapters.api.event_resource_api import EventResourceApiAdapter
from conductor.asyncio_client.adapters.api.event_execution_resource_api import (
    EventExecutionResourceApiAdapter,
)
from conductor.asyncio_client.configuration.configuration import Configuration


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
        self._metadata_api = MetadataResourceApiAdapter(self.api_client)
        self.__task_api = TaskResourceApiAdapter(self.api_client)
        self.__workflow_api = WorkflowResourceApiAdapter(self.api_client)
        self.__application_api = ApplicationResourceApiAdapter(self.api_client)
        self.__secret_api = SecretResourceApiAdapter(self.api_client)
        self.__user_api = UserResourceApiAdapter(self.api_client)
        self.__group_api = GroupResourceApiAdapter(self.api_client)
        self.__authorization_api = AuthorizationResourceApiAdapter(self.api_client)
        self.__scheduler_api = SchedulerResourceApiAdapter(self.api_client)
        self.__tags_api = TagsApiAdapter(self.api_client)
        self.__integration_api = IntegrationResourceApiAdapter(self.api_client)
        self.__prompt_api = PromptResourceApiAdapter(self.api_client)
        self.__schema_api = SchemaResourceApiAdapter(self.api_client)

    @property
    @typing_deprecated(
        "metadata_api is deprecated; use OrkesMetadataClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "metadata_api is deprecated; use OrkesMetadataClient instead. "
        "This attribute will be removed in a future version."
    )
    def metadata_api(self) -> MetadataResourceApiAdapter:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesMetadataClient` methods instead.
        """
        warnings.warn(
            "'metadata_api' is deprecated and will be removed in a future release. "
            "Use `OrkesMetadataClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._metadata_api

    @property
    @typing_deprecated(
        "task_api is deprecated; use OrkesTaskClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "task_api is deprecated; use OrkesTaskClient instead. "
        "This attribute will be removed in a future version."
    )
    def task_api(self) -> TaskResourceApiAdapter:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesTaskClient` methods instead.
        """
        warnings.warn(
            "'task_api' is deprecated and will be removed in a future release. "
            "Use `OrkesTaskClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__task_api

    @property
    @typing_deprecated(
        "workflow_api is deprecated; use OrkesWorkflowClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "workflow_api is deprecated; use OrkesWorkflowClient instead. "
        "This attribute will be removed in a future version."
    )
    def workflow_api(self) -> WorkflowResourceApiAdapter:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesWorkflowClient` methods instead.
        """
        warnings.warn(
            "'workflow_api' is deprecated and will be removed in a future release. "
            "Use `OrkesWorkflowClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__workflow_api

    @property
    @typing_deprecated(
        "application_api is deprecated; use OrkesAuthorizationClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "application_api is deprecated; use OrkesAuthorizationClient instead. "
        "This attribute will be removed in a future version."
    )
    def application_api(self) -> ApplicationResourceApiAdapter:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesAuthorizationClient` methods instead.
        """
        warnings.warn(
            "'application_api' is deprecated and will be removed in a future release. "
            "Use `OrkesAuthorizationClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__application_api

    @property
    @typing_deprecated(
        "secret_api is deprecated; use OrkesSecretClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "secret_api is deprecated; use OrkesSecretClient instead. "
        "This attribute will be removed in a future version."
    )
    def secret_api(self) -> SecretResourceApiAdapter:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesSecretClient` methods instead.
        """
        warnings.warn(
            "'secret_api' is deprecated and will be removed in a future release. "
            "Use `OrkesSecretClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__secret_api

    @property
    @typing_deprecated(
        "user_api is deprecated; use OrkesAuthorizationClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "user_api is deprecated; use OrkesAuthorizationClient instead. "
        "This attribute will be removed in a future version."
    )
    def user_api(self) -> UserResourceApiAdapter:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesAuthorizationClient` methods instead.
        """
        warnings.warn(
            "'user_api' is deprecated and will be removed in a future release. "
            "Use `OrkesAuthorizationClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__user_api

    @property
    @typing_deprecated(
        "group_api is deprecated; use OrkesAuthorizationClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "group_api is deprecated; use OrkesAuthorizationClient instead. "
        "This attribute will be removed in a future version."
    )
    def group_api(self) -> GroupResourceApiAdapter:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesAuthorizationClient` methods instead.
        """
        warnings.warn(
            "'group_api' is deprecated and will be removed in a future release. "
            "Use `OrkesAuthorizationClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__group_api

    @property
    @typing_deprecated(
        "authorization_api is deprecated; use OrkesAuthorizationClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "authorization_api is deprecated; use OrkesAuthorizationClient instead. "
        "This attribute will be removed in a future version."
    )
    def authorization_api(self) -> AuthorizationResourceApiAdapter:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesAuthorizationClient` methods instead.
        """
        warnings.warn(
            "'authorization_api' is deprecated and will be removed in a future release. "
            "Use `OrkesAuthorizationClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__authorization_api

    @property
    @typing_deprecated(
        "scheduler_api is deprecated; use OrkesSchedulerClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "scheduler_api is deprecated; use OrkesSchedulerClient instead. "
        "This attribute will be removed in a future version."
    )
    def scheduler_api(self) -> SchedulerResourceApiAdapter:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesSchedulerClient` methods instead.
        """
        warnings.warn(
            "'scheduler_api' is deprecated and will be removed in a future release. "
            "Use `OrkesSchedulerClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__scheduler_api

    @property
    @typing_deprecated(
        "tags_api is deprecated; use OrkesTagsClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "tags_api is deprecated; use OrkesTagsClient instead. "
        "This attribute will be removed in a future version."
    )
    def tags_api(self) -> TagsApiAdapter:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesTagsClient` methods instead.
        """
        warnings.warn(
            "'tags_api' is deprecated and will be removed in a future release. "
            "Use `OrkesTagsClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__tags_api

    @property
    @typing_deprecated(
        "integration_api is deprecated; use OrkesIntegrationClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "integration_api is deprecated; use OrkesIntegrationClient instead. "
        "This attribute will be removed in a future version."
    )
    def integration_api(self) -> IntegrationResourceApiAdapter:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesIntegrationClient` methods instead.
        """
        warnings.warn(
            "'integration_api' is deprecated and will be removed in a future release. "
            "Use `OrkesIntegrationClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__integration_api

    @property
    @typing_deprecated(
        "prompt_api is deprecated; use OrkesPromptClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "prompt_api is deprecated; use OrkesPromptClient instead. "
        "This attribute will be removed in a future version."
    )
    def prompt_api(self) -> PromptResourceApiAdapter:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesPromptClient` methods instead.
        """
        warnings.warn(
            "'prompt_api' is deprecated and will be removed in a future release. "
            "Use `OrkesPromptClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__prompt_api

    @property
    @typing_deprecated(
        "schema_api is deprecated; use OrkesSchemaClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "schema_api is deprecated; use OrkesSchemaClient instead. "
        "This attribute will be removed in a future version."
    )
    def schema_api(self) -> SchemaResourceApiAdapter:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesSchemaClient` methods instead.
        """
        warnings.warn(
            "'schema_api' is deprecated and will be removed in a future release. "
            "Use `OrkesSchemaClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__schema_api
