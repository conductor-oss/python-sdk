from __future__ import annotations

from typing import List, Optional

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.tag_string import TagString
from conductor.client.http.models.task_def import TaskDef
from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.metadata_client import MetadataClient
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.orkes.models.ratelimit_tag import RateLimitTag
from conductor.client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.http.models.extended_task_def import ExtendedTaskDef
from conductor.client.http.models.extended_workflow_def import ExtendedWorkflowDef


class OrkesMetadataClient(OrkesBaseClient, MetadataClient):
    def __init__(self, configuration: Configuration):
        super(OrkesMetadataClient, self).__init__(configuration)

    def register_workflow_def(
        self, workflow_def: ExtendedWorkflowDef, overwrite: Optional[bool] = True
    ) -> object:
        return self.metadataResourceApi.create(workflow_def, overwrite=overwrite)

    def update_workflow_def(
        self, workflow_def: ExtendedWorkflowDef, overwrite: Optional[bool] = True
    ) -> object:
        return self.metadataResourceApi.update([workflow_def], overwrite=overwrite)

    def unregister_workflow_def(self, name: str, version: int) -> None:
        self.metadataResourceApi.unregister_workflow_def(name, version)

    def get_workflow_def(self, name: str, version: Optional[int] = None) -> WorkflowDef:
        workflow = None
        if version:
            workflow = self.metadataResourceApi.get1(name, version=version)
        else:
            workflow = self.metadataResourceApi.get1(name)

        return workflow

    def get_all_workflow_defs(self) -> List[WorkflowDef]:
        return self.metadataResourceApi.get_workflow_defs()

    def register_task_def(self, task_def: ExtendedTaskDef) -> object:
        return self.metadataResourceApi.register_task_def([task_def])

    def update_task_def(self, task_def: TaskDef):
        self.metadataResourceApi.update_task_def(task_def)

    def unregister_task_def(self, task_type: str):
        self.metadataResourceApi.unregister_task_def(task_type)

    def get_task_def(self, task_type: str) -> object:
        return self.metadataResourceApi.get_task_def(task_type)

    def get_all_task_defs(self) -> List[TaskDef]:
        return self.metadataResourceApi.get_task_defs()

    def add_workflow_tag(self, tag: MetadataTag, workflow_name: str):
        self.tagsApi.add_workflow_tag(tag, workflow_name)

    def delete_workflow_tag(self, tag: MetadataTag, workflow_name: str):
        tagStr = TagString(tag.key, tag.type, tag.value)
        self.tagsApi.delete_workflow_tag(tagStr, workflow_name)

    def get_workflow_tags(self, workflow_name: str) -> object:
        return self.tagsApi.get_workflow_tags(workflow_name)

    def set_workflow_tags(self, tags: List[MetadataTag], workflow_name: str):
        self.tagsApi.set_workflow_tags(tags, workflow_name)

    def addTaskTag(self, tag: MetadataTag, taskName: str):
        self.tagsApi.add_task_tag(tag, taskName)

    def deleteTaskTag(self, tag: MetadataTag, taskName: str):
        tagStr = TagString(tag.key, tag.type, tag.value)
        self.tagsApi.delete_task_tag(tagStr, taskName)

    def getTaskTags(self, taskName: str) -> object:
        return self.tagsApi.get_task_tags(taskName)

    def setTaskTags(self, tags: List[MetadataTag], taskName: str):
        self.tagsApi.set_task_tags(tags, taskName)

    def setWorkflowRateLimit(self, rateLimit: int, workflowName: str):
        self.removeWorkflowRateLimit(workflowName)
        rateLimitTag = RateLimitTag(workflowName, rateLimit)
        self.tagsApi.add_workflow_tag(rateLimitTag, workflowName)

    def getWorkflowRateLimit(self, workflowName: str) -> Optional[int]:
        tags = self.tagsApi.get_workflow_tags(workflowName)
        for tag in tags:
            if tag.type == "RATE_LIMIT" and tag.key == workflowName:
                return tag.value

        return None

    def removeWorkflowRateLimit(self, workflowName: str):
        current_rate_limit = self.getWorkflowRateLimit(workflowName)
        if current_rate_limit:
            rateLimitTag = RateLimitTag(workflowName, current_rate_limit)
            self.tagsApi.delete_workflow_tag(rateLimitTag, workflowName)
