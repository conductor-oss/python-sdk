from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Optional

from pydantic import Field, field_validator
from typing_extensions import Self

from conductor.asyncio_client.http.models import IntegrationDefFormField


class IntegrationDefFormFieldAdapter(IntegrationDefFormField):
    value_options: Optional[List["OptionAdapter"]] = Field(default=None, alias="valueOptions")
    depends_on: Optional[List["IntegrationDefFormFieldAdapter"]] = Field(
        default=None, alias="dependsOn"
    )
    __properties: ClassVar[List[str]] = [
        "defaultValue",
        "description",
        "fieldName",
        "fieldType",
        "label",
        "optional",
        "value",
        "valueOptions",
        "dependsOn",
    ]

    @field_validator("field_name")
    def field_name_validate_enum(cls, value):
        """Validates the enum"""
        if value is None:
            return value

        if value not in {
            "api_key",
            "authenticationType",
            "authUrl",
            "awsAccountId",
            "batchPollConsumersCount",
            "batchSize",
            "batchWaitTime",
            "betaVersion",
            "channel",
            "cipherSuite",
            "completionsPath",
            "connectionPoolSize",
            "connectionType",
            "consumer",
            "consumer_type",
            "datasourceURL",
            "dimensions",
            "distance_metric",
            "endpoint",
            "environment",
            "externalId",
            "file",
            "groupId",
            "header",
            "indexing_method",
            "indexName",
            "inverted_list_count",
            "jdbcDriver",
            "keyStoreLocation",
            "keyStorePassword",
            "mechanism",
            "namespace",
            "organizationId",
            "password",
            "port",
            "projectName",
            "protocol",
            "pubSubMethod",
            "publisher",
            "pullBatchWaitMillis",
            "pullPeriod",
            "queueManager",
            "region",
            "roleArn",
            "schemaRegistryApiKey",
            "schemaRegistryApiSecret",
            "schemaRegistryAuthType",
            "schemaRegistryUrl",
            "serviceAccountCredentials",
            "stream",
            "subscription",
            "tls",
            "tlsFile",
            "truststoreAuthenticationType",
            "user",
            "valueSubjectNameStrategy",
            "version",
            "visibilityTimeout",
            "oAuth2RefreshToken",
            "oAuth2AuthCode",
            "oAuth2TokenExpiresAt",
            "oAuth2RedirectUri",
            "oAuth2Scope",
            "oAuth2Provider",
            "oAuth2AccessToken",
        }:
            raise ValueError(
                "must be one of enum values ("
                "'api_key', 'authenticationType', 'authUrl', 'awsAccountId', "
                "'batchPollConsumersCount', 'batchSize', 'batchWaitTime', "
                "'betaVersion', 'channel', 'cipherSuite', 'completionsPath', "
                "'connectionPoolSize', 'connectionType', 'consumer', 'consumer_type', "
                "'datasourceURL', 'dimensions', 'distance_metric', 'endpoint', "
                "'environment', 'externalId', 'file', 'groupId', 'header', "
                "'indexing_method', 'indexName', 'inverted_list_count', 'jdbcDriver', "
                "'keyStoreLocation', 'keyStorePassword', 'mechanism', 'namespace', "
                "'organizationId', 'password', 'port', 'projectName', 'protocol', "
                "'pubSubMethod', 'publisher', 'pullBatchWaitMillis', 'pullPeriod', "
                "'queueManager', 'region', 'roleArn', 'schemaRegistryApiKey', "
                "'schemaRegistryApiSecret', 'schemaRegistryAuthType', 'schemaRegistryUrl', "
                "'serviceAccountCredentials', 'stream', 'subscription', 'tls', 'tlsFile', "
                "'truststoreAuthenticationType', 'user', 'valueSubjectNameStrategy', "
                "'version', 'visibilityTimeout', 'oAuth2RefreshToken', 'oAuth2AuthCode', "
                "'oAuth2TokenExpiresAt', 'oAuth2RedirectUri', 'oAuth2Scope', 'oAuth2Provider', 'oAuth2AccessToken'"
                ")"
            )

        return value

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of IntegrationDefFormField from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "defaultValue": obj.get("defaultValue"),
                "description": obj.get("description"),
                "fieldName": obj.get("fieldName"),
                "fieldType": obj.get("fieldType"),
                "label": obj.get("label"),
                "optional": obj.get("optional"),
                "value": obj.get("value"),
                "valueOptions": (
                    [OptionAdapter.from_dict(_item) for _item in obj["valueOptions"]]
                    if obj.get("valueOptions") is not None
                    else None
                ),
                "dependsOn": (
                    [IntegrationDefFormFieldAdapter.from_dict(_item) for _item in obj["dependsOn"]]
                    if obj.get("dependsOn") is not None
                    else None
                ),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.option_adapter import (  # noqa: E402
    OptionAdapter,
)

IntegrationDefFormFieldAdapter.model_rebuild(raise_errors=False)
