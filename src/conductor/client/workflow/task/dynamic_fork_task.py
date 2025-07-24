from copy import deepcopy

from typing_extensions import Self

from conductor.client.http.models.workflow_task import WorkflowTask
from conductor.client.workflow.task.join_task import JoinTask
from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class DynamicForkTask(TaskInterface):
    def __init__(self, task_ref_name: str, tasks_param: str = 'dynamicTasks', tasks_input_param_name: str = 'dynamicTasksInputs', join_task: JoinTask = None) -> Self:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.FORK_JOIN_DYNAMIC
        )
        self.tasks_param = tasks_param
        self.tasks_input_param_name = tasks_input_param_name
        self._join_task = deepcopy(join_task)

    def to_workflow_task(self) -> WorkflowTask:
        wf_task = super().to_workflow_task()
        wf_task.dynamic_fork_join_tasks_param = self.tasks_param
        wf_task.dynamic_fork_tasks_input_param_name = self.tasks_input_param_name
        tasks = [
            wf_task,
        ]
        if self._join_task is not None:
            tasks.append(self._join_task.to_workflow_task())
        return tasks
