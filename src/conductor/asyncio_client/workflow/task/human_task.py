from __future__ import annotations

from typing import Optional

from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import AssignmentCompletionStrategy, TaskType


class HumanTask(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        display_name: Optional[str] = None,
        form_template: Optional[str] = None,
        form_version: int = 0,
        assignment_completion_strategy: AssignmentCompletionStrategy = AssignmentCompletionStrategy.LEAVE_OPEN,
    ):
        super().__init__(task_reference_name=task_ref_name, task_type=TaskType.HUMAN)
        self.input_parameters.update(
            {
                "__humanTaskDefinition": {
                    "assignmentCompletionStrategy": assignment_completion_strategy.name,
                    "displayName": display_name,
                    "userFormTemplate": {
                        "name": form_template,
                        "version": form_version,
                    },
                }
            }
        )
