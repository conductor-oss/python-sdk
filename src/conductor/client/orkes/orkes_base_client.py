import logging
import warnings
from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api.application_resource_api import ApplicationResourceApi
from conductor.client.http.api.authorization_resource_api import AuthorizationResourceApi
from conductor.client.http.api.group_resource_api import GroupResourceApi
from conductor.client.http.api.integration_resource_api import IntegrationResourceApi
from conductor.client.http.api.metadata_resource_api import MetadataResourceApi
from conductor.client.http.api.prompt_resource_api import PromptResourceApi
from conductor.client.http.api.scheduler_resource_api import SchedulerResourceApi
from conductor.client.http.api.schema_resource_api import SchemaResourceApi
from conductor.client.http.api.secret_resource_api import SecretResourceApi
from conductor.client.http.api.service_registry_resource_api import ServiceRegistryResourceApi
from conductor.client.http.api.tags_api import TagsApi
from conductor.client.http.api.task_resource_api import TaskResourceApi
from conductor.client.http.api.user_resource_api import UserResourceApi
from conductor.client.http.api.workflow_resource_api import WorkflowResourceApi
from conductor.client.http.api_client import ApiClient
from conductor.client.http.api.event_resource_api import EventResourceApi


class OrkesBaseClient(object):
    def __init__(self, configuration: Configuration):
        self.api_client = ApiClient(configuration)
        self.logger = logging.getLogger(Configuration.get_logging_formatted_name(__name__))

        self._metadata_api = MetadataResourceApi(self.api_client)
        self._task_api = TaskResourceApi(self.api_client)
        self._workflow_api = WorkflowResourceApi(self.api_client)
        self._application_api = ApplicationResourceApi(self.api_client)
        self._secret_api = SecretResourceApi(self.api_client)
        self._user_api = UserResourceApi(self.api_client)
        self._group_api = GroupResourceApi(self.api_client)
        self._authorization_api = AuthorizationResourceApi(self.api_client)
        self._scheduler_api = SchedulerResourceApi(self.api_client)
        self._tags_api = TagsApi(self.api_client)
        self._integration_api = IntegrationResourceApi(self.api_client)
        self._prompt_api = PromptResourceApi(self.api_client)
        self._schema_api = SchemaResourceApi(self.api_client)
        self._service_registry_api = ServiceRegistryResourceApi(self.api_client)
        self._event_api = EventResourceApi(self.api_client)

    @property
    @typing_deprecated(
        "metadataResourceApi is deprecated; use OrkesMetadataClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "metadataResourceApi is deprecated; use OrkesMetadataClient instead. "
        "This attribute will be removed in a future version."
    )
    def metadataResourceApi(self) -> MetadataResourceApi:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesMetadataClient` methods instead.
        """
        warnings.warn(
            "'metadataResourceApi' is deprecated and will be removed in a future release. "
            "Use `OrkesMetadataClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._metadata_api

    @property
    @typing_deprecated(
        "taskResourceApi is deprecated; use OrkesTaskClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "taskResourceApi is deprecated; use OrkesTaskClient instead. "
        "This attribute will be removed in a future version."
    )
    def taskResourceApi(self) -> TaskResourceApi:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesTaskClient` methods instead.
        """
        warnings.warn(
            "'taskResourceApi' is deprecated and will be removed in a future release. "
            "Use `OrkesTaskClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._task_api

    @property
    @typing_deprecated(
        "workflowResourceApi is deprecated; use OrkesWorkflowClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "workflowResourceApi is deprecated; use OrkesWorkflowClient instead. "
        "This attribute will be removed in a future version."
    )
    def workflowResourceApi(self) -> WorkflowResourceApi:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesWorkflowClient` methods instead.
        """
        warnings.warn(
            "'workflowResourceApi' is deprecated and will be removed in a future release. "
            "Use `OrkesWorkflowClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._workflow_api

    @property
    @typing_deprecated(
        "applicationResourceApi is deprecated; use OrkesAuthorizationClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "applicationResourceApi is deprecated; use OrkesAuthorizationClient instead. "
        "This attribute will be removed in a future version."
    )
    def applicationResourceApi(self) -> ApplicationResourceApi:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesAuthorizationClient` methods instead.
        """
        warnings.warn(
            "'applicationResourceApi' is deprecated and will be removed in a future release. "
            "Use `OrkesAuthorizationClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._application_api

    @property
    @typing_deprecated(
        "secretResourceApi is deprecated; use OrkesSecretClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "secretResourceApi is deprecated; use OrkesSecretClient instead. "
        "This attribute will be removed in a future version."
    )
    def secretResourceApi(self) -> SecretResourceApi:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesSecretClient` methods instead.
        """
        warnings.warn(
            "'secretResourceApi' is deprecated and will be removed in a future release. "
            "Use `OrkesSecretClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._secret_api

    @property
    @typing_deprecated(
        "userResourceApi is deprecated; use OrkesAuthorizationClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "userResourceApi is deprecated; use OrkesAuthorizationClient instead. "
        "This attribute will be removed in a future version."
    )
    def userResourceApi(self) -> UserResourceApi:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesAuthorizationClient` methods instead.
        """
        warnings.warn(
            "'userResourceApi' is deprecated and will be removed in a future release. "
            "Use `OrkesAuthorizationClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._user_api

    @property
    @typing_deprecated(
        "groupResourceApi is deprecated; use OrkesAuthorizationClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "groupResourceApi is deprecated; use OrkesAuthorizationClient instead. "
        "This attribute will be removed in a future version."
    )
    def groupResourceApi(self) -> GroupResourceApi:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesAuthorizationClient` methods instead.
        """
        warnings.warn(
            "'groupResourceApi' is deprecated and will be removed in a future release. "
            "Use `OrkesAuthorizationClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._group_api

    @property
    @typing_deprecated(
        "authorizationResourceApi is deprecated; use OrkesAuthorizationClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "authorizationResourceApi is deprecated; use OrkesAuthorizationClient instead. "
        "This attribute will be removed in a future version."
    )
    def authorizationResourceApi(self) -> AuthorizationResourceApi:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesAuthorizationClient` methods instead.
        """
        warnings.warn(
            "'authorizationResourceApi' is deprecated and will be removed in a future release. "
            "Use `OrkesAuthorizationClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._authorization_api

    @property
    @typing_deprecated(
        "schedulerResourceApi is deprecated; use OrkesSchedulerClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "schedulerResourceApi is deprecated; use OrkesSchedulerClient instead. "
        "This attribute will be removed in a future version."
    )
    def schedulerResourceApi(self) -> SchedulerResourceApi:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesSchedulerClient` methods instead.
        """
        warnings.warn(
            "'schedulerResourceApi' is deprecated and will be removed in a future release. "
            "Use `OrkesSchedulerClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._scheduler_api

    @property
    @typing_deprecated(
        "tagsApi is deprecated; use OrkesTagsClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "tagsApi is deprecated; use OrkesTagsClient instead. "
        "This attribute will be removed in a future version."
    )
    def tagsApi(self) -> TagsApi:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesTagsClient` methods instead.
        """
        warnings.warn(
            "'tagsApi' is deprecated and will be removed in a future release. "
            "Use `OrkesTagsClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._tags_api

    @property
    @typing_deprecated(
        "integrationApi is deprecated; use OrkesIntegrationClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "integrationApi is deprecated; use OrkesIntegrationClient instead. "
        "This attribute will be removed in a future version."
    )
    def integrationApi(self) -> IntegrationResourceApi:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesIntegrationClient` methods instead.
        """
        warnings.warn(
            "'integrationApi' is deprecated and will be removed in a future release. "
            "Use `OrkesIntegrationClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._integration_api

    @property
    @typing_deprecated(
        "promptApi is deprecated; use OrkesPromptClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "promptApi is deprecated; use OrkesPromptClient instead. "
        "This attribute will be removed in a future version."
    )
    def promptApi(self) -> PromptResourceApi:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesPromptClient` methods instead.
        """
        warnings.warn(
            "'promptApi' is deprecated and will be removed in a future release. "
            "Use `OrkesPromptClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._prompt_api

    @property
    @typing_deprecated(
        "schemaApi is deprecated; use OrkesSchemaClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "schemaApi is deprecated; use OrkesSchemaClient instead. "
        "This attribute will be removed in a future version."
    )
    def schemaApi(self) -> SchemaResourceApi:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesSchemaClient` methods instead.
        """
        warnings.warn(
            "'schemaApi' is deprecated and will be removed in a future release. "
            "Use `OrkesSchemaClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._schema_api

    @property
    @typing_deprecated(
        "serviceRegistryResourceApi is deprecated; use OrkesServiceRegistryClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "serviceRegistryResourceApi is deprecated; use OrkesServiceRegistryClient instead. "
        "This attribute will be removed in a future version."
    )
    def serviceRegistryResourceApi(self) -> ServiceRegistryResourceApi:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesServiceRegistryClient` methods instead.
        """
        warnings.warn(
            "'serviceRegistryResourceApi' is deprecated and will be removed in a future release. "
            "Use `OrkesServiceRegistryClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._service_registry_api

    @property
    @typing_deprecated(
        "eventResourceApi is deprecated; use OrkesEventClient instead. "
        "This attribute will be removed in a future version."
    )
    @deprecated(
        "eventResourceApi is deprecated; use OrkesEventClient instead. "
        "This attribute will be removed in a future version."
    )
    def eventResourceApi(self) -> EventResourceApi:
        """
        Deprecated: attribute-style access maintained for backward compatibility.
        Prefer using `OrkesEventClient` methods instead.
        """
        warnings.warn(
            "'eventResourceApi' is deprecated and will be removed in a future release. "
            "Use `OrkesEventClient` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._event_api
