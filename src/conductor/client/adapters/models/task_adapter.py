from conductor.client.adapters.models.task_result_adapter import TaskResultAdapter
from conductor.client.codegen.models.task import Task
from conductor.shared.http.enums import TaskResultStatus


class TaskAdapter(Task):
    def to_task_result(
        self, status: TaskResultStatus = TaskResultStatus.COMPLETED
    ) -> TaskResultAdapter:
        task_result = TaskResultAdapter(
            task_id=self.task_id,
            workflow_instance_id=self.workflow_instance_id,
            worker_id=self.worker_id,
            status=status,
        )
        return task_result
