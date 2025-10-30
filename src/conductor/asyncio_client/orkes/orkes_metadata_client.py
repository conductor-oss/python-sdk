from __future__ import annotations

from typing import List, Optional

from conductor.asyncio_client.adapters.models.extended_task_def_adapter import (
    ExtendedTaskDefAdapter,
)
from conductor.asyncio_client.adapters.models.extended_workflow_def_adapter import (
    ExtendedWorkflowDefAdapter,
)
from conductor.asyncio_client.adapters.models.task_def_adapter import TaskDefAdapter
from conductor.asyncio_client.adapters.models.workflow_def_adapter import WorkflowDefAdapter
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.http.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient


class OrkesMetadataClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        super().__init__(configuration, api_client)

    # Task Definition Operations
    async def register_task_def(self, task_def: ExtendedTaskDefAdapter) -> None:
        """Register a new task definition"""
        await self.metadata_api.register_task_def([task_def])

    async def update_task_def(self, task_def: ExtendedTaskDefAdapter) -> None:
        """Update an existing task definition"""
        await self.metadata_api.update_task_def(task_def)

    async def unregister_task_def(self, task_type: str) -> None:
        """Unregister a task definition"""
        await self.metadata_api.unregister_task_def(task_type)

    async def get_task_def(self, task_type: str) -> TaskDefAdapter:
        """Get a task definition by task type"""
        return await self.metadata_api.get_task_def(task_type)

    async def get_task_defs(
        self,
        access: Optional[str] = None,
        metadata: Optional[bool] = None,
        tag_key: Optional[str] = None,
        tag_value: Optional[str] = None,
    ) -> List[TaskDefAdapter]:
        """Get all task definitions with optional filtering"""
        return await self.metadata_api.get_task_defs(
            access=access, metadata=metadata, tag_key=tag_key, tag_value=tag_value
        )

    # Workflow Definition Operations
    async def create_workflow_def(
        self,
        extended_workflow_def: ExtendedWorkflowDefAdapter,
        overwrite: Optional[bool] = None,
        new_version: Optional[bool] = None,
    ) -> object:
        """Create a new workflow definition"""
        return await self.metadata_api.create(
            extended_workflow_def, overwrite=overwrite, new_version=new_version
        )

    async def update_workflow_defs(
        self,
        extended_workflow_defs: List[ExtendedWorkflowDefAdapter],
        overwrite: Optional[bool] = None,
        new_version: Optional[bool] = None,
    ) -> object:
        """Create or update multiple workflow definitions"""
        return await self.metadata_api.update(
            extended_workflow_defs, overwrite=overwrite, new_version=new_version
        )

    async def get_workflow_def(
        self, name: str, version: Optional[int] = None, metadata: Optional[bool] = None
    ) -> WorkflowDefAdapter:
        """Get a workflow definition by name and version"""
        return await self.metadata_api.get(name, version=version, metadata=metadata)

    async def get_workflow_defs(
        self,
        access: Optional[str] = None,
        metadata: Optional[bool] = None,
        tag_key: Optional[str] = None,
        tag_value: Optional[str] = None,
        name: Optional[str] = None,
        short: Optional[bool] = None,
    ) -> List[WorkflowDefAdapter]:
        """Get all workflow definitions with optional filtering"""
        return await self.metadata_api.get_workflow_defs(
            access=access,
            metadata=metadata,
            tag_key=tag_key,
            tag_value=tag_value,
            name=name,
            short=short,
        )

    async def unregister_workflow_def(self, name: str, version: int) -> None:
        """Unregister a workflow definition"""
        await self.metadata_api.unregister_workflow_def(name, version)

    # Bulk Operations
    async def upload_definitions_to_s3(self) -> None:
        """Upload all workflows and tasks definitions to Object storage if configured"""
        await self.metadata_api.upload_workflows_and_tasks_definitions_to_s3()

    # Convenience Methods
    async def get_latest_workflow_def(self, name: str) -> WorkflowDefAdapter:
        """Get the latest version of a workflow definition"""
        return await self.get_workflow_def(name)

    async def get_workflow_def_with_metadata(
        self, name: str, version: Optional[int] = None
    ) -> WorkflowDefAdapter:
        """Get workflow definition with metadata included"""
        return await self.get_workflow_def(name, version=version, metadata=True)

    async def get_all_task_defs(self) -> List[TaskDefAdapter]:
        """Get all task definitions"""
        return await self.get_task_defs()

    async def get_all_workflow_defs(self) -> List[WorkflowDefAdapter]:
        """Get all workflow definitions"""
        return await self.get_workflow_defs()

    async def get_task_defs_by_tag(self, tag_key: str, tag_value: str) -> List[TaskDefAdapter]:
        """Get task definitions filtered by tag"""
        return await self.get_task_defs(tag_key=tag_key, tag_value=tag_value)

    async def get_workflow_defs_by_tag(
        self, tag_key: str, tag_value: str
    ) -> List[WorkflowDefAdapter]:
        """Get workflow definitions filtered by tag"""
        return await self.get_workflow_defs(tag_key=tag_key, tag_value=tag_value)

    async def get_task_defs_with_metadata(self) -> List[TaskDefAdapter]:
        """Get all task definitions with metadata"""
        return await self.get_task_defs(metadata=True)

    async def get_workflow_defs_with_metadata(self) -> List[WorkflowDefAdapter]:
        """Get all workflow definitions with metadata"""
        return await self.get_workflow_defs(metadata=True)

    async def get_workflow_defs_by_name(self, name: str) -> List[WorkflowDefAdapter]:
        """Get all versions of a workflow definition by name"""
        return await self.get_workflow_defs(name=name)

    async def get_workflow_defs_short(self) -> List[WorkflowDefAdapter]:
        """Get workflow definitions in short format (without task details)"""
        return await self.get_workflow_defs(short=True)

    # Access Control Methods
    async def get_task_defs_by_access(self, access: str) -> List[TaskDefAdapter]:
        """Get task definitions filtered by access level"""
        return await self.get_task_defs(access=access)

    async def get_workflow_defs_by_access(self, access: str) -> List[WorkflowDefAdapter]:
        """Get workflow definitions filtered by access level"""
        return await self.get_workflow_defs(access=access)

    # Bulk Registration
    async def register_workflow_def(
        self, extended_workflow_def: ExtendedWorkflowDefAdapter, overwrite: bool = False
    ) -> object:
        """Register a new workflow definition (alias for create_workflow_def)"""
        return await self.create_workflow_def(extended_workflow_def, overwrite=overwrite)

    async def update_workflow_def(
        self, extended_workflow_def: ExtendedWorkflowDefAdapter, overwrite: bool = True
    ) -> object:
        """Update a workflow definition (alias for create_workflow_def with overwrite)"""
        return await self.create_workflow_def(extended_workflow_def, overwrite=overwrite)

    # Legacy compatibility methods
    async def get_workflow_def_versions(self, name: str) -> List[int]:
        """Get all version numbers for a workflow definition"""
        workflow_defs = await self.get_workflow_defs_by_name(name)
        return [wd.version for wd in workflow_defs if wd.version is not None]

    async def get_workflow_def_latest_version(self, name: str) -> WorkflowDefAdapter:
        """Get the latest version workflow definition"""
        return await self.get_latest_workflow_def(name)

    async def get_workflow_def_latest_versions(self) -> List[WorkflowDefAdapter]:
        """Get the latest version of all workflow definitions"""
        return await self.get_all_workflow_defs()

    async def get_workflow_def_by_version(self, name: str, version: int) -> WorkflowDefAdapter:
        """Get workflow definition by name and specific version"""
        return await self.get_workflow_def(name, version=version)

    async def get_workflow_def_by_name(self, name: str) -> List[WorkflowDefAdapter]:
        """Get all versions of workflow definition by name"""
        return await self.get_workflow_defs_by_name(name)

    async def add_workflow_tag(self, tag: TagAdapter, workflow_name: str):
        await self.tags_api.add_workflow_tag(workflow_name, tag)

    async def delete_workflow_tag(self, tag: TagAdapter, workflow_name: str):
        await self.tags_api.delete_workflow_tag(workflow_name, tag)

    async def get_workflow_tags(self, workflow_name: str) -> List[TagAdapter]:
        return await self.tags_api.get_workflow_tags(workflow_name)

    async def set_workflow_tags(self, tags: List[TagAdapter], workflow_name: str):
        await self.tags_api.set_workflow_tags(workflow_name, tags)

    async def add_task_tag(self, tag: TagAdapter, task_name: str):
        await self.tags_api.add_task_tag(task_name, tag)

    async def delete_task_tag(self, tag: TagAdapter, task_name: str):
        await self.tags_api.delete_task_tag(task_name, tag)

    async def get_task_tags(self, task_name: str) -> List[TagAdapter]:
        return await self.tags_api.get_task_tags(task_name)

    async def set_task_tags(self, tags: List[TagAdapter], task_name: str):
        await self.tags_api.set_task_tags(task_name, tags)
