from conductor.client.codegen.models.target_ref import TargetRef


class TargetRefAdapter(TargetRef):
    @TargetRef.id.setter
    def id(self, id):
        """Sets the id of this TargetRef.


        :param id: The id of this TargetRef.  # noqa: E501
        :type: str
        """
        self._id = id
