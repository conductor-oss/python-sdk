from __future__ import annotations

from copy import deepcopy
from typing import List, Optional

from conductor.asyncio_client.adapters.models.workflow_task_adapter import WorkflowTaskAdapter
from conductor.asyncio_client.workflow.task.join_task import JoinTask
from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import TaskType


class DynamicForkTask(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        tasks_param: str = "dynamicTasks",
        tasks_input_param_name: str = "dynamicTasksInputs",
        join_task: Optional[JoinTask] = None,
    ):
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.FORK_JOIN_DYNAMIC,
        )
        self.tasks_param = tasks_param
        self.tasks_input_param_name = tasks_input_param_name
        self._join_task = deepcopy(join_task) if join_task else None

    def to_workflow_task(self) -> List[WorkflowTaskAdapter]:
        wf_task = super().to_workflow_task()
        wf_task.dynamic_fork_tasks_param = self.tasks_param
        wf_task.dynamic_fork_tasks_input_param_name = self.tasks_input_param_name

        tasks = [wf_task]
        if self._join_task:
            tasks.append(self._join_task.to_workflow_task())
        return tasks
