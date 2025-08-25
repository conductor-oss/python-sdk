from conductor.client.http.models.target_ref import TargetRef


class TargetRefAdapter(TargetRef):
    @TargetRef.id.setter
    def id(self, id):
        """Sets the id of this TargetRef.


        :param id: The id of this TargetRef.  # noqa: E501
        :type: str
        """
        allowed_values = [
            "Identifier of the target e.g. `name` in case it's a WORKFLOW_DEF"
        ]
        if id not in allowed_values:
            raise ValueError(
                "Invalid value for `id` ({0}), must be one of {1}".format(
                    id, allowed_values
                )
            )

        self._id = id
