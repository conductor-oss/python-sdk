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
        """Initialize the OrkesMetadataClient with configuration and API client.

        Args:
            configuration: Configuration object containing server settings and authentication
            api_client: ApiClient instance for making API requests

        Example:
            ```python
            from conductor.asyncio_client.configuration.configuration import Configuration
            from conductor.asyncio_client.adapters import ApiClient

            config = Configuration(server_api_url="http://localhost:8080/api")
            api_client = ApiClient(configuration=config)
            metadata_client = OrkesMetadataClient(config, api_client)
            ```
        """
        super().__init__(configuration, api_client)

    # Task Definition Operations
    @deprecated("register_task_def is deprecated; use register_task_def_validated instead")
    @typing_deprecated("register_task_def is deprecated; use register_task_def_validated instead")
    async def register_task_def(self, task_def: ExtendedTaskDefAdapter) -> None:
        """Register a new task definition.

        .. deprecated::
            Use register_task_def_validated instead for type-safe validated responses.

        Args:
            task_def: Task definition to register

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.extended_task_def_adapter import ExtendedTaskDefAdapter

            task_def = ExtendedTaskDefAdapter(
                name="my_task",
                description="My custom task",
                timeout_seconds=60,
                retry_count=3
            )
            await metadata_client.register_task_def(task_def)
            ```
        """
        await self._metadata_api.register_task_def([task_def])

    async def register_task_def_validated(
        self, extended_task_def: List[ExtendedTaskDefAdapter], **kwargs
    ) -> None:
        """Register one or more task definitions.

        Args:
            extended_task_def: List of task definitions to register
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.extended_task_def_adapter import ExtendedTaskDefAdapter

            task_defs = [
                ExtendedTaskDefAdapter(
                    name="task1",
                    description="First task",
                    timeout_seconds=60
                ),
                ExtendedTaskDefAdapter(
                    name="task2",
                    description="Second task",
                    timeout_seconds=120
                )
            ]
            await metadata_client.register_task_def_validated(task_defs)
            ```
        """
        await self._metadata_api.register_task_def(extended_task_def=extended_task_def, **kwargs)

    async def update_task_def(self, task_def: ExtendedTaskDefAdapter, **kwargs) -> None:
        """Update an existing task definition.

        Args:
            task_def: Updated task definition
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.extended_task_def_adapter import ExtendedTaskDefAdapter

            task_def = ExtendedTaskDefAdapter(
                name="my_task",
                description="Updated description",
                timeout_seconds=90,
                retry_count=5
            )
            await metadata_client.update_task_def(task_def)
            ```
        """
        await self._metadata_api.update_task_def(extended_task_def=task_def, **kwargs)

    async def unregister_task_def(self, task_type: str, **kwargs) -> None:
        """Unregister (delete) a task definition.

        Args:
            task_type: Name of the task definition to unregister
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await metadata_client.unregister_task_def("my_task")
            ```
        """
        await self._metadata_api.unregister_task_def(tasktype=task_type, **kwargs)

    @deprecated("get_task_def is deprecated; use get_task_def_validated instead")
    @typing_deprecated("get_task_def is deprecated; use get_task_def_validated instead")
    async def get_task_def(self, task_type: str) -> object:
        """Get a task definition by task type.

        .. deprecated::
            Use get_task_def_validated instead for type-safe validated responses.

        Args:
            task_type: Name of the task definition

        Returns:
            Raw response object from the API

        Example:
            ```python
            task_def = await metadata_client.get_task_def("my_task")
            ```
        """
        return await self._metadata_api.get_task_def(task_type)

    async def get_task_def_validated(self, task_type: str, **kwargs) -> Optional[TaskDefAdapter]:
        """Get a task definition by task type.

        Args:
            task_type: Name of the task definition
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            TaskDefAdapter instance containing the task definition, or None if not found

        Example:
            ```python
            task_def = await metadata_client.get_task_def_validated("my_task")
            if task_def:
                print(f"Task: {task_def.name}, Timeout: {task_def.timeout_seconds}s")
            ```
        """
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
        """Get all task definitions with optional filtering.

        Args:
            access: Filter by access level (e.g., "READ", "EXECUTE")
            metadata: If True, include metadata in the response
            tag_key: Filter by tag key
            tag_value: Filter by tag value (requires tag_key)
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of TaskDefAdapter instances

        Example:
            ```python
            # Get all task definitions
            all_tasks = await metadata_client.get_task_defs()

            # Get tasks with metadata
            tasks_with_metadata = await metadata_client.get_task_defs(metadata=True)

            # Get tasks by tag
            tagged_tasks = await metadata_client.get_task_defs(
                tag_key="environment",
                tag_value="production"
            )
            ```
        """
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
        """Create a new workflow definition.

        .. deprecated::
            Use create_workflow_def_validated instead for type-safe validated responses.

        Args:
            extended_workflow_def: Workflow definition to create
            overwrite: If True, overwrite existing definition with same name
            new_version: If True, create a new version instead of overwriting

        Returns:
            Raw response object from the API

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.extended_workflow_def_adapter import ExtendedWorkflowDefAdapter

            workflow_def = ExtendedWorkflowDefAdapter(
                name="my_workflow",
                description="My workflow",
                version=1,
                tasks=[]
            )
            await metadata_client.create_workflow_def(workflow_def)
            ```
        """
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
        """Create a new workflow definition.

        Args:
            extended_workflow_def: Workflow definition to create
            overwrite: If True, overwrite existing definition with same name
            new_version: If True, create a new version instead of overwriting
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.extended_workflow_def_adapter import ExtendedWorkflowDefAdapter
            from conductor.asyncio_client.adapters.models.workflow_task_adapter import WorkflowTaskAdapter

            workflow_def = ExtendedWorkflowDefAdapter(
                name="my_workflow",
                description="Order processing workflow",
                version=1,
                tasks=[
                    WorkflowTaskAdapter(
                        name="validate_order",
                        task_reference_name="validate_ref",
                        type="SIMPLE"
                    )
                ]
            )
            await metadata_client.create_workflow_def_validated(workflow_def)
            ```
        """
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
        """Create or update multiple workflow definitions.

        .. deprecated::
            Use update_workflow_defs_validated instead for type-safe validated responses.

        Args:
            extended_workflow_defs: List of workflow definitions to create/update
            overwrite: If True, overwrite existing definitions
            new_version: If True, create new versions instead of overwriting

        Returns:
            Raw response object from the API

        Example:
            ```python
            workflows = [workflow_def1, workflow_def2]
            await metadata_client.update_workflow_defs(workflows, overwrite=True)
            ```
        """
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
        """Create or update multiple workflow definitions.

        Args:
            extended_workflow_defs: List of workflow definitions to create/update
            overwrite: If True, overwrite existing definitions
            new_version: If True, create new versions instead of overwriting
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            workflows = [workflow_def1, workflow_def2]
            await metadata_client.update_workflow_defs_validated(workflows, overwrite=True)
            ```
        """
        await self._metadata_api.update(
            extended_workflow_def=extended_workflow_defs,
            overwrite=overwrite,
            new_version=new_version,
            **kwargs,
        )

    async def get_workflow_def(
        self, name: str, version: Optional[int] = None, metadata: Optional[bool] = None, **kwargs
    ) -> WorkflowDefAdapter:
        """Get a workflow definition by name and version.

        Args:
            name: Name of the workflow definition
            version: Optional version number. If None, returns the latest version
            metadata: If True, include metadata in the response
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowDefAdapter instance containing the workflow definition

        Example:
            ```python
            # Get latest version
            workflow = await metadata_client.get_workflow_def("my_workflow")

            # Get specific version
            workflow_v2 = await metadata_client.get_workflow_def("my_workflow", version=2)

            # Get with metadata
            workflow_meta = await metadata_client.get_workflow_def("my_workflow", metadata=True)
            ```
        """
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
        """Get all workflow definitions with optional filtering.

        Args:
            access: Filter by access level (e.g., "READ", "EXECUTE")
            metadata: If True, include metadata in the response
            tag_key: Filter by tag key
            tag_value: Filter by tag value (requires tag_key)
            name: Filter by workflow name (returns all versions of that workflow)
            short: If True, return short format without task details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of WorkflowDefAdapter instances

        Example:
            ```python
            # Get all workflows
            all_workflows = await metadata_client.get_workflow_defs()

            # Get workflows by tag
            prod_workflows = await metadata_client.get_workflow_defs(
                tag_key="environment",
                tag_value="production"
            )

            # Get short format (faster)
            workflows_short = await metadata_client.get_workflow_defs(short=True)
            ```
        """
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
        """Unregister (delete) a workflow definition.

        Args:
            name: Name of the workflow definition
            version: Version number to unregister
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await metadata_client.unregister_workflow_def("my_workflow", version=1)
            ```
        """
        await self._metadata_api.unregister_workflow_def(name=name, version=version, **kwargs)

    # Bulk Operations
    async def upload_definitions_to_s3(self, **kwargs) -> None:
        """Upload all workflow and task definitions to object storage.

        Backs up all metadata definitions to configured S3-compatible storage.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await metadata_client.upload_definitions_to_s3()
            ```
        """
        await self._metadata_api.upload_workflows_and_tasks_definitions_to_s3(**kwargs)

    # Convenience Methods
    async def get_latest_workflow_def(self, name: str, **kwargs) -> WorkflowDefAdapter:
        """Get the latest version of a workflow definition.

        Args:
            name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowDefAdapter instance for the latest version

        Example:
            ```python
            latest = await metadata_client.get_latest_workflow_def("my_workflow")
            print(f"Latest version: {latest.version}")
            ```
        """
        return await self.get_workflow_def(name=name, **kwargs)

    async def get_workflow_def_with_metadata(
        self, name: str, version: Optional[int] = None, **kwargs
    ) -> WorkflowDefAdapter:
        """Get workflow definition with metadata included.

        Args:
            name: Name of the workflow
            version: Optional version number
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowDefAdapter instance with metadata

        Example:
            ```python
            workflow = await metadata_client.get_workflow_def_with_metadata("my_workflow")
            ```
        """
        return await self.get_workflow_def(name=name, version=version, metadata=True, **kwargs)

    async def get_all_task_defs(self, **kwargs) -> List[TaskDefAdapter]:
        """Get all task definitions.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of all TaskDefAdapter instances

        Example:
            ```python
            tasks = await metadata_client.get_all_task_defs()
            print(f"Total tasks: {len(tasks)}")
            ```
        """
        return await self.get_task_defs(**kwargs)

    async def get_all_workflow_defs(self, **kwargs) -> List[WorkflowDefAdapter]:
        """Get all workflow definitions.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of all WorkflowDefAdapter instances

        Example:
            ```python
            workflows = await metadata_client.get_all_workflow_defs()
            print(f"Total workflows: {len(workflows)}")
            ```
        """
        return await self.get_workflow_defs(**kwargs)

    async def get_task_defs_by_tag(
        self, tag_key: str, tag_value: str, **kwargs
    ) -> List[TaskDefAdapter]:
        """Get task definitions filtered by tag.

        Args:
            tag_key: Tag key to filter by
            tag_value: Tag value to filter by
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of TaskDefAdapter instances with matching tag

        Example:
            ```python
            tasks = await metadata_client.get_task_defs_by_tag("environment", "production")
            ```
        """
        return await self.get_task_defs(tag_key=tag_key, tag_value=tag_value, **kwargs)

    async def get_workflow_defs_by_tag(
        self, tag_key: str, tag_value: str, **kwargs
    ) -> List[WorkflowDefAdapter]:
        """Get workflow definitions filtered by tag.

        Args:
            tag_key: Tag key to filter by
            tag_value: Tag value to filter by
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of WorkflowDefAdapter instances with matching tag

        Example:
            ```python
            workflows = await metadata_client.get_workflow_defs_by_tag("team", "platform")
            ```
        """
        return await self.get_workflow_defs(tag_key=tag_key, tag_value=tag_value, **kwargs)

    async def get_task_defs_with_metadata(self, **kwargs) -> List[TaskDefAdapter]:
        """Get all task definitions with metadata.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of TaskDefAdapter instances with metadata

        Example:
            ```python
            tasks = await metadata_client.get_task_defs_with_metadata()
            ```
        """
        return await self.get_task_defs(metadata=True, **kwargs)

    async def get_workflow_defs_with_metadata(self, **kwargs) -> List[WorkflowDefAdapter]:
        """Get all workflow definitions with metadata.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of WorkflowDefAdapter instances with metadata

        Example:
            ```python
            workflows = await metadata_client.get_workflow_defs_with_metadata()
            ```
        """
        return await self.get_workflow_defs(metadata=True, **kwargs)

    async def get_workflow_defs_by_name(self, name: str, **kwargs) -> List[WorkflowDefAdapter]:
        """Get all versions of a workflow definition by name.

        Args:
            name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of WorkflowDefAdapter instances for all versions

        Example:
            ```python
            versions = await metadata_client.get_workflow_defs_by_name("my_workflow")
            for v in versions:
                print(f"Version {v.version}")
            ```
        """
        return await self.get_workflow_defs(name=name, **kwargs)

    async def get_workflow_defs_short(self, **kwargs) -> List[WorkflowDefAdapter]:
        """Get workflow definitions in short format (without task details).

        Faster than full format, useful for listing workflows.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of WorkflowDefAdapter instances in short format

        Example:
            ```python
            workflows = await metadata_client.get_workflow_defs_short()
            ```
        """
        return await self.get_workflow_defs(short=True, **kwargs)

    # Access Control Methods
    async def get_task_defs_by_access(self, access: str, **kwargs) -> List[TaskDefAdapter]:
        """Get task definitions filtered by access level.

        Args:
            access: Access level to filter by (e.g., "READ", "EXECUTE")
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of TaskDefAdapter instances with specified access level

        Example:
            ```python
            executable_tasks = await metadata_client.get_task_defs_by_access("EXECUTE")
            ```
        """
        return await self.get_task_defs(access=access, **kwargs)

    async def get_workflow_defs_by_access(self, access: str, **kwargs) -> List[WorkflowDefAdapter]:
        """Get workflow definitions filtered by access level.

        Args:
            access: Access level to filter by (e.g., "READ", "EXECUTE")
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of WorkflowDefAdapter instances with specified access level

        Example:
            ```python
            readable_workflows = await metadata_client.get_workflow_defs_by_access("READ")
            ```
        """
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
        """Register a new workflow definition (alias for create_workflow_def).

        .. deprecated::
            Use register_workflow_def_validated instead for type-safe validated responses.

        Args:
            extended_workflow_def: Workflow definition to register
            overwrite: If True, overwrite existing definition

        Returns:
            Raw response object from the API

        Example:
            ```python
            await metadata_client.register_workflow_def(workflow_def, overwrite=False)
            ```
        """
        return await self.create_workflow_def(extended_workflow_def, overwrite=overwrite)

    async def register_workflow_def_validated(
        self, extended_workflow_def: ExtendedWorkflowDefAdapter, overwrite: bool = False, **kwargs
    ) -> None:
        """Register a new workflow definition (alias for create_workflow_def_validated).

        Args:
            extended_workflow_def: Workflow definition to register
            overwrite: If True, overwrite existing definition
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await metadata_client.register_workflow_def_validated(workflow_def)
            ```
        """
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
        """Update a workflow definition (alias for create_workflow_def with overwrite).

        .. deprecated::
            Use update_workflow_def_validated instead for type-safe validated responses.

        Args:
            extended_workflow_def: Updated workflow definition
            overwrite: If True, overwrite existing definition (default: True)

        Returns:
            Raw response object from the API

        Example:
            ```python
            await metadata_client.update_workflow_def(workflow_def)
            ```
        """
        return await self.create_workflow_def(extended_workflow_def, overwrite=overwrite)

    async def update_workflow_def_validated(
        self, extended_workflow_def: ExtendedWorkflowDefAdapter, overwrite: bool = True, **kwargs
    ) -> None:
        """Update a workflow definition (alias for create_workflow_def_validated with overwrite).

        Args:
            extended_workflow_def: Updated workflow definition
            overwrite: If True, overwrite existing definition (default: True)
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await metadata_client.update_workflow_def_validated(workflow_def)
            ```
        """
        await self.create_workflow_def_validated(
            extended_workflow_def=extended_workflow_def, overwrite=overwrite, **kwargs
        )

    # Legacy compatibility methods
    async def get_workflow_def_versions(self, name: str, **kwargs) -> List[int]:
        """Get all version numbers for a workflow definition.

        Args:
            name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of version numbers

        Example:
            ```python
            versions = await metadata_client.get_workflow_def_versions("my_workflow")
            print(f"Available versions: {versions}")  # [1, 2, 3]
            ```
        """
        workflow_defs = await self.get_workflow_defs_by_name(name=name, **kwargs)
        return [wd.version for wd in workflow_defs if wd.version is not None]

    async def get_workflow_def_latest_version(self, name: str, **kwargs) -> WorkflowDefAdapter:
        """Get the latest version workflow definition (alias for get_latest_workflow_def).

        Args:
            name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowDefAdapter instance for the latest version

        Example:
            ```python
            latest = await metadata_client.get_workflow_def_latest_version("my_workflow")
            ```
        """
        return await self.get_latest_workflow_def(name=name, **kwargs)

    async def get_workflow_def_latest_versions(self, **kwargs) -> List[WorkflowDefAdapter]:
        """Get the latest version of all workflow definitions.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of WorkflowDefAdapter instances (latest version of each workflow)

        Example:
            ```python
            all_latest = await metadata_client.get_workflow_def_latest_versions()
            ```
        """
        return await self.get_all_workflow_defs(**kwargs)

    async def get_workflow_def_by_version(
        self, name: str, version: int, **kwargs
    ) -> WorkflowDefAdapter:
        """Get workflow definition by name and specific version.

        Args:
            name: Name of the workflow
            version: Version number
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            WorkflowDefAdapter instance for the specified version

        Example:
            ```python
            v2 = await metadata_client.get_workflow_def_by_version("my_workflow", 2)
            ```
        """
        return await self.get_workflow_def(name=name, version=version, **kwargs)

    async def get_workflow_def_by_name(self, name: str, **kwargs) -> List[WorkflowDefAdapter]:
        """Get all versions of workflow definition by name.

        Args:
            name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of WorkflowDefAdapter instances for all versions

        Example:
            ```python
            all_versions = await metadata_client.get_workflow_def_by_name("my_workflow")
            ```
        """
        return await self.get_workflow_defs_by_name(name=name, **kwargs)

    async def add_workflow_tag(self, tag: TagAdapter, workflow_name: str, **kwargs) -> None:
        """Add a tag to a workflow definition.

        Args:
            tag: Tag to add
            workflow_name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tag = TagAdapter(key="environment", value="production")
            await metadata_client.add_workflow_tag(tag, "my_workflow")
            ```
        """
        await self._tags_api.add_workflow_tag(name=workflow_name, tag=tag, **kwargs)

    async def delete_workflow_tag(self, tag: TagAdapter, workflow_name: str, **kwargs) -> None:
        """Delete a tag from a workflow definition.

        Args:
            tag: Tag to delete
            workflow_name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tag = TagAdapter(key="environment", value="production")
            await metadata_client.delete_workflow_tag(tag, "my_workflow")
            ```
        """
        await self._tags_api.delete_workflow_tag(name=workflow_name, tag=tag, **kwargs)

    async def get_workflow_tags(self, workflow_name: str, **kwargs) -> List[TagAdapter]:
        """Get all tags for a workflow definition.

        Args:
            workflow_name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of TagAdapter instances

        Example:
            ```python
            tags = await metadata_client.get_workflow_tags("my_workflow")
            for tag in tags:
                print(f"{tag.key}: {tag.value}")
            ```
        """
        return await self._tags_api.get_workflow_tags(name=workflow_name, **kwargs)

    async def set_workflow_tags(self, tags: List[TagAdapter], workflow_name: str, **kwargs) -> None:
        """Set tags for a workflow definition (replaces existing tags).

        Args:
            tags: List of tags to set
            workflow_name: Name of the workflow
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [
                TagAdapter(key="environment", value="production"),
                TagAdapter(key="team", value="platform")
            ]
            await metadata_client.set_workflow_tags(tags, "my_workflow")
            ```
        """
        await self._tags_api.set_workflow_tags(name=workflow_name, tag=tags, **kwargs)

    async def add_task_tag(self, tag: TagAdapter, task_name: str, **kwargs) -> None:
        """Add a tag to a task definition.

        Args:
            tag: Tag to add
            task_name: Name of the task
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tag = TagAdapter(key="category", value="data-processing")
            await metadata_client.add_task_tag(tag, "my_task")
            ```
        """
        await self._tags_api.add_task_tag(task_name=task_name, tag=tag, **kwargs)

    async def delete_task_tag(self, tag: TagAdapter, task_name: str, **kwargs) -> None:
        """Delete a tag from a task definition.

        Args:
            tag: Tag to delete
            task_name: Name of the task
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tag = TagAdapter(key="category", value="data-processing")
            await metadata_client.delete_task_tag(tag, "my_task")
            ```
        """
        await self._tags_api.delete_task_tag(task_name=task_name, tag=tag, **kwargs)

    async def get_task_tags(self, task_name: str, **kwargs) -> List[TagAdapter]:
        """Get all tags for a task definition.

        Args:
            task_name: Name of the task
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of TagAdapter instances

        Example:
            ```python
            tags = await metadata_client.get_task_tags("my_task")
            for tag in tags:
                print(f"{tag.key}: {tag.value}")
            ```
        """
        return await self._tags_api.get_task_tags(task_name=task_name, **kwargs)

    async def set_task_tags(self, tags: List[TagAdapter], task_name: str, **kwargs) -> None:
        """Set tags for a task definition (replaces existing tags).

        Args:
            tags: List of tags to set
            task_name: Name of the task
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [
                TagAdapter(key="category", value="data-processing"),
                TagAdapter(key="priority", value="high")
            ]
            await metadata_client.set_task_tags(tags, "my_task")
            ```
        """
        await self._tags_api.set_task_tags(task_name=task_name, tag=tags, **kwargs)

    async def set_workflow_rate_limit(self, rate_limit: str, workflow_name: str) -> None:
        """Set rate limit for a workflow.

        Rate limits control how many instances of a workflow can execute concurrently.

        Args:
            rate_limit: Rate limit value (e.g., "10" for max 10 concurrent executions)
            workflow_name: Name of the workflow

        Returns:
            None

        Example:
            ```python
            # Limit to 5 concurrent executions
            await metadata_client.set_workflow_rate_limit("5", "my_workflow")
            ```
        """
        await self.remove_workflow_rate_limit(workflow_name=workflow_name)
        rate_limit_tag = TagAdapter(key=workflow_name, type="RATE_LIMIT", value=rate_limit)
        await self._tags_api.add_workflow_tag(name=workflow_name, tag=rate_limit_tag)

    async def get_workflow_rate_limit(self, workflow_name: str) -> Optional[str]:
        """Get rate limit for a workflow.

        Args:
            workflow_name: Name of the workflow

        Returns:
            Rate limit value as string, or None if no rate limit is set

        Example:
            ```python
            limit = await metadata_client.get_workflow_rate_limit("my_workflow")
            if limit:
                print(f"Rate limit: {limit} concurrent executions")
            else:
                print("No rate limit set")
            ```
        """
        tags = await self._tags_api.get_workflow_tags(name=workflow_name)
        for tag in tags:
            if tag.type == "RATE_LIMIT" and tag.key == workflow_name:
                return tag.value

        return None

    async def remove_workflow_rate_limit(self, workflow_name: str) -> None:
        """Remove rate limit from a workflow.

        Args:
            workflow_name: Name of the workflow

        Returns:
            None

        Example:
            ```python
            await metadata_client.remove_workflow_rate_limit("my_workflow")
            ```
        """
        current_rate_limit = await self.get_workflow_rate_limit(workflow_name=workflow_name)
        if current_rate_limit:
            rate_limit_tag = TagAdapter(
                key=workflow_name, type="RATE_LIMIT", value=current_rate_limit
            )
            await self._tags_api.delete_workflow_tag(name=workflow_name, tag=rate_limit_tag)
