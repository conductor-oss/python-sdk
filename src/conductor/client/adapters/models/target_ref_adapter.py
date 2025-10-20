from conductor.client.codegen.models.target_ref import TargetRef


class TargetRefAdapter(TargetRef):
    @TargetRef.id.setter
    def id(self, id):
        """Sets the id of this TargetRef.


        :param id: The id of this TargetRef.  # noqa: E501
        :type: str
        """
        self._id = id

    @TargetRef.type.setter
    def type(self, type):
        """Sets the type of this TargetRef.


        :param type: The type of this TargetRef.  # noqa: E501
        :type: str
        """
        allowed_values = [
            "WORKFLOW",
            "WORKFLOW_DEF",
            "WORKFLOW_SCHEDULE",
            "EVENT_HANDLER",
            "TASK_DEF",
            "TASK_REF_NAME",
            "TASK_ID",
            "APPLICATION",
            "USER",
            "SECRET_NAME",
            "ENV_VARIABLE",
            "TAG",
            "DOMAIN",
            "INTEGRATION_PROVIDER",
            "INTEGRATION",
            "PROMPT",
            "USER_FORM_TEMPLATE",
            "SCHEMA",
            "CLUSTER_CONFIG",
            "WEBHOOK",
            "SECRET",
        ]
        if type not in allowed_values:
            raise ValueError("Invalid value for `type` ({0}), must be one of {1}".format(type, allowed_values))

        self._type = type
