from __future__ import annotations

from typing import List, Optional, Union

from conductor.asyncio_client.adapters.models.workflow_task_adapter import WorkflowTaskAdapter
from conductor.asyncio_client.workflow.task.join_task import JoinTask
from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import TaskType


def get_join_task(task_reference_name: str) -> str:
    return task_reference_name + "_join"


class ForkTask(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        forked_tasks: List[List[TaskInterface]],
        join_on: Optional[List[str]] = None,
    ):
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.FORK_JOIN,
        )
        self._forked_tasks = forked_tasks
        self._join_on = join_on

    def to_workflow_task(  # type: ignore[override]
        self,
    ) -> Union[WorkflowTaskAdapter, List[WorkflowTaskAdapter]]:
        workflow_task = super().to_workflow_task()
        workflow_task.fork_tasks = []
        workflow_task.join_on = []

        for inner_forked_tasks in self._forked_tasks:
            converted_inner_forked_tasks = [
                inner_forked_task.to_workflow_task() for inner_forked_task in inner_forked_tasks
            ]
            workflow_task.fork_tasks.append(converted_inner_forked_tasks)
            workflow_task.join_on.append(converted_inner_forked_tasks[-1].task_reference_name)

        if self._join_on:
            join_task = JoinTask(f"{workflow_task.task_reference_name}_join", join_on=self._join_on)
            return [workflow_task, join_task.to_workflow_task()]

        return workflow_task
