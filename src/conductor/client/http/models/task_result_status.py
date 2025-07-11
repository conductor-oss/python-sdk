from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from deprecated import deprecated


class TaskResultStatus(str, Enum):
    COMPLETED = "COMPLETED",
    FAILED = "FAILED",
    FAILED_WITH_TERMINAL_ERROR = "FAILED_WITH_TERMINAL_ERROR",
    IN_PROGRESS = "IN_PROGRESS"

    def __str__(self) -> str:
        return self.name.__str__()


class TaskExecLog:
    def __init__(self, log: str):
        self.log = log


@dataclass
class TaskResult:
    _workflow_instance_id: str = field(default=None)
    _task_id: str = field(default=None)
    _reason_for_incompletion: str = field(default=None)
    _callback_after_seconds: int = field(default=0)
    _worker_id: str = field(default=None)
    _status: TaskResultStatus = field(default=None)
    _output_data: Dict[str, Any] = field(default_factory=dict)
    _logs: List[TaskExecLog] = field(default_factory=list)
    _external_output_payload_storage_path: str = field(default=None)
    _sub_workflow_id: str = field(default=None)
    _extend_lease: bool = field(default=False)

    def __init__(self, task=None):
        self._workflow_instance_id = None
        self._task_id = None
        self._reason_for_incompletion = None
        self._callback_after_seconds = 0
        self._worker_id = None
        self._status = None
        self._output_data = {}
        self._logs = []
        self._external_output_payload_storage_path = None
        self._sub_workflow_id = None
        self._extend_lease = False

        if task is not None:
            self._workflow_instance_id = task.workflow_instance_id
            self._task_id = task.task_id
            self._reason_for_incompletion = task.reason_for_incompletion
            self._callback_after_seconds = task.callback_after_seconds
            self._worker_id = task.worker_id
            self._output_data = task.output_data
            self._external_output_payload_storage_path = task.external_output_payload_storage_path
            self._sub_workflow_id = task.sub_workflow_id
            
            if task.status == "CANCELED" or task.status == "COMPLETED_WITH_ERRORS" or task.status == "TIMED_OUT" or task.status == "SKIPPED":
                self._status = TaskResultStatus.FAILED
            elif task.status == "SCHEDULED":
                self._status = TaskResultStatus.IN_PROGRESS
            else:
                self._status = TaskResultStatus[task.status]

    def __post_init__(self):
        if self._output_data is None:
            self._output_data = {}
        if self._logs is None:
            self._logs = []

    @property
    def workflow_instance_id(self) -> str:
        """
        Returns the workflow instance id
        """
        return self._workflow_instance_id

    @workflow_instance_id.setter
    def workflow_instance_id(self, workflow_instance_id: str):
        """
        Sets the workflow instance id
        """
        self._workflow_instance_id = workflow_instance_id

    @property
    def task_id(self) -> str:
        """
        Returns the task id
        """
        return self._task_id

    @task_id.setter
    def task_id(self, task_id: str):
        """
        Sets the task id
        """
        self._task_id = task_id

    @property
    def reason_for_incompletion(self) -> str:
        """
        Returns the reason for incompletion
        """
        return self._reason_for_incompletion

    @reason_for_incompletion.setter
    def reason_for_incompletion(self, reason_for_incompletion: str):
        """
        Sets the reason for incompletion
        """
        if reason_for_incompletion and len(reason_for_incompletion) > 500:
            self._reason_for_incompletion = reason_for_incompletion[:500]
        else:
            self._reason_for_incompletion = reason_for_incompletion

    @property
    def callback_after_seconds(self) -> int:
        """
        Returns the callback after seconds
        """
        return self._callback_after_seconds

    @callback_after_seconds.setter
    def callback_after_seconds(self, callback_after_seconds: int):
        """
        Sets the callback after seconds
        """
        self._callback_after_seconds = callback_after_seconds

    @property
    def worker_id(self) -> str:
        """
        Returns the worker id
        """
        return self._worker_id

    @worker_id.setter
    def worker_id(self, worker_id: str):
        """
        Sets the worker id
        """
        self._worker_id = worker_id

    @property
    def status(self) -> TaskResultStatus:
        """
        Returns the status
        """
        return self._status

    @status.setter
    def status(self, status: TaskResultStatus):
        """
        Sets the status
        """
        self._status = status

    @property
    def output_data(self) -> Dict[str, Any]:
        """
        Returns the output data
        """
        return self._output_data

    @output_data.setter
    def output_data(self, output_data: Dict[str, Any]):
        """
        Sets the output data
        """
        self._output_data = output_data

    @property
    def logs(self) -> List[TaskExecLog]:
        """
        Returns the logs
        """
        return self._logs

    @logs.setter
    def logs(self, logs: List[TaskExecLog]):
        """
        Sets the logs
        """
        self._logs = logs

    @property
    def external_output_payload_storage_path(self) -> str:
        """
        Returns the external output payload storage path
        """
        return self._external_output_payload_storage_path

    @external_output_payload_storage_path.setter
    def external_output_payload_storage_path(self, external_output_payload_storage_path: str):
        """
        Sets the external output payload storage path
        """
        self._external_output_payload_storage_path = external_output_payload_storage_path

    @property
    def sub_workflow_id(self) -> str:
        """
        Returns the sub workflow id
        """
        return self._sub_workflow_id

    @sub_workflow_id.setter
    def sub_workflow_id(self, sub_workflow_id: str):
        """
        Sets the sub workflow id
        """
        self._sub_workflow_id = sub_workflow_id

    @property
    def extend_lease(self) -> bool:
        """
        Returns whether to extend lease
        """
        return self._extend_lease

    @extend_lease.setter
    def extend_lease(self, extend_lease: bool):
        """
        Sets whether to extend lease
        """
        self._extend_lease = extend_lease

    def add_output_data(self, key: str, value: Any) -> 'TaskResult':
        """
        Adds output data
        """
        self._output_data[key] = value
        return self

    def log(self, log: str) -> 'TaskResult':
        """
        Adds a log
        """
        self._logs.append(TaskExecLog(log))
        return self

    def __str__(self) -> str:
        return f"TaskResult{{workflowInstanceId='{self._workflow_instance_id}', taskId='{self._task_id}', reasonForIncompletion='{self._reason_for_incompletion}', callbackAfterSeconds={self._callback_after_seconds}, workerId='{self._worker_id}', status={self._status}, outputData={self._output_data}, logs={self._logs}, externalOutputPayloadStoragePath='{self._external_output_payload_storage_path}', subWorkflowId='{self._sub_workflow_id}', extendLease='{self._extend_lease}'}}"

    def __eq__(self, other):
        if not isinstance(other, TaskResult):
            return False
        return (self._workflow_instance_id == other.workflow_instance_id and
                self._task_id == other.task_id and
                self._reason_for_incompletion == other.reason_for_incompletion and
                self._callback_after_seconds == other.callback_after_seconds and
                self._worker_id == other.worker_id and
                self._status == other.status and
                self._output_data == other.output_data and
                self._logs == other.logs and
                self._external_output_payload_storage_path == other.external_output_payload_storage_path and
                self._sub_workflow_id == other.sub_workflow_id and
                self._extend_lease == other.extend_lease)

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the task result to a dictionary
        """
        return {
            "workflowInstanceId": self._workflow_instance_id,
            "taskId": self._task_id,
            "reasonForIncompletion": self._reason_for_incompletion,
            "callbackAfterSeconds": self._callback_after_seconds,
            "workerId": self._worker_id,
            "status": self._status.name if self._status else None,
            "outputData": self._output_data,
            "logs": self._logs,
            "externalOutputPayloadStoragePath": self._external_output_payload_storage_path,
            "subWorkflowId": self._sub_workflow_id,
            "extendLease": self._extend_lease
        }

    @staticmethod
    def complete() -> 'TaskResult':
        """
        Creates a completed task result
        """
        return TaskResult.new_task_result(TaskResultStatus.COMPLETED)

    @staticmethod
    def failed() -> 'TaskResult':
        """
        Creates a failed task result
        """
        return TaskResult.new_task_result(TaskResultStatus.FAILED)

    @staticmethod
    def failed(failure_reason: str) -> 'TaskResult':
        """
        Creates a failed task result with a reason
        """
        result = TaskResult.new_task_result(TaskResultStatus.FAILED)
        result.reason_for_incompletion = failure_reason
        return result

    @staticmethod
    def in_progress() -> 'TaskResult':
        """
        Creates an in progress task result
        """
        return TaskResult.new_task_result(TaskResultStatus.IN_PROGRESS)

    @staticmethod
    def new_task_result(status: TaskResultStatus) -> 'TaskResult':
        """
        Creates a new task result with the given status
        """
        result = TaskResult()
        result.status = status
        return result