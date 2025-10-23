from conductor.client.codegen.models.upsert_group_request import UpsertGroupRequest


class UpsertGroupRequestAdapter(UpsertGroupRequest):
    @UpsertGroupRequest.roles.setter  # type: ignore[attr-defined]
    def roles(self, roles):
        """Sets the roles of this UpsertGroupRequest.


        :param roles: The roles of this UpsertGroupRequest.  # noqa: E501
        :type: list[str]
        """
        allowed_values = [
            "ADMIN",
            "USER",
            "WORKER",
            "METADATA_MANAGER",
            "WORKFLOW_MANAGER",
        ]
        if not set(roles).issubset(set(allowed_values)):
            raise ValueError(
                "Invalid values for `roles` [{0}], must be a subset of [{1}]".format(
                    ", ".join(map(str, set(roles) - set(allowed_values))),
                    ", ".join(map(str, allowed_values)),
                )
            )

        self._roles = roles

    @UpsertGroupRequest.default_access.setter  # type: ignore[attr-defined]
    def default_access(self, default_access):
        """Sets the default_access of this UpsertGroupRequest.

        A default Map<TargetType, Set<Access>> to share permissions, allowed target types: WORKFLOW_DEF, TASK_DEF  # noqa: E501

        :param default_access: The default_access of this UpsertGroupRequest.  # noqa: E501
        :type: dict(str, list[str])
        """
        self._default_access = default_access
