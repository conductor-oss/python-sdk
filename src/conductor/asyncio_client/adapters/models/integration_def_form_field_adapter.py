from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Optional

from pydantic import Field, field_validator
from typing_extensions import Self

from conductor.asyncio_client.http.models import IntegrationDefFormField


class IntegrationDefFormFieldAdapter(IntegrationDefFormField):
    value_options: Optional[List["OptionAdapter"]] = Field(
        default=None, alias="valueOptions"
    )
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

        if value not in set(
            [
                "api_key",
                "user",
                "header",
                "endpoint",
                "authUrl",
                "environment",
                "projectName",
                "indexName",
                "publisher",
                "password",
                "namespace",
                "batchSize",
                "batchWaitTime",
                "visibilityTimeout",
                "connectionType",
                "connectionPoolSize",
                "consumer",
                "stream",
                "batchPollConsumersCount",
                "consumer_type",
                "region",
                "awsAccountId",
                "externalId",
                "roleArn",
                "protocol",
                "mechanism",
                "port",
                "schemaRegistryUrl",
                "schemaRegistryApiKey",
                "schemaRegistryApiSecret",
                "authenticationType",
                "truststoreAuthenticationType",
                "tls",
                "cipherSuite",
                "pubSubMethod",
                "keyStorePassword",
                "keyStoreLocation",
                "schemaRegistryAuthType",
                "valueSubjectNameStrategy",
                "datasourceURL",
                "jdbcDriver",
                "subscription",
                "serviceAccountCredentials",
                "file",
                "tlsFile",
                "queueManager",
                "groupId",
                "channel",
                "dimensions",
                "distance_metric",
                "indexing_method",
                "inverted_list_count",
                "pullPeriod",
                "pullBatchWaitMillis",
                "completionsPath",
                "betaVersion",
                "version",
                "organizationId",
            ]
        ):
            raise ValueError(
                "must be one of enum values ('api_key', 'user', 'endpoint', 'authUrl', 'environment', 'projectName', 'indexName', 'publisher', 'password', 'namespace', 'batchSize', 'batchWaitTime', 'visibilityTimeout', 'connectionType', 'consumer', 'stream', 'batchPollConsumersCount', 'consumer_type', 'region', 'awsAccountId', 'externalId', 'roleArn', 'protocol', 'mechanism', 'port', 'schemaRegistryUrl', 'schemaRegistryApiKey', 'schemaRegistryApiSecret', 'authenticationType', 'truststoreAuthenticationType', 'tls', 'cipherSuite', 'pubSubMethod', 'keyStorePassword', 'keyStoreLocation', 'schemaRegistryAuthType', 'valueSubjectNameStrategy', 'datasourceURL', 'jdbcDriver', 'subscription', 'serviceAccountCredentials', 'file', 'tlsFile', 'queueManager', 'groupId', 'channel', 'dimensions', 'distance_metric', 'indexing_method', 'inverted_list_count')"
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
                    [
                        IntegrationDefFormFieldAdapter.from_dict(_item)
                        for _item in obj["dependsOn"]
                    ]
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
