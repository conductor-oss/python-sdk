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
        """Initialize the OrkesMetadataClient with configuration.

        Args:
            configuration: Configuration object containing server settings and authentication

        Example:
            ```python
            from conductor.client.configuration.configuration import Configuration

            config = Configuration(server_api_url="http://localhost:8080/api")
            metadata_client = OrkesMetadataClient(config)
            ```
        """
        super().__init__(configuration)

    @deprecated("register_workflow_def is deprecated; use register_workflow_def_validated instead")
    @typing_deprecated(
        "register_workflow_def is deprecated; use register_workflow_def_validated instead"
    )
    def register_workflow_def(  # type: ignore[override]
        self, workflow_def: ExtendedWorkflowDef, overwrite: Optional[bool] = True
    ) -> object:
        """Register a workflow definition.

        .. deprecated::
            Use register_workflow_def_validated() instead.

        Args:
            workflow_def: Workflow definition to register
            overwrite: If True, overwrite existing definition

        Returns:
            Response object
        """
        return self._metadata_api.create(workflow_def, overwrite=overwrite)

    def register_workflow_def_validated(
        self,
        workflow_def: ExtendedWorkflowDef,
        overwrite: bool = True,
        new_version: bool = True,
        **kwargs,
    ) -> None:
        """Register a workflow definition.

        Args:
            workflow_def: Workflow definition to register
            overwrite: If True, overwrite existing definition
            new_version: If True, create a new version
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.extended_workflow_def import ExtendedWorkflowDef
            from conductor.client.http.models.workflow_task import WorkflowTask

            workflow_def = ExtendedWorkflowDef(
                name="order_workflow",
                version=1,
                description="Order processing workflow",
                tasks=[
                    WorkflowTask(
                        name="validate_order",
                        task_reference_name="validate",
                        type="SIMPLE"
                    )
                ]
            )

            metadata_client.register_workflow_def_validated(workflow_def)
            ```
        """
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
        """Update a workflow definition.

        .. deprecated::
            Use update_workflow_def_validated() instead.

        Args:
            workflow_def: Workflow definition to update
            overwrite: If True, overwrite existing definition
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Response object
        """
        return self._metadata_api.update([workflow_def], overwrite=overwrite, **kwargs)

    def update_workflow_def_validated(
        self,
        workflow_def: ExtendedWorkflowDef,
        overwrite: bool = True,
        new_version: bool = True,
        **kwargs,
    ) -> None:
        """Update a workflow definition.

        Args:
            workflow_def: Workflow definition to update
            overwrite: If True, overwrite existing definition
            new_version: If True, create a new version
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            workflow_def = metadata_client.get_workflow_def("order_workflow", 1)
            workflow_def.description = "Updated description"

            metadata_client.update_workflow_def_validated(workflow_def)
            ```
        """
        self._metadata_api.update(
            body=[workflow_def], overwrite=overwrite, new_version=new_version, **kwargs
        )

    def unregister_workflow_def(self, name: str, version: int, **kwargs) -> None:
        """Unregister a workflow definition by name and version.

        Args:
            name: Name of the workflow
            version: Version number
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            metadata_client.unregister_workflow_def("old_workflow", 1)
            ```
        """
        self._metadata_api.unregister_workflow_def(name=name, version=version, **kwargs)

    def get_workflow_def(self, name: str, version: Optional[int] = None, **kwargs) -> WorkflowDef:
        """Get a workflow definition by name and optional version.

        Args:
            name: Name of the workflow
            version: Optional version number. If None, gets latest version
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowDef instance

        Example:
            ```python
            # Get latest version
            workflow = metadata_client.get_workflow_def("order_workflow")

            # Get specific version
            workflow = metadata_client.get_workflow_def("order_workflow", 2)
            print(f"Workflow: {workflow.name}, Version: {workflow.version}")
            ```
        """
        workflow = None
        if version:
            workflow = self._metadata_api.get1(name=name, version=version, **kwargs)
        else:
            workflow = self._metadata_api.get1(name=name, **kwargs)

        return workflow

    def get_all_workflow_defs(self, **kwargs) -> List[WorkflowDef]:
        """Get all workflow definitions.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of WorkflowDef instances

        Example:
            ```python
            workflows = metadata_client.get_all_workflow_defs()
            for workflow in workflows:
                print(f"Workflow: {workflow.name}, Version: {workflow.version}")
            ```
        """
        return self._metadata_api.get_workflow_defs(**kwargs)

    @deprecated("register_task_def is deprecated; use register_task_def_validated instead")
    @typing_deprecated("register_task_def is deprecated; use register_task_def_validated instead")
    def register_task_def(self, task_def: ExtendedTaskDef) -> object:  # type: ignore[override]
        """Register a task definition.

        .. deprecated::
            Use register_task_def_validated() instead.

        Args:
            task_def: Task definition to register

        Returns:
            Response object
        """
        return self._metadata_api.register_task_def([task_def])

    def register_task_def_validated(self, task_def: List[ExtendedTaskDef], **kwargs) -> None:
        """Register one or more task definitions.

        Args:
            task_def: List of task definitions to register
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.extended_task_def import ExtendedTaskDef

            task_defs = [
                ExtendedTaskDef(
                    name="validate_order",
                    description="Validate order details",
                    timeout_seconds=60
                ),
                ExtendedTaskDef(
                    name="process_payment",
                    description="Process payment",
                    timeout_seconds=120
                )
            ]

            metadata_client.register_task_def_validated(task_defs)
            ```
        """
        self._metadata_api.register_task_def(body=task_def, **kwargs)

    def update_task_def(self, task_def: TaskDef, **kwargs) -> None:
        """Update a task definition.

        Args:
            task_def: Task definition to update
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            task_def = metadata_client.get_task_def_validated("validate_order")
            task_def.timeout_seconds = 90

            metadata_client.update_task_def(task_def)
            ```
        """
        self._metadata_api.update_task_def(body=task_def, **kwargs)

    def unregister_task_def(self, task_type: str, **kwargs) -> None:
        """Unregister a task definition by task type.

        Args:
            task_type: Type of task to unregister
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            metadata_client.unregister_task_def("old_task_type")
            ```
        """
        self._metadata_api.unregister_task_def(tasktype=task_type, **kwargs)

    @deprecated("get_task_def is deprecated; use get_task_def_validated instead")
    @typing_deprecated("get_task_def is deprecated; use get_task_def_validated instead")
    def get_task_def(self, task_type: str) -> object:  # type: ignore[override]
        """Get a task definition by task type.

        .. deprecated::
            Use get_task_def_validated() instead.

        Args:
            task_type: Type of task to retrieve

        Returns:
            Response object
        """
        return self._metadata_api.get_task_def(task_type)

    def get_task_def_validated(self, task_type: str, **kwargs) -> TaskDef:
        """Get a task definition by task type.

        Args:
            task_type: Type of task to retrieve
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            TaskDef instance

        Example:
            ```python
            task_def = metadata_client.get_task_def_validated("validate_order")
            print(f"Task: {task_def.name}, Timeout: {task_def.timeout_seconds}s")
            ```
        """
        task_def = self._metadata_api.get_task_def(tasktype=task_type, **kwargs)
        return self.api_client.deserialize_class(task_def, "TaskDef")

    def get_all_task_defs(self, **kwargs) -> List[TaskDef]:
        """Get all task definitions.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of TaskDef instances

        Example:
            ```python
            task_defs = metadata_client.get_all_task_defs()
            for task_def in task_defs:
                print(f"Task: {task_def.name}")
            ```
        """
        return self._metadata_api.get_task_defs(**kwargs)

    def add_workflow_tag(self, tag: MetadataTag, workflow_name: str, **kwargs) -> None:
        """Add a tag to a workflow.

        Args:
            tag: Tag to add
            workflow_name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.orkes.models.metadata_tag import MetadataTag

            tag = MetadataTag(key="environment", type="METADATA", value="production")
            metadata_client.add_workflow_tag(tag, "order_workflow")
            ```
        """
        self._tags_api.add_workflow_tag(body=tag, name=workflow_name, **kwargs)

    def delete_workflow_tag(self, tag: MetadataTag, workflow_name: str, **kwargs) -> None:
        """Delete a tag from a workflow.

        Args:
            tag: Tag to delete
            workflow_name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.orkes.models.metadata_tag import MetadataTag

            tag = MetadataTag(key="environment", type="METADATA", value="staging")
            metadata_client.delete_workflow_tag(tag, "order_workflow")
            ```
        """
        tag_str = TagString(tag.key, tag.type, tag.value)
        self._tags_api.delete_workflow_tag(body=tag_str, name=workflow_name, **kwargs)

    @deprecated("get_workflow_tags is deprecated; use get_workflow_tags_validated instead")
    @typing_deprecated("get_workflow_tags is deprecated; use get_workflow_tags_validated instead")
    def get_workflow_tags(self, workflow_name: str) -> object:  # type: ignore[override]
        """Get tags for a workflow.

        .. deprecated::
            Use get_workflow_tags_validated() instead.

        Args:
            workflow_name: Name of the workflow

        Returns:
            Response object
        """
        return self._tags_api.get_workflow_tags(workflow_name)

    def get_workflow_tags_validated(self, workflow_name: str, **kwargs) -> List[Tag]:
        """Get tags for a workflow.

        Args:
            workflow_name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of Tag instances

        Example:
            ```python
            tags = metadata_client.get_workflow_tags_validated("order_workflow")
            for tag in tags:
                print(f"Tag: {tag.key}={tag.value}")
            ```
        """
        tags = self._tags_api.get_workflow_tags(name=workflow_name, **kwargs)
        return self.api_client.deserialize_class(tags, "List[Tag]")

    def set_workflow_tags(self, tags: List[MetadataTag], workflow_name: str, **kwargs) -> None:
        """Set tags for a workflow, replacing any existing tags.

        Args:
            tags: List of tags to set
            workflow_name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.orkes.models.metadata_tag import MetadataTag

            tags = [
                MetadataTag(key="environment", type="METADATA", value="production"),
                MetadataTag(key="team", type="METADATA", value="platform")
            ]
            metadata_client.set_workflow_tags(tags, "order_workflow")
            ```
        """
        self._tags_api.set_workflow_tags(body=tags, name=workflow_name, **kwargs)

    @deprecated("addTaskTag is deprecated; use add_task_tag instead")
    @typing_deprecated("addTaskTag is deprecated; use add_task_tag instead")
    def addTaskTag(self, tag: MetadataTag, taskName: str):
        """Add a tag to a task.

        .. deprecated::
            Use add_task_tag() instead.

        Args:
            tag: Tag to add
            taskName: Name of the task
        """
        self._tags_api.add_task_tag(tag, taskName)

    def add_task_tag(self, tag: MetadataTag, task_name: str, **kwargs) -> None:
        """Add a tag to a task.

        Args:
            tag: Tag to add
            task_name: Name of the task
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.orkes.models.metadata_tag import MetadataTag

            tag = MetadataTag(key="priority", type="METADATA", value="high")
            metadata_client.add_task_tag(tag, "process_payment")
            ```
        """
        tag_str = TagString(tag.key, tag.type, tag.value)
        self._tags_api.add_task_tag(tag=tag_str, task_name=task_name, **kwargs)

    @deprecated("deleteTaskTag is deprecated; use delete_task_tag instead")
    @typing_deprecated("deleteTaskTag is deprecated; use delete_task_tag instead")
    def deleteTaskTag(self, tag: MetadataTag, taskName: str):
        """Delete a tag from a task.

        .. deprecated::
            Use delete_task_tag() instead.

        Args:
            tag: Tag to delete
            taskName: Name of the task
        """
        tagStr = TagString(tag.key, tag.type, tag.value)
        self._tags_api.delete_task_tag(tagStr, taskName)

    def delete_task_tag(self, tag: MetadataTag, task_name: str, **kwargs) -> None:
        """Delete a tag from a task.

        Args:
            tag: Tag to delete
            task_name: Name of the task
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.orkes.models.metadata_tag import MetadataTag

            tag = MetadataTag(key="priority", type="METADATA", value="low")
            metadata_client.delete_task_tag(tag, "process_payment")
            ```
        """
        tag_str = TagString(tag.key, tag.type, tag.value)
        self._tags_api.delete_task_tag(tag=tag_str, task_name=task_name, **kwargs)

    @deprecated("getTaskTags is deprecated; use get_task_tags instead")
    @typing_deprecated("getTaskTags is deprecated; use get_task_tags instead")
    def getTaskTags(self, taskName: str) -> object:
        """Get tags for a task.

        .. deprecated::
            Use get_task_tags() instead.

        Args:
            taskName: Name of the task

        Returns:
            Response object
        """
        return self._tags_api.get_task_tags(taskName)

    def get_task_tags(self, task_name: str, **kwargs) -> List[MetadataTag]:
        """Get tags for a task.

        Args:
            task_name: Name of the task
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of MetadataTag instances

        Example:
            ```python
            tags = metadata_client.get_task_tags("process_payment")
            for tag in tags:
                print(f"Tag: {tag.key}={tag.value}")
            ```
        """
        tags = self._tags_api.get_task_tags(task_name=task_name, **kwargs)
        result = self.api_client.deserialize_class(tags, "List[Tag]")
        return result

    @deprecated("setTaskTags is deprecated; use set_task_tags instead")
    @typing_deprecated("setTaskTags is deprecated; use set_task_tags instead")
    def setTaskTags(self, tags: List[MetadataTag], taskName: str):
        """Set tags for a task.

        .. deprecated::
            Use set_task_tags() instead.

        Args:
            tags: List of tags to set
            taskName: Name of the task
        """
        self._tags_api.set_task_tags(tags, taskName)

    def set_task_tags(self, tags: List[MetadataTag], task_name: str, **kwargs) -> None:
        """Set tags for a task, replacing any existing tags.

        Args:
            tags: List of tags to set
            task_name: Name of the task
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.orkes.models.metadata_tag import MetadataTag

            tags = [
                MetadataTag(key="priority", type="METADATA", value="high"),
                MetadataTag(key="category", type="METADATA", value="payment")
            ]
            metadata_client.set_task_tags(tags, "process_payment")
            ```
        """
        self._tags_api.set_task_tags(body=tags, task_name=task_name, **kwargs)

    @deprecated("setWorkflowRateLimit is deprecated; use set_workflow_rate_limit instead")
    @typing_deprecated("setWorkflowRateLimit is deprecated; use set_workflow_rate_limit instead")
    def setWorkflowRateLimit(self, rateLimit: int, workflowName: str):
        """Set rate limit for a workflow.

        .. deprecated::
            Use set_workflow_rate_limit() instead.

        Args:
            rateLimit: Rate limit value
            workflowName: Name of the workflow
        """
        self.remove_workflow_rate_limit(workflow_name=workflowName)
        rateLimitTag = RateLimitTag(workflowName, rateLimit)
        self._tags_api.add_workflow_tag(rateLimitTag, workflowName)

    def set_workflow_rate_limit(self, rate_limit: int, workflow_name: str, **kwargs) -> None:
        """Set rate limit for a workflow.

        Args:
            rate_limit: Rate limit value (executions per time window)
            workflow_name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Limit to 10 concurrent executions
            metadata_client.set_workflow_rate_limit(10, "order_workflow")
            ```
        """
        self.remove_workflow_rate_limit(workflow_name)
        rate_limit_tag = RateLimitTag(workflow_name, rate_limit)
        self._tags_api.add_workflow_tag(tag=rate_limit_tag, name=workflow_name, **kwargs)

    @deprecated("getWorkflowRateLimit is deprecated; use get_workflow_rate_limit instead")
    @typing_deprecated("getWorkflowRateLimit is deprecated; use get_workflow_rate_limit instead")
    def getWorkflowRateLimit(self, workflowName: str) -> Optional[int]:
        """Get rate limit for a workflow.

        .. deprecated::
            Use get_workflow_rate_limit() instead.

        Args:
            workflowName: Name of the workflow

        Returns:
            Rate limit value or None
        """
        tags = self._tags_api.get_workflow_tags(workflowName)
        for tag in tags:
            if tag.type == "RATE_LIMIT" and tag.key == workflowName:
                return tag.value

        return None

    def get_workflow_rate_limit(self, workflow_name: str, **kwargs) -> Optional[int]:
        """Get rate limit for a workflow.

        Args:
            workflow_name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Rate limit value or None if not set

        Example:
            ```python
            limit = metadata_client.get_workflow_rate_limit("order_workflow")
            if limit:
                print(f"Rate limit: {limit} concurrent executions")
            ```
        """
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
        """Remove rate limit for a workflow.

        .. deprecated::
            Use remove_workflow_rate_limit() instead.

        Args:
            workflowName: Name of the workflow
        """
        current_rate_limit = self.getWorkflowRateLimit(workflowName)
        if current_rate_limit:
            rateLimitTag = RateLimitTag(workflowName, current_rate_limit)
            self._tags_api.delete_workflow_tag(rateLimitTag, workflowName)

    def remove_workflow_rate_limit(self, workflow_name: str, **kwargs) -> None:
        """Remove rate limit for a workflow.

        Args:
            workflow_name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            metadata_client.remove_workflow_rate_limit("order_workflow")
            ```
        """
        current_rate_limit = self.get_workflow_rate_limit(workflow_name=workflow_name, **kwargs)
        if current_rate_limit:
            rate_limit_tag = RateLimitTag(workflow_name, current_rate_limit)
            self._tags_api.delete_workflow_tag(tag=rate_limit_tag, name=workflow_name, **kwargs)

    def upload_definitions_to_s3(self, **kwargs) -> None:
        """Upload workflow and task definitions to S3.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            metadata_client.upload_definitions_to_s3()
            ```
        """
        self._metadata_api.upload_workflows_and_tasks_definitions_to_s3(**kwargs)

    def upload_bpmn_file(self, body: IncomingBpmnFile, **kwargs) -> List[ExtendedWorkflowDef]:
        """Upload a BPMN file and convert it to workflow definitions.

        Args:
            body: BPMN file content
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of ExtendedWorkflowDef instances created from the BPMN file

        Example:
            ```python
            from conductor.client.http.models.incoming_bpmn_file import IncomingBpmnFile

            with open("workflow.bpmn", "r") as f:
                bpmn_content = f.read()

            bpmn_file = IncomingBpmnFile(content=bpmn_content)
            workflow_defs = metadata_client.upload_bpmn_file(bpmn_file)

            for workflow_def in workflow_defs:
                print(f"Created workflow: {workflow_def.name}")
            ```
        """
        return self._metadata_api.upload_bpmn_file(body=body, **kwargs)
