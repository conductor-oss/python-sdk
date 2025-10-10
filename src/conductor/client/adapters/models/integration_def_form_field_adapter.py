from conductor.client.codegen.models import IntegrationDefFormField


class IntegrationDefFormFieldAdapter(IntegrationDefFormField):
    @IntegrationDefFormField.field_name.setter
    def field_name(self, field_name):
        """Sets the field_name of this IntegrationDefFormField.


        :param field_name: The field_name of this IntegrationDefFormField.  # noqa: E501
        :type: str
        """
        allowed_values = [
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
            "oAuth2RefreshToken",
            "oAuth2AuthCode",
            "oAuth2TokenExpiresAt",
            "oAuth2RedirectUri",
        ]
        if field_name not in allowed_values:
            raise ValueError(
                "Invalid value for `field_name` ({0}), must be one of {1}".format(  # noqa: E501
                    field_name, allowed_values
                )
            )

        self._field_name = field_name
