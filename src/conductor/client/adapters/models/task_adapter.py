from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.shared.http.enums import TaskResultStatus


class TaskAdapter(Task):
    def to_task_result(
        self, status: TaskResultStatus = TaskResultStatus.COMPLETED
    ) -> TaskResult:
        task_result = TaskResult(
            task_id=self.task_id,
            workflow_instance_id=self.workflow_instance_id,
            worker_id=self.worker_id,
            status=status,
        )
        return task_result
