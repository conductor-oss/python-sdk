from typing import List

from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.api.metadata_resource_api import MetadataResourceApi
from conductor.client.http.models.extended_task_def import ExtendedTaskDef
from conductor.client.http.models.extended_workflow_def import ExtendedWorkflowDef
from conductor.client.http.models.incoming_bpmn_file import IncomingBpmnFile
from conductor.client.http.models.task_def import TaskDef
from conductor.client.http.models.workflow_def import WorkflowDef


class MetadataResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = MetadataResourceApi(api_client)

    def create(self, body: ExtendedWorkflowDef, **kwargs) -> object:
        """Create a new workflow definition"""
        return self._api.create(body, **kwargs)

    def get1(self, name: str, **kwargs) -> WorkflowDef:
        """Get a workflow definition"""
        return self._api.get1(name, **kwargs)

    def get_task_def(self, tasktype: str, **kwargs) -> object:
        """Get a task definition"""
        return self._api.get_task_def(tasktype, **kwargs)

    def get_task_defs(self, **kwargs) -> List[TaskDef]:
        """Get all task definitions"""
        return self._api.get_task_defs(**kwargs)

    def get_workflow_defs(self, **kwargs) -> List[WorkflowDef]:
        """Get all workflow definitions"""
        return self._api.get_workflow_defs(**kwargs)

    def register_task_def(self, body: List[ExtendedTaskDef], **kwargs) -> object:
        """Register a task definition"""
        return self._api.register_task_def(body, **kwargs)

    def unregister_task_def(self, tasktype: str, **kwargs) -> None:
        """Unregister a task definition"""
        return self._api.unregister_task_def(tasktype, **kwargs)

    def unregister_workflow_def(self, name: str, version: int, **kwargs) -> None:
        """Unregister a workflow definition"""
        return self._api.unregister_workflow_def(name, version, **kwargs)

    def update(self, body: List[ExtendedWorkflowDef], **kwargs) -> object:
        """Update a workflow definition"""
        return self._api.update(body, **kwargs)

    def update_task_def(self, body: ExtendedTaskDef, **kwargs) -> object:
        """Update a task definition"""
        return self._api.update_task_def(body, **kwargs)

    def upload_bpmn_file(self, body: IncomingBpmnFile, **kwargs) -> List[ExtendedWorkflowDef]:
        """Upload a BPMN file"""
        return self._api.upload_bpmn_file(body, **kwargs)

    def upload_workflows_and_tasks_definitions_to_s3(self, **kwargs) -> None:
        """Upload all workflows and tasks definitions to Object storage if configured"""
        return self._api.upload_workflows_and_tasks_definitions_to_s3(**kwargs)
