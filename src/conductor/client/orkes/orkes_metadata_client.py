from __future__ import annotations

from typing import List, Optional

from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.extended_task_def import ExtendedTaskDef
from conductor.client.http.models.extended_workflow_def import ExtendedWorkflowDef
from conductor.client.http.models.incoming_bpmn_file import IncomingBpmnFile
from conductor.client.http.models.tag import Tag
from conductor.client.http.models.tag_string import TagString
from conductor.client.http.models.task_def import TaskDef
from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.metadata_client import MetadataClient
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.orkes.models.ratelimit_tag import RateLimitTag
from conductor.client.orkes.orkes_base_client import OrkesBaseClient


class OrkesMetadataClient(OrkesBaseClient, MetadataClient):
    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    @deprecated("register_workflow_def is deprecated; use register_workflow_def_validated instead")
    @typing_deprecated(
        "register_workflow_def is deprecated; use register_workflow_def_validated instead"
    )
    def register_workflow_def(  # type: ignore[override]
        self, workflow_def: ExtendedWorkflowDef, overwrite: Optional[bool] = True
    ) -> object:
        return self._metadata_api.create(workflow_def, overwrite=overwrite)

    def register_workflow_def_validated(
        self,
        workflow_def: ExtendedWorkflowDef,
        overwrite: bool = True,
        new_version: bool = True,
        **kwargs,
    ) -> None:
        self._metadata_api.create(
            body=workflow_def, overwrite=overwrite, new_version=new_version, **kwargs
        )

    @deprecated("update_workflow_def is deprecated; use update_workflow_def_validated instead")
    @typing_deprecated(
        "update_workflow_def is deprecated; use update_workflow_def_validated instead"
    )
    def update_workflow_def(  # type: ignore[override]
        self,
        workflow_def: ExtendedWorkflowDef,
        overwrite: Optional[bool] = True,
        **kwargs,
    ) -> object:
        return self._metadata_api.update([workflow_def], overwrite=overwrite, **kwargs)

    def update_workflow_def_validated(
        self,
        workflow_def: ExtendedWorkflowDef,
        overwrite: bool = True,
        new_version: bool = True,
        **kwargs,
    ) -> None:
        self._metadata_api.update(
            body=[workflow_def], overwrite=overwrite, new_version=new_version, **kwargs
        )

    def unregister_workflow_def(self, name: str, version: int, **kwargs) -> None:
        self._metadata_api.unregister_workflow_def(name=name, version=version, **kwargs)

    def get_workflow_def(self, name: str, version: Optional[int] = None, **kwargs) -> WorkflowDef:
        workflow = None
        if version:
            workflow = self._metadata_api.get1(name=name, version=version, **kwargs)
        else:
            workflow = self._metadata_api.get1(name=name, **kwargs)

        return workflow

    def get_all_workflow_defs(self, **kwargs) -> List[WorkflowDef]:
        return self._metadata_api.get_workflow_defs(**kwargs)

    @deprecated("register_task_def is deprecated; use register_task_def_validated instead")
    @typing_deprecated("register_task_def is deprecated; use register_task_def_validated instead")
    def register_task_def(self, task_def: ExtendedTaskDef) -> object:  # type: ignore[override]
        return self._metadata_api.register_task_def([task_def])

    def register_task_def_validated(self, task_def: List[ExtendedTaskDef], **kwargs) -> None:
        self._metadata_api.register_task_def(body=task_def, **kwargs)

    def update_task_def(self, task_def: TaskDef, **kwargs) -> None:
        self._metadata_api.update_task_def(body=task_def, **kwargs)

    def unregister_task_def(self, task_type: str, **kwargs) -> None:
        self._metadata_api.unregister_task_def(tasktype=task_type, **kwargs)

    @deprecated("get_task_def is deprecated; use get_task_def_validated instead")
    @typing_deprecated("get_task_def is deprecated; use get_task_def_validated instead")
    def get_task_def(self, task_type: str) -> object:  # type: ignore[override]
        return self._metadata_api.get_task_def(task_type)

    def get_task_def_validated(self, task_type: str, **kwargs) -> TaskDef:
        task_def = self._metadata_api.get_task_def(tasktype=task_type, **kwargs)
        return self.api_client.deserialize_class(task_def, "TaskDef")

    def get_all_task_defs(self, **kwargs) -> List[TaskDef]:
        return self._metadata_api.get_task_defs(**kwargs)

    def add_workflow_tag(self, tag: MetadataTag, workflow_name: str, **kwargs) -> None:
        self._tags_api.add_workflow_tag(body=tag, name=workflow_name, **kwargs)

    def delete_workflow_tag(self, tag: MetadataTag, workflow_name: str, **kwargs) -> None:
        tag_str = TagString(tag.key, tag.type, tag.value)
        self._tags_api.delete_workflow_tag(body=tag_str, name=workflow_name, **kwargs)

    @deprecated("get_workflow_tags is deprecated; use get_workflow_tags_validated instead")
    @typing_deprecated("get_workflow_tags is deprecated; use get_workflow_tags_validated instead")
    def get_workflow_tags(self, workflow_name: str) -> object:  # type: ignore[override]
        return self._tags_api.get_workflow_tags(workflow_name)

    def get_workflow_tags_validated(self, workflow_name: str, **kwargs) -> List[Tag]:
        tags = self._tags_api.get_workflow_tags(name=workflow_name, **kwargs)
        return self.api_client.deserialize_class(tags, "List[Tag]")

    def set_workflow_tags(self, tags: List[MetadataTag], workflow_name: str, **kwargs) -> None:
        self._tags_api.set_workflow_tags(body=tags, name=workflow_name, **kwargs)

    @deprecated("addTaskTag is deprecated; use add_task_tag instead")
    @typing_deprecated("addTaskTag is deprecated; use add_task_tag instead")
    def addTaskTag(self, tag: MetadataTag, taskName: str):
        self._tags_api.add_task_tag(tag, taskName)

    def add_task_tag(self, tag: MetadataTag, task_name: str, **kwargs) -> None:
        tag_str = TagString(tag.key, tag.type, tag.value)
        self._tags_api.add_task_tag(tag=tag_str, task_name=task_name, **kwargs)

    @deprecated("deleteTaskTag is deprecated; use delete_task_tag instead")
    @typing_deprecated("deleteTaskTag is deprecated; use delete_task_tag instead")
    def deleteTaskTag(self, tag: MetadataTag, taskName: str):
        tagStr = TagString(tag.key, tag.type, tag.value)
        self._tags_api.delete_task_tag(tagStr, taskName)

    def delete_task_tag(self, tag: MetadataTag, task_name: str, **kwargs) -> None:
        tag_str = TagString(tag.key, tag.type, tag.value)
        self._tags_api.delete_task_tag(tag=tag_str, task_name=task_name, **kwargs)

    @deprecated("getTaskTags is deprecated; use get_task_tags instead")
    @typing_deprecated("getTaskTags is deprecated; use get_task_tags instead")
    def getTaskTags(self, taskName: str) -> object:
        return self._tags_api.get_task_tags(taskName)

    def get_task_tags(self, task_name: str, **kwargs) -> List[MetadataTag]:
        tags = self._tags_api.get_task_tags(task_name=task_name, **kwargs)
        result = self.api_client.deserialize_class(tags, "List[Tag]")
        return result

    @deprecated("setTaskTags is deprecated; use set_task_tags instead")
    @typing_deprecated("setTaskTags is deprecated; use set_task_tags instead")
    def setTaskTags(self, tags: List[MetadataTag], taskName: str):
        self._tags_api.set_task_tags(tags, taskName)

    def set_task_tags(self, tags: List[MetadataTag], task_name: str, **kwargs) -> None:
        self._tags_api.set_task_tags(body=tags, task_name=task_name, **kwargs)

    @deprecated("setWorkflowRateLimit is deprecated; use set_workflow_rate_limit instead")
    @typing_deprecated("setWorkflowRateLimit is deprecated; use set_workflow_rate_limit instead")
    def setWorkflowRateLimit(self, rateLimit: int, workflowName: str):
        self.remove_workflow_rate_limit(workflow_name=workflowName)
        rateLimitTag = RateLimitTag(workflowName, rateLimit)
        self._tags_api.add_workflow_tag(rateLimitTag, workflowName)

    def set_workflow_rate_limit(self, rate_limit: int, workflow_name: str, **kwargs) -> None:
        self.remove_workflow_rate_limit(workflow_name)
        rate_limit_tag = RateLimitTag(workflow_name, rate_limit)
        self._tags_api.add_workflow_tag(tag=rate_limit_tag, name=workflow_name, **kwargs)

    @deprecated("getWorkflowRateLimit is deprecated; use get_workflow_rate_limit instead")
    @typing_deprecated("getWorkflowRateLimit is deprecated; use get_workflow_rate_limit instead")
    def getWorkflowRateLimit(self, workflowName: str) -> Optional[int]:
        tags = self._tags_api.get_workflow_tags(workflowName)
        for tag in tags:
            if tag.type == "RATE_LIMIT" and tag.key == workflowName:
                return tag.value

        return None

    def get_workflow_rate_limit(self, workflow_name: str, **kwargs) -> Optional[int]:
        tags = self._tags_api.get_workflow_tags(name=workflow_name, **kwargs)
        for tag in tags:
            if tag.type == "RATE_LIMIT" and tag.key == workflow_name:
                return tag.value

        return None

    @deprecated("removeWorkflowRateLimit is deprecated; use remove_workflow_rate_limit instead")
    @typing_deprecated(
        "removeWorkflowRateLimit is deprecated; use remove_workflow_rate_limit instead"
    )
    def removeWorkflowRateLimit(self, workflowName: str) -> None:
        current_rate_limit = self.getWorkflowRateLimit(workflowName)
        if current_rate_limit:
            rateLimitTag = RateLimitTag(workflowName, current_rate_limit)
            self._tags_api.delete_workflow_tag(rateLimitTag, workflowName)

    def remove_workflow_rate_limit(self, workflow_name: str, **kwargs) -> None:
        current_rate_limit = self.get_workflow_rate_limit(workflow_name=workflow_name, **kwargs)
        if current_rate_limit:
            rate_limit_tag = RateLimitTag(workflow_name, current_rate_limit)
            self._tags_api.delete_workflow_tag(tag=rate_limit_tag, name=workflow_name, **kwargs)

    def upload_definitions_to_s3(self, **kwargs) -> None:
        self._metadata_api.upload_workflows_and_tasks_definitions_to_s3(**kwargs)

    def upload_bpmn_file(self, body: IncomingBpmnFile, **kwargs) -> List[ExtendedWorkflowDef]:
        return self._metadata_api.upload_bpmn_file(body=body, **kwargs)
