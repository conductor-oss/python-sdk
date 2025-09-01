from enum import Enum

from conductor.client.codegen.models.upsert_user_request import \
    UpsertUserRequest


class RolesEnum(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    WORKER = "WORKER"
    METADATA_MANAGER = "METADATA_MANAGER"
    WORKFLOW_MANAGER = "WORKFLOW_MANAGER"


class UpsertUserRequestAdapter(UpsertUserRequest):
    @UpsertUserRequest.roles.setter
    def roles(self, roles):
        """Sets the roles of this UpsertUserRequest.


        :param roles: The roles of this UpsertUserRequest.  # noqa: E501
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
