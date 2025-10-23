from conductor.client.codegen.models import IntegrationUpdate


class IntegrationUpdateAdapter(IntegrationUpdate):
    @IntegrationUpdate.category.setter  # type: ignore[attr-defined]
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
            "CLOUD",
        ]
        if category not in allowed_values:
            raise ValueError(
                "Invalid value for `category` ({0}), must be one of {1}".format(
                    category, allowed_values
                )
            )

        self._category = category
