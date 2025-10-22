from __future__ import annotations
from copy import deepcopy
from typing import Dict, Optional

from conductor.client.http.models.sub_workflow_params import SubWorkflowParams
from conductor.client.http.models.workflow_task import WorkflowTask
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class SubWorkflowTask(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        workflow_name: str,
        version: Optional[int] = None,
        task_to_domain_map: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(task_reference_name=task_ref_name, task_type=TaskType.SUB_WORKFLOW)
        self._workflow_name = deepcopy(workflow_name)
        self._version = deepcopy(version)
        self._task_to_domain_map = deepcopy(task_to_domain_map)

    def to_workflow_task(self) -> WorkflowTask:
        workflow = super().to_workflow_task()
        workflow.sub_workflow_param = SubWorkflowParams(
            name=self._workflow_name,
            version=self._version,
            task_to_domain=self._task_to_domain_map,
        )
        return workflow


class InlineSubWorkflowTask(TaskInterface):
    def __init__(self, task_ref_name: str, workflow: ConductorWorkflow) -> None:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.SUB_WORKFLOW,
        )
        self._workflow_name = deepcopy(workflow.name)
        self._workflow_version = deepcopy(workflow.version)
        self._workflow_definition = deepcopy(workflow.to_workflow_def())

    def to_workflow_task(self) -> WorkflowTask:
        workflow = super().to_workflow_task()
        workflow.sub_workflow_param = SubWorkflowParams(
            name=self._workflow_name,
            version=self._workflow_version,
            workflow_definition=self._workflow_definition,
        )
        return workflow
