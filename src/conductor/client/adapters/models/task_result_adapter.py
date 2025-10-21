from conductor.client.adapters.models.task_exec_log_adapter import TaskExecLogAdapter
from conductor.client.codegen.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus


class TaskResultAdapter(TaskResult):
    @TaskResult.status.setter
    def status(self, status):
        """Sets the status of this TaskResult.


        :param status: The status of this TaskResult.  # noqa: E501
        :type: str
        """
        if isinstance(status, str):
            try:
                status = TaskResultStatus(status)
            except ValueError as e:
                raise ValueError(
                    f"Invalid value for `status` ({status}), must be one of {[e.value for e in TaskResultStatus]}"
                ) from e
        elif not isinstance(status, TaskResultStatus):
            raise TypeError(f"status must be a TaskStatus enum or string, got {type(status)}")

        self._status = status

    def add_output_data(self, key, value):
        if self.output_data is None:
            self.output_data = {}
        self.output_data[key] = value
        return self

    def log(self, log):
        """Adds a log entry to this TaskResult.

        :param log: The log message to add
        :type: str
        :return: This TaskResult instance
        :rtype: TaskResult
        """
        if self.logs is None:
            self.logs = []
        self.logs.append(TaskExecLogAdapter(log=log))
        return self

    @staticmethod
    def new_task_result(status):
        """Creates a new TaskResult with the specified status.

        :param status: The status for the new TaskResult
        :type: str
        :return: A new TaskResult with the specified status
        :rtype: TaskResult
        """
        result = TaskResult()
        result.status = status
        return result

    @staticmethod
    def complete():
        """Creates a new TaskResult with COMPLETED status.

        :return: A new TaskResult with COMPLETED status
        :rtype: TaskResult
        """
        return TaskResultAdapter.new_task_result("COMPLETED")

    @staticmethod
    def failed(failure_reason):
        """Creates a new TaskResult with FAILED status and the specified failure reason.

        :param failure_reason: The reason for failure
        :type: str
        :return: A new TaskResult with FAILED status and the specified failure reason
        :rtype: TaskResult
        """
        result = TaskResultAdapter.new_task_result("FAILED")
        result.reason_for_incompletion = failure_reason
        return result

    @staticmethod
    def in_progress():
        """Creates a new TaskResult with IN_PROGRESS status.

        :return: A new TaskResult with IN_PROGRESS status
        :rtype: TaskResult
        """
        return TaskResultAdapter.new_task_result("IN_PROGRESS")
