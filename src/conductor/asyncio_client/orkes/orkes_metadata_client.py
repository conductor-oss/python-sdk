from __future__ import annotations

from typing import Any, Dict, List, Optional, cast

from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.models.extended_task_def_adapter import (
    ExtendedTaskDefAdapter,
)
from conductor.asyncio_client.adapters.models.extended_workflow_def_adapter import (
    ExtendedWorkflowDefAdapter,
)
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.adapters.models.task_def_adapter import TaskDefAdapter
from conductor.asyncio_client.adapters.models.workflow_def_adapter import WorkflowDefAdapter
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient


class OrkesMetadataClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        super().__init__(configuration, api_client)

    # Task Definition Operations
    @deprecated("register_task_def is deprecated; use register_task_def_validated instead")
    @typing_deprecated("register_task_def is deprecated; use register_task_def_validated instead")
    async def register_task_def(self, task_def: ExtendedTaskDefAdapter) -> None:
        """Register a new task definition"""
        await self._metadata_api.register_task_def([task_def])

    async def register_task_def_validated(
        self, extended_task_def: List[ExtendedTaskDefAdapter], **kwargs
    ) -> None:
        """Register a new task definition and return None"""
        await self._metadata_api.register_task_def(extended_task_def=extended_task_def, **kwargs)

    async def update_task_def(self, task_def: ExtendedTaskDefAdapter, **kwargs) -> None:
        """Update an existing task definition"""
        await self._metadata_api.update_task_def(extended_task_def=task_def, **kwargs)

    async def unregister_task_def(self, task_type: str, **kwargs) -> None:
        """Unregister a task definition"""
        await self._metadata_api.unregister_task_def(tasktype=task_type, **kwargs)

    @deprecated("get_task_def is deprecated; use get_task_def_validated instead")
    @typing_deprecated("get_task_def is deprecated; use get_task_def_validated instead")
    async def get_task_def(self, task_type: str) -> object:
        """Get a task definition by task type"""
        return await self._metadata_api.get_task_def(task_type)

    async def get_task_def_validated(self, task_type: str, **kwargs) -> Optional[TaskDefAdapter]:
        """Get a task definition by task type and return a validated TaskDefAdapter"""
        result = await self._metadata_api.get_task_def(tasktype=task_type, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = TaskDefAdapter.from_dict(result_dict)

        return result_model

    async def get_task_defs(
        self,
        access: Optional[str] = None,
        metadata: Optional[bool] = None,
        tag_key: Optional[str] = None,
        tag_value: Optional[str] = None,
        **kwargs,
    ) -> List[TaskDefAdapter]:
        """Get all task definitions with optional filtering"""
        return await self._metadata_api.get_task_defs(
            access=access, metadata=metadata, tag_key=tag_key, tag_value=tag_value, **kwargs
        )

    # Workflow Definition Operations
    @deprecated("create_workflow_def is deprecated; use create_workflow_def_validated instead")
    @typing_deprecated(
        "create_workflow_def is deprecated; use create_workflow_def_validated instead"
    )
    async def create_workflow_def(
        self,
        extended_workflow_def: ExtendedWorkflowDefAdapter,
        overwrite: Optional[bool] = None,
        new_version: Optional[bool] = None,
    ) -> object:
        """Create a new workflow definition"""
        return await self._metadata_api.create(
            extended_workflow_def, overwrite=overwrite, new_version=new_version
        )

    async def create_workflow_def_validated(
        self,
        extended_workflow_def: ExtendedWorkflowDefAdapter,
        overwrite: Optional[bool] = None,
        new_version: Optional[bool] = None,
        **kwargs,
    ) -> None:
        """Create a new workflow definition and return None"""
        await self._metadata_api.create(
            extended_workflow_def, overwrite=overwrite, new_version=new_version, **kwargs
        )

    @deprecated("update_workflow_defs is deprecated; use update_workflow_defs_validated instead")
    @typing_deprecated(
        "update_workflow_defs is deprecated; use update_workflow_defs_validated instead"
    )
    async def update_workflow_defs(
        self,
        extended_workflow_defs: List[ExtendedWorkflowDefAdapter],
        overwrite: Optional[bool] = None,
        new_version: Optional[bool] = None,
    ) -> object:
        """Create or update multiple workflow definitions"""
        return await self._metadata_api.update(
            extended_workflow_defs, overwrite=overwrite, new_version=new_version
        )

    async def update_workflow_defs_validated(
        self,
        extended_workflow_defs: List[ExtendedWorkflowDefAdapter],
        overwrite: Optional[bool] = None,
        new_version: Optional[bool] = None,
        **kwargs,
    ) -> None:
        """Create or update multiple workflow definitions and return None"""
        await self._metadata_api.update(
            extended_workflow_def=extended_workflow_defs,
            overwrite=overwrite,
            new_version=new_version,
            **kwargs,
        )

    async def get_workflow_def(
        self, name: str, version: Optional[int] = None, metadata: Optional[bool] = None, **kwargs
    ) -> WorkflowDefAdapter:
        """Get a workflow definition by name and version"""
        return await self._metadata_api.get(name=name, version=version, metadata=metadata, **kwargs)

    async def get_workflow_defs(
        self,
        access: Optional[str] = None,
        metadata: Optional[bool] = None,
        tag_key: Optional[str] = None,
        tag_value: Optional[str] = None,
        name: Optional[str] = None,
        short: Optional[bool] = None,
        **kwargs,
    ) -> List[WorkflowDefAdapter]:
        """Get all workflow definitions with optional filtering"""
        return await self._metadata_api.get_workflow_defs(
            access=access,
            metadata=metadata,
            tag_key=tag_key,
            tag_value=tag_value,
            name=name,
            short=short,
            **kwargs,
        )

    async def unregister_workflow_def(self, name: str, version: int, **kwargs) -> None:
        """Unregister a workflow definition"""
        await self._metadata_api.unregister_workflow_def(name=name, version=version, **kwargs)

    # Bulk Operations
    async def upload_definitions_to_s3(self, **kwargs) -> None:
        """Upload all workflows and tasks definitions to Object storage if configured"""
        await self._metadata_api.upload_workflows_and_tasks_definitions_to_s3(**kwargs)

    # Convenience Methods
    async def get_latest_workflow_def(self, name: str, **kwargs) -> WorkflowDefAdapter:
        """Get the latest version of a workflow definition"""
        return await self.get_workflow_def(name=name, **kwargs)

    async def get_workflow_def_with_metadata(
        self, name: str, version: Optional[int] = None, **kwargs
    ) -> WorkflowDefAdapter:
        """Get workflow definition with metadata included"""
        return await self.get_workflow_def(name=name, version=version, metadata=True, **kwargs)

    async def get_all_task_defs(self, **kwargs) -> List[TaskDefAdapter]:
        """Get all task definitions"""
        return await self.get_task_defs(**kwargs)

    async def get_all_workflow_defs(self, **kwargs) -> List[WorkflowDefAdapter]:
        """Get all workflow definitions"""
        return await self.get_workflow_defs(**kwargs)

    async def get_task_defs_by_tag(
        self, tag_key: str, tag_value: str, **kwargs
    ) -> List[TaskDefAdapter]:
        """Get task definitions filtered by tag"""
        return await self.get_task_defs(tag_key=tag_key, tag_value=tag_value, **kwargs)

    async def get_workflow_defs_by_tag(
        self, tag_key: str, tag_value: str, **kwargs
    ) -> List[WorkflowDefAdapter]:
        """Get workflow definitions filtered by tag"""
        return await self.get_workflow_defs(tag_key=tag_key, tag_value=tag_value, **kwargs)

    async def get_task_defs_with_metadata(self, **kwargs) -> List[TaskDefAdapter]:
        """Get all task definitions with metadata"""
        return await self.get_task_defs(metadata=True, **kwargs)

    async def get_workflow_defs_with_metadata(self, **kwargs) -> List[WorkflowDefAdapter]:
        """Get all workflow definitions with metadata"""
        return await self.get_workflow_defs(metadata=True, **kwargs)

    async def get_workflow_defs_by_name(self, name: str, **kwargs) -> List[WorkflowDefAdapter]:
        """Get all versions of a workflow definition by name"""
        return await self.get_workflow_defs(name=name, **kwargs)

    async def get_workflow_defs_short(self, **kwargs) -> List[WorkflowDefAdapter]:
        """Get workflow definitions in short format (without task details)"""
        return await self.get_workflow_defs(short=True, **kwargs)

    # Access Control Methods
    async def get_task_defs_by_access(self, access: str, **kwargs) -> List[TaskDefAdapter]:
        """Get task definitions filtered by access level"""
        return await self.get_task_defs(access=access, **kwargs)

    async def get_workflow_defs_by_access(self, access: str, **kwargs) -> List[WorkflowDefAdapter]:
        """Get workflow definitions filtered by access level"""
        return await self.get_workflow_defs(access=access, **kwargs)

    # Bulk Registration
    @deprecated("register_workflow_def is deprecated; use register_workflow_def_validated instead")
    @typing_deprecated(
        "register_workflow_def is deprecated; use register_workflow_def_validated instead"
    )
    async def register_workflow_def(
        self,
        extended_workflow_def: ExtendedWorkflowDefAdapter,
        overwrite: bool = False,
    ) -> object:
        """Register a new workflow definition (alias for create_workflow_def)"""
        return await self.create_workflow_def(extended_workflow_def, overwrite=overwrite)

    async def register_workflow_def_validated(
        self, extended_workflow_def: ExtendedWorkflowDefAdapter, overwrite: bool = False, **kwargs
    ) -> None:
        """Register a new workflow definition and return None (alias for create_workflow_def_validated)"""
        await self.create_workflow_def_validated(
            extended_workflow_def=extended_workflow_def, overwrite=overwrite, **kwargs
        )

    @deprecated("update_workflow_def is deprecated; use update_workflow_def_validated instead")
    @typing_deprecated(
        "update_workflow_def is deprecated; use update_workflow_def_validated instead"
    )
    async def update_workflow_def(
        self, extended_workflow_def: ExtendedWorkflowDefAdapter, overwrite: bool = True
    ) -> object:
        """Update a workflow definition (alias for create_workflow_def with overwrite)"""
        return await self.create_workflow_def(extended_workflow_def, overwrite=overwrite)

    async def update_workflow_def_validated(
        self, extended_workflow_def: ExtendedWorkflowDefAdapter, overwrite: bool = True, **kwargs
    ) -> None:
        """Update a workflow definition and return None (alias for create_workflow_def_validated with overwrite)"""
        await self.create_workflow_def_validated(
            extended_workflow_def=extended_workflow_def, overwrite=overwrite, **kwargs
        )

    # Legacy compatibility methods
    async def get_workflow_def_versions(self, name: str, **kwargs) -> List[int]:
        """Get all version numbers for a workflow definition"""
        workflow_defs = await self.get_workflow_defs_by_name(name=name, **kwargs)
        return [wd.version for wd in workflow_defs if wd.version is not None]

    async def get_workflow_def_latest_version(self, name: str, **kwargs) -> WorkflowDefAdapter:
        """Get the latest version workflow definition"""
        return await self.get_latest_workflow_def(name=name, **kwargs)

    async def get_workflow_def_latest_versions(self, **kwargs) -> List[WorkflowDefAdapter]:
        """Get the latest version of all workflow definitions"""
        return await self.get_all_workflow_defs(**kwargs)

    async def get_workflow_def_by_version(
        self, name: str, version: int, **kwargs
    ) -> WorkflowDefAdapter:
        """Get workflow definition by name and specific version"""
        return await self.get_workflow_def(name=name, version=version, **kwargs)

    async def get_workflow_def_by_name(self, name: str, **kwargs) -> List[WorkflowDefAdapter]:
        """Get all versions of workflow definition by name"""
        return await self.get_workflow_defs_by_name(name=name, **kwargs)

    async def add_workflow_tag(self, tag: TagAdapter, workflow_name: str, **kwargs) -> None:
        await self._tags_api.add_workflow_tag(name=workflow_name, tag=tag, **kwargs)

    async def delete_workflow_tag(self, tag: TagAdapter, workflow_name: str, **kwargs) -> None:
        await self._tags_api.delete_workflow_tag(name=workflow_name, tag=tag, **kwargs)

    async def get_workflow_tags(self, workflow_name: str, **kwargs) -> List[TagAdapter]:
        return await self._tags_api.get_workflow_tags(name=workflow_name, **kwargs)

    async def set_workflow_tags(self, tags: List[TagAdapter], workflow_name: str, **kwargs) -> None:
        await self._tags_api.set_workflow_tags(name=workflow_name, tag=tags, **kwargs)

    async def add_task_tag(self, tag: TagAdapter, task_name: str, **kwargs) -> None:
        await self._tags_api.add_task_tag(task_name=task_name, tag=tag, **kwargs)

    async def delete_task_tag(self, tag: TagAdapter, task_name: str, **kwargs) -> None:
        await self._tags_api.delete_task_tag(task_name=task_name, tag=tag, **kwargs)

    async def get_task_tags(self, task_name: str, **kwargs) -> List[TagAdapter]:
        return await self._tags_api.get_task_tags(task_name=task_name, **kwargs)

    async def set_task_tags(self, tags: List[TagAdapter], task_name: str, **kwargs) -> None:
        await self._tags_api.set_task_tags(task_name=task_name, tag=tags, **kwargs)

    async def set_workflow_rate_limit(self, rate_limit: str, workflow_name: str) -> None:
        await self.remove_workflow_rate_limit(workflow_name=workflow_name)
        rate_limit_tag = TagAdapter(key=workflow_name, type="RATE_LIMIT", value=rate_limit)
        await self._tags_api.add_workflow_tag(name=workflow_name, tag=rate_limit_tag)

    async def get_workflow_rate_limit(self, workflow_name: str) -> Optional[str]:
        tags = await self._tags_api.get_workflow_tags(name=workflow_name)
        for tag in tags:
            if tag.type == "RATE_LIMIT" and tag.key == workflow_name:
                return tag.value

        return None

    async def remove_workflow_rate_limit(self, workflow_name: str) -> None:
        current_rate_limit = await self.get_workflow_rate_limit(workflow_name=workflow_name)
        if current_rate_limit:
            rate_limit_tag = TagAdapter(
                key=workflow_name, type="RATE_LIMIT", value=current_rate_limit
            )
            await self._tags_api.delete_workflow_tag(name=workflow_name, tag=rate_limit_tag)
