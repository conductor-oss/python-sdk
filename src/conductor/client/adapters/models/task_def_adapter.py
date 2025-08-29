from conductor.client.codegen.models.task_def import TaskDef


class TaskDefAdapter(TaskDef):
    @TaskDef.total_timeout_seconds.setter
    def total_timeout_seconds(self, total_timeout_seconds):
        """Sets the total_timeout_seconds of this TaskDef.


        :param total_timeout_seconds: The total_timeout_seconds of this TaskDef.  # noqa: E501
        :type: int
        """
        self._total_timeout_seconds = total_timeout_seconds

    @TaskDef.timeout_seconds.setter
    def timeout_seconds(self, timeout_seconds):
        """Sets the timeout_seconds of this TaskDef.


        :param timeout_seconds: The timeout_seconds of this TaskDef.  # noqa: E501
        :type: int
        """
        self._timeout_seconds = timeout_seconds
