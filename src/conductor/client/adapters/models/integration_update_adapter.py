from conductor.client.http.models import IntegrationUpdate


class IntegrationUpdateAdapter(IntegrationUpdate):
    @IntegrationUpdate.category.setter
    def category(self, category):
        allowed_values = [
            "API",
            "AI_MODEL",
            "VECTOR_DB",
            "RELATIONAL_DB",
            "MESSAGE_BROKER",
            "GIT",
            "EMAIL",
            "MCP",
        ]  # noqa: E501
        if category not in allowed_values:
            raise ValueError(
                "Invalid value for `category` ({0}), must be one of {1}".format(  # noqa: E501
                    category, allowed_values
                )
            )

        self._category = category
