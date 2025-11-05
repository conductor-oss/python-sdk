from __future__ import annotations

from typing import Any, Dict, List, Optional, cast

from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.models.access_key_adapter import AccessKeyAdapter
from conductor.asyncio_client.adapters.models.authorization_request_adapter import (
    AuthorizationRequestAdapter,
)
from conductor.asyncio_client.adapters.models.conductor_user_adapter import (
    ConductorUserAdapter,
)
from conductor.asyncio_client.adapters.models.create_or_update_application_request_adapter import (
    CreateOrUpdateApplicationRequestAdapter,
)
from conductor.asyncio_client.adapters.models.created_access_key_adapter import (
    CreatedAccessKeyAdapter,
)
from conductor.asyncio_client.adapters.models.extended_conductor_application_adapter import (
    ExtendedConductorApplicationAdapter,
)
from conductor.asyncio_client.adapters.models.granted_access_adapter import (
    GrantedAccessAdapter,
)
from conductor.asyncio_client.adapters.models.granted_access_response_adapter import (
    GrantedAccessResponseAdapter,
)
from conductor.asyncio_client.adapters.models.group_adapter import GroupAdapter
from conductor.asyncio_client.adapters.models.subject_ref_adapter import SubjectRefAdapter
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.adapters.models.target_ref_adapter import (
    TargetRefAdapter,
)
from conductor.asyncio_client.adapters.models.upsert_group_request_adapter import (
    UpsertGroupRequestAdapter,
)
from conductor.asyncio_client.adapters.models.upsert_user_request_adapter import (
    UpsertUserRequestAdapter,
)
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient


class OrkesAuthorizationClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        """Initialize the OrkesAuthorizationClient with configuration and API client.

        Args:
            configuration: Configuration object containing server settings and authentication
            api_client: ApiClient instance for making API requests

        Example:
            ```python
            from conductor.asyncio_client.configuration.configuration import Configuration
            from conductor.asyncio_client.adapters import ApiClient

            config = Configuration(server_api_url="http://localhost:8080/api")
            api_client = ApiClient(configuration=config)
            auth_client = OrkesAuthorizationClient(config, api_client)
            ```
        """
        super().__init__(configuration, api_client)

    # User Operations
    @deprecated("create_user is deprecated; use create_user_validated instead")
    @typing_deprecated("create_user is deprecated; use create_user_validated instead")
    async def create_user(
        self, user_id: str, upsert_user_request: UpsertUserRequestAdapter
    ) -> object:
        """Create a new user.

        .. deprecated::
            Use create_user_validated instead for type-safe validated responses.

        Args:
            user_id: Unique identifier for the user
            upsert_user_request: User details including name, roles, and groups

        Returns:
            Raw response object from the API

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.upsert_user_request_adapter import UpsertUserRequestAdapter

            request = UpsertUserRequestAdapter(name="John Doe", roles=["USER"])
            await auth_client.create_user("john.doe@example.com", request)
            ```
        """
        return await self._user_api.upsert_user(id=user_id, upsert_user_request=upsert_user_request)

    async def create_user_validated(
        self, user_id: str, upsert_user_request: UpsertUserRequestAdapter, **kwargs
    ) -> Optional[ConductorUserAdapter]:
        """Create a new user and return a validated ConductorUserAdapter.

        Args:
            user_id: Unique identifier for the user (typically email address)
            upsert_user_request: User details including name, roles, and groups
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ConductorUserAdapter instance containing the created user details, or None if creation failed

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.upsert_user_request_adapter import UpsertUserRequestAdapter

            request = UpsertUserRequestAdapter(
                name="John Doe",
                roles=["USER"],
                groups=["engineering"]
            )
            user = await auth_client.create_user_validated("john.doe@example.com", request)
            print(f"Created user: {user.name}")
            ```
        """
        result = await self._user_api.upsert_user(
            id=user_id, upsert_user_request=upsert_user_request, **kwargs
        )

        result_dict = cast(Dict[str, Any], result)
        result_model = ConductorUserAdapter.from_dict(result_dict)

        return result_model

    @deprecated("update_user is deprecated; use update_user_validated instead")
    @typing_deprecated("update_user is deprecated; use update_user_validated instead")
    async def update_user(
        self, user_id: str, upsert_user_request: UpsertUserRequestAdapter
    ) -> object:
        """Update an existing user.

        .. deprecated::
            Use update_user_validated instead for type-safe validated responses.

        Args:
            user_id: Unique identifier for the user to update
            upsert_user_request: Updated user details

        Returns:
            Raw response object from the API

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.upsert_user_request_adapter import UpsertUserRequestAdapter

            request = UpsertUserRequestAdapter(name="John Smith", roles=["USER", "ADMIN"])
            await auth_client.update_user("john.doe@example.com", request)
            ```
        """
        return await self._user_api.upsert_user(id=user_id, upsert_user_request=upsert_user_request)

    async def update_user_validated(
        self, user_id: str, upsert_user_request: UpsertUserRequestAdapter, **kwargs
    ) -> Optional[ConductorUserAdapter]:
        """Update an existing user and return a validated ConductorUserAdapter.

        Args:
            user_id: Unique identifier for the user to update
            upsert_user_request: Updated user details including name, roles, and groups
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ConductorUserAdapter instance containing the updated user details, or None if update failed

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.upsert_user_request_adapter import UpsertUserRequestAdapter

            request = UpsertUserRequestAdapter(
                name="John Smith",
                roles=["USER", "ADMIN"]
            )
            user = await auth_client.update_user_validated("john.doe@example.com", request)
            print(f"Updated user: {user.name}")
            ```
        """
        result = await self._user_api.upsert_user(
            id=user_id, upsert_user_request=upsert_user_request, **kwargs
        )

        result_dict = cast(Dict[str, Any], result)
        result_model = ConductorUserAdapter.from_dict(result_dict)

        return result_model

    async def get_user(self, user_id: str, **kwargs) -> Optional[ConductorUserAdapter]:
        """Get a user by ID and return a validated ConductorUserAdapter.

        Args:
            user_id: Unique identifier for the user to retrieve
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ConductorUserAdapter instance containing the user details, or None if user not found

        Example:
            ```python
            user = await auth_client.get_user("john.doe@example.com")
            if user:
                print(f"User: {user.name}, Roles: {user.roles}")
            ```
        """
        result = await self._user_api.get_user(id=user_id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = ConductorUserAdapter.from_dict(result_dict)

        return result_model

    async def delete_user(self, user_id: str, **kwargs) -> None:
        """Delete a user by ID.

        Args:
            user_id: Unique identifier for the user to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await auth_client.delete_user("john.doe@example.com")
            ```
        """
        await self._user_api.delete_user(id=user_id, **kwargs)

    async def list_users(self, include_apps: bool = False, **kwargs) -> List[ConductorUserAdapter]:
        """List all users in the system.

        Args:
            include_apps: If True, include application users in the result. Defaults to False
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of ConductorUserAdapter instances representing all users

        Example:
            ```python
            # List only regular users
            users = await auth_client.list_users()
            for user in users:
                print(f"User: {user.name}")

            # Include application users
            all_users = await auth_client.list_users(include_apps=True)
            ```
        """
        return await self._user_api.list_users(apps=include_apps, **kwargs)

    async def get_user_permissions(
        self, user_id: str, **kwargs
    ) -> Optional[GrantedAccessResponseAdapter]:
        """Get permissions granted to a user.

        Args:
            user_id: Unique identifier for the user
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            GrantedAccessResponseAdapter containing all permissions granted to the user, or None if user not found

        Example:
            ```python
            permissions = await auth_client.get_user_permissions("john.doe@example.com")
            if permissions and permissions.granted_access:
                for access in permissions.granted_access:
                    print(f"Access: {access.access} on {access.target.type}:{access.target.id}")
            ```
        """
        result = await self._user_api.get_granted_permissions(user_id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = GrantedAccessResponseAdapter.from_dict(result_dict)

        return result_model

    # Application Operations
    async def create_application(
        self,
        create_or_update_application_request: CreateOrUpdateApplicationRequestAdapter,
        **kwargs,
    ) -> Optional[ExtendedConductorApplicationAdapter]:
        """Create a new application and return a validated ExtendedConductorApplicationAdapter.

        Args:
            create_or_update_application_request: Application details including name and owner
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ExtendedConductorApplicationAdapter instance containing the created application details, or None if creation failed

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.create_or_update_application_request_adapter import CreateOrUpdateApplicationRequestAdapter

            request = CreateOrUpdateApplicationRequestAdapter(
                name="My Application",
                owner="engineering-team"
            )
            app = await auth_client.create_application(request)
            print(f"Created application: {app.name} with ID: {app.id}")
            ```
        """
        result = await self._application_api.create_application(
            create_or_update_application_request=create_or_update_application_request, **kwargs
        )

        result_dict = cast(Dict[str, Any], result)
        result_model = ExtendedConductorApplicationAdapter.from_dict(result_dict)

        return result_model

    async def update_application(
        self,
        application_id: str,
        create_or_update_application_request: CreateOrUpdateApplicationRequestAdapter,
        **kwargs,
    ) -> Optional[ExtendedConductorApplicationAdapter]:
        """Update an existing application and return a validated ExtendedConductorApplicationAdapter.

        Args:
            application_id: Unique identifier for the application to update
            create_or_update_application_request: Updated application details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ExtendedConductorApplicationAdapter instance containing the updated application details, or None if update failed

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.create_or_update_application_request_adapter import CreateOrUpdateApplicationRequestAdapter

            request = CreateOrUpdateApplicationRequestAdapter(
                name="Updated Application Name",
                owner="new-owner-team"
            )
            app = await auth_client.update_application("app-123", request)
            print(f"Updated application: {app.name}")
            ```
        """
        result = await self._application_api.update_application(
            id=application_id,
            create_or_update_application_request=create_or_update_application_request,
            **kwargs,
        )

        result_dict = cast(Dict[str, Any], result)
        result_model = ExtendedConductorApplicationAdapter.from_dict(result_dict)

        return result_model

    async def get_application(
        self, application_id: str, **kwargs
    ) -> Optional[ExtendedConductorApplicationAdapter]:
        """Get an application by ID and return a validated ExtendedConductorApplicationAdapter.

        Args:
            application_id: Unique identifier for the application to retrieve
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ExtendedConductorApplicationAdapter instance containing the application details, or None if not found

        Example:
            ```python
            app = await auth_client.get_application("app-123")
            if app:
                print(f"Application: {app.name}, Owner: {app.owner}")
            ```
        """
        result = await self._application_api.get_application(id=application_id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = ExtendedConductorApplicationAdapter.from_dict(result_dict)

        return result_model

    async def delete_application(self, application_id: str, **kwargs) -> None:
        """Delete an application by ID.

        Args:
            application_id: Unique identifier for the application to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await auth_client.delete_application("app-123")
            ```
        """
        await self._application_api.delete_application(id=application_id, **kwargs)

    async def list_applications(self, **kwargs) -> List[ExtendedConductorApplicationAdapter]:
        """List all applications in the system.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of ExtendedConductorApplicationAdapter instances representing all applications

        Example:
            ```python
            apps = await auth_client.list_applications()
            for app in apps:
                print(f"Application: {app.name}, ID: {app.id}")
            ```
        """
        return await self._application_api.list_applications(**kwargs)

    # Group Operations
    @deprecated("create_group is deprecated; use create_group_validated instead")
    @typing_deprecated("create_group is deprecated; use create_group_validated instead")
    async def create_group(
        self, group_id: str, upsert_group_request: UpsertGroupRequestAdapter
    ) -> object:
        """Create a new group.

        .. deprecated::
            Use create_group_validated instead for type-safe validated responses.

        Args:
            group_id: Unique identifier for the group
            upsert_group_request: Group details including description and roles

        Returns:
            Raw response object from the API

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.upsert_group_request_adapter import UpsertGroupRequestAdapter

            request = UpsertGroupRequestAdapter(description="Engineering team", roles=["WORKER"])
            await auth_client.create_group("engineering", request)
            ```
        """
        return await self._group_api.upsert_group(
            id=group_id, upsert_group_request=upsert_group_request
        )

    async def create_group_validated(
        self, group_id: str, upsert_group_request: UpsertGroupRequestAdapter, **kwargs
    ) -> Optional[GroupAdapter]:
        """Create a new group and return a validated GroupAdapter.

        Args:
            group_id: Unique identifier for the group
            upsert_group_request: Group details including description and roles
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            GroupAdapter instance containing the created group details, or None if creation failed

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.upsert_group_request_adapter import UpsertGroupRequestAdapter

            request = UpsertGroupRequestAdapter(
                description="Engineering team",
                roles=["WORKER"]
            )
            group = await auth_client.create_group_validated("engineering", request)
            print(f"Created group: {group.id}")
            ```
        """
        result = await self._group_api.upsert_group(
            id=group_id, upsert_group_request=upsert_group_request, **kwargs
        )

        result_dict = cast(Dict[str, Any], result)
        result_model = GroupAdapter.from_dict(result_dict)

        return result_model

    async def update_group(
        self, group_id: str, upsert_group_request: UpsertGroupRequestAdapter, **kwargs
    ) -> Optional[GroupAdapter]:
        """Update an existing group and return a validated GroupAdapter.

        Args:
            group_id: Unique identifier for the group to update
            upsert_group_request: Updated group details
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            GroupAdapter instance containing the updated group details, or None if update failed

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.upsert_group_request_adapter import UpsertGroupRequestAdapter

            request = UpsertGroupRequestAdapter(
                description="Updated engineering team",
                roles=["WORKER", "ADMIN"]
            )
            group = await auth_client.update_group("engineering", request)
            print(f"Updated group: {group.id}")
            ```
        """
        result = await self._group_api.upsert_group(
            id=group_id, upsert_group_request=upsert_group_request, **kwargs
        )

        result_dict = cast(Dict[str, Any], result)
        result_model = GroupAdapter.from_dict(result_dict)

        return result_model

    async def get_group(self, group_id: str, **kwargs) -> Optional[GroupAdapter]:
        """Get a group by ID and return a validated GroupAdapter.

        Args:
            group_id: Unique identifier for the group to retrieve
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            GroupAdapter instance containing the group details, or None if not found

        Example:
            ```python
            group = await auth_client.get_group("engineering")
            if group:
                print(f"Group: {group.id}, Description: {group.description}")
            ```
        """
        result = await self._group_api.get_group(id=group_id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = GroupAdapter.from_dict(result_dict)

        return result_model

    async def delete_group(self, group_id: str, **kwargs) -> None:
        """Delete a group by ID.

        Args:
            group_id: Unique identifier for the group to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await auth_client.delete_group("engineering")
            ```
        """
        await self._group_api.delete_group(id=group_id, **kwargs)

    async def list_groups(self, **kwargs) -> List[GroupAdapter]:
        """List all groups in the system.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of GroupAdapter instances representing all groups

        Example:
            ```python
            groups = await auth_client.list_groups()
            for group in groups:
                print(f"Group: {group.id}, Description: {group.description}")
            ```
        """
        return await self._group_api.list_groups(**kwargs)

    # Group User Management Operations
    @deprecated("add_user_to_group is deprecated; use add_user_to_group_validated instead")
    @typing_deprecated("add_user_to_group is deprecated; use add_user_to_group_validated instead")
    async def add_user_to_group(self, group_id: str, user_id: str) -> object:
        """Add a user to a group.

        .. deprecated::
            Use add_user_to_group_validated instead for type-safe validated responses.

        Args:
            group_id: Unique identifier for the group
            user_id: Unique identifier for the user to add

        Returns:
            Raw response object from the API

        Example:
            ```python
            await auth_client.add_user_to_group("engineering", "john.doe@example.com")
            ```
        """
        return await self._group_api.add_user_to_group(group_id=group_id, user_id=user_id)

    async def add_user_to_group_validated(self, group_id: str, user_id: str, **kwargs) -> None:
        """Add a user to a group.

        Args:
            group_id: Unique identifier for the group
            user_id: Unique identifier for the user to add
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await auth_client.add_user_to_group_validated("engineering", "john.doe@example.com")
            ```
        """
        await self._group_api.add_user_to_group(group_id=group_id, user_id=user_id, **kwargs)

    @deprecated(
        "remove_user_from_group is deprecated; use remove_user_from_group_validated instead"
    )
    @typing_deprecated(
        "remove_user_from_group is deprecated; use remove_user_from_group_validated instead"
    )
    async def remove_user_from_group(self, group_id: str, user_id: str) -> object:
        """Remove a user from a group.

        .. deprecated::
            Use remove_user_from_group_validated instead for type-safe validated responses.

        Args:
            group_id: Unique identifier for the group
            user_id: Unique identifier for the user to remove

        Returns:
            Raw response object from the API

        Example:
            ```python
            await auth_client.remove_user_from_group("engineering", "john.doe@example.com")
            ```
        """
        return await self._group_api.remove_user_from_group(group_id=group_id, user_id=user_id)

    async def remove_user_from_group_validated(self, group_id: str, user_id: str, **kwargs) -> None:
        """Remove a user from a group.

        Args:
            group_id: Unique identifier for the group
            user_id: Unique identifier for the user to remove
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await auth_client.remove_user_from_group_validated("engineering", "john.doe@example.com")
            ```
        """
        await self._group_api.remove_user_from_group(group_id=group_id, user_id=user_id, **kwargs)

    @deprecated("add_users_to_group is deprecated; use add_users_to_group_validated instead")
    @typing_deprecated("add_users_to_group is deprecated; use add_users_to_group_validated instead")
    async def add_users_to_group(self, group_id: str, user_ids: List[str]) -> None:
        """Add multiple users to a group.

        .. deprecated::
            Use add_users_to_group_validated instead for type-safe validated responses.

        Args:
            group_id: Unique identifier for the group
            user_ids: List of user identifiers to add to the group

        Returns:
            None

        Example:
            ```python
            users = ["john.doe@example.com", "jane.smith@example.com"]
            await auth_client.add_users_to_group("engineering", users)
            ```
        """
        return await self._group_api.add_users_to_group(group_id=group_id, request_body=user_ids)

    async def add_users_to_group_validated(
        self, group_id: str, user_ids: List[str], **kwargs
    ) -> None:
        """Add multiple users to a group.

        Args:
            group_id: Unique identifier for the group
            user_ids: List of user identifiers to add to the group
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            users = ["john.doe@example.com", "jane.smith@example.com"]
            await auth_client.add_users_to_group_validated("engineering", users)
            ```
        """
        await self._group_api.add_users_to_group(group_id=group_id, request_body=user_ids, **kwargs)

    async def remove_users_from_group(self, group_id: str, user_ids: List[str], **kwargs) -> None:
        """Remove multiple users from a group.

        Args:
            group_id: Unique identifier for the group
            user_ids: List of user identifiers to remove from the group
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            users = ["john.doe@example.com", "jane.smith@example.com"]
            await auth_client.remove_users_from_group("engineering", users)
            ```
        """
        return await self._group_api.remove_users_from_group(
            group_id=group_id, request_body=user_ids, **kwargs
        )

    @deprecated("get_users_in_group is deprecated; use get_users_in_group_validated instead")
    @typing_deprecated("get_users_in_group is deprecated; use get_users_in_group_validated instead")
    async def get_users_in_group(self, group_id: str) -> object:
        """Get all users in a group.

        .. deprecated::
            Use get_users_in_group_validated instead for type-safe validated responses.

        Args:
            group_id: Unique identifier for the group

        Returns:
            Raw response object from the API containing list of users

        Example:
            ```python
            users = await auth_client.get_users_in_group("engineering")
            ```
        """
        return await self._group_api.get_users_in_group(id=group_id)

    async def get_users_in_group_validated(
        self, group_id: str, **kwargs
    ) -> List[Optional[ConductorUserAdapter]]:
        """Get all users in a group and return a list of validated ConductorUserAdapters.

        Args:
            group_id: Unique identifier for the group
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of ConductorUserAdapter instances representing users in the group

        Example:
            ```python
            users = await auth_client.get_users_in_group_validated("engineering")
            for user in users:
                if user:
                    print(f"User: {user.name}")
            ```
        """
        result = await self._group_api.get_users_in_group(id=group_id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = [ConductorUserAdapter.from_dict(_item) for _item in result_dict]

        return result_model

    # Permission Operations (Only available operations)
    @deprecated("grant_permissions is deprecated; use grant_permissions_validated instead")
    @typing_deprecated("grant_permissions is deprecated; use grant_permissions_validated instead")
    async def grant_permissions(self, authorization_request: AuthorizationRequestAdapter) -> object:
        """Grant permissions to users or groups.

        .. deprecated::
            Use grant_permissions_validated instead for type-safe validated responses.

        Args:
            authorization_request: Authorization details including subject, target, and access level

        Returns:
            Raw response object from the API

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.authorization_request_adapter import AuthorizationRequestAdapter
            from conductor.asyncio_client.adapters.models.subject_ref_adapter import SubjectRefAdapter
            from conductor.asyncio_client.adapters.models.target_ref_adapter import TargetRefAdapter

            request = AuthorizationRequestAdapter(
                subject=SubjectRefAdapter(type="USER", id="john.doe@example.com"),
                target=TargetRefAdapter(type="WORKFLOW_DEF", id="my_workflow"),
                access=["READ", "EXECUTE"]
            )
            await auth_client.grant_permissions(request)
            ```
        """
        return await self._authorization_api.grant_permissions(
            authorization_request=authorization_request
        )

    async def grant_permissions_validated(
        self, authorization_request: AuthorizationRequestAdapter, **kwargs
    ) -> None:
        """Grant permissions to users or groups.

        Args:
            authorization_request: Authorization details including subject, target, and access level
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.authorization_request_adapter import AuthorizationRequestAdapter
            from conductor.asyncio_client.adapters.models.subject_ref_adapter import SubjectRefAdapter
            from conductor.asyncio_client.adapters.models.target_ref_adapter import TargetRefAdapter

            request = AuthorizationRequestAdapter(
                subject=SubjectRefAdapter(type="USER", id="john.doe@example.com"),
                target=TargetRefAdapter(type="WORKFLOW_DEF", id="my_workflow"),
                access=["READ", "EXECUTE"]
            )
            await auth_client.grant_permissions_validated(request)
            ```
        """
        await self._authorization_api.grant_permissions(
            authorization_request=authorization_request, **kwargs
        )

    @deprecated("remove_permissions is deprecated; use remove_permissions_validated instead")
    @typing_deprecated("remove_permissions is deprecated; use remove_permissions_validated instead")
    async def remove_permissions(
        self, authorization_request: AuthorizationRequestAdapter
    ) -> object:
        """Remove permissions from users or groups.

        .. deprecated::
            Use remove_permissions_validated instead for type-safe validated responses.

        Args:
            authorization_request: Authorization details including subject, target, and access level to remove

        Returns:
            Raw response object from the API

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.authorization_request_adapter import AuthorizationRequestAdapter
            from conductor.asyncio_client.adapters.models.subject_ref_adapter import SubjectRefAdapter
            from conductor.asyncio_client.adapters.models.target_ref_adapter import TargetRefAdapter

            request = AuthorizationRequestAdapter(
                subject=SubjectRefAdapter(type="USER", id="john.doe@example.com"),
                target=TargetRefAdapter(type="WORKFLOW_DEF", id="my_workflow"),
                access=["EXECUTE"]
            )
            await auth_client.remove_permissions(request)
            ```
        """
        return await self._authorization_api.remove_permissions(
            authorization_request=authorization_request
        )

    async def remove_permissions_validated(
        self, authorization_request: AuthorizationRequestAdapter, **kwargs
    ) -> None:
        """Remove permissions from users or groups.

        Args:
            authorization_request: Authorization details including subject, target, and access level to remove
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.authorization_request_adapter import AuthorizationRequestAdapter
            from conductor.asyncio_client.adapters.models.subject_ref_adapter import SubjectRefAdapter
            from conductor.asyncio_client.adapters.models.target_ref_adapter import TargetRefAdapter

            request = AuthorizationRequestAdapter(
                subject=SubjectRefAdapter(type="USER", id="john.doe@example.com"),
                target=TargetRefAdapter(type="WORKFLOW_DEF", id="my_workflow"),
                access=["EXECUTE"]
            )
            await auth_client.remove_permissions_validated(request)
            ```
        """
        await self._authorization_api.remove_permissions(
            authorization_request=authorization_request, **kwargs
        )

    @deprecated("get_permissions is deprecated; use get_permissions_validated instead")
    @typing_deprecated("get_permissions is deprecated; use get_permissions_validated instead")
    async def get_permissions(self, entity_type: str, entity_id: str) -> object:
        """Get permissions for a specific entity (user, group, or application).

        .. deprecated::
            Use get_permissions_validated instead for type-safe validated responses.

        Args:
            entity_type: Type of the entity (USER, GROUP, or APPLICATION)
            entity_id: Unique identifier for the entity

        Returns:
            Raw response object from the API containing permissions

        Example:
            ```python
            permissions = await auth_client.get_permissions("USER", "john.doe@example.com")
            ```
        """
        return await self._authorization_api.get_permissions(type=entity_type, id=entity_id)

    async def get_permissions_validated(
        self, target: TargetRefAdapter, **kwargs
    ) -> Dict[str, List[SubjectRefAdapter]]:
        """Get permissions for a specific entity (user, group, or application).

        Args:
            target: Target entity reference containing type and ID
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping access types to lists of SubjectRefAdapter instances

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.target_ref_adapter import TargetRefAdapter

            target = TargetRefAdapter(type="WORKFLOW_DEF", id="my_workflow")
            permissions = await auth_client.get_permissions_validated(target)
            for access_type, subjects in permissions.items():
                print(f"Access {access_type}: {[s.id for s in subjects]}")
            ```
        """
        result = await self._authorization_api.get_permissions(
            type=target.type, id=target.id, **kwargs
        )

        permissions = {}
        for access_type, subjects in result.items():
            subject_list = [SubjectRefAdapter(id=sub["id"], type=sub["type"]) for sub in subjects]
            permissions[access_type] = subject_list

        return permissions

    async def get_group_permissions(self, group_id: str, **kwargs) -> GrantedAccessResponseAdapter:
        """Get permissions granted to a group.

        Args:
            group_id: Unique identifier for the group
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            GrantedAccessResponseAdapter containing all permissions granted to the group

        Example:
            ```python
            permissions = await auth_client.get_group_permissions("engineering")
            if permissions.granted_access:
                for access in permissions.granted_access:
                    print(f"Access: {access.access} on {access.target.type}:{access.target.id}")
            ```
        """
        return await self._group_api.get_granted_permissions1(group_id=group_id, **kwargs)

    # Convenience Methods
    async def upsert_user(
        self, user_id: str, upsert_user_request: UpsertUserRequestAdapter, **kwargs
    ) -> Optional[ConductorUserAdapter]:
        """Create or update a user (upsert operation).

        This is an alias for create_user_validated/update_user_validated.

        Args:
            user_id: Unique identifier for the user
            upsert_user_request: User details to create or update
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ConductorUserAdapter instance containing the user details, or None if operation failed

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.upsert_user_request_adapter import UpsertUserRequestAdapter

            request = UpsertUserRequestAdapter(name="John Doe", roles=["USER"])
            user = await auth_client.upsert_user("john.doe@example.com", request)
            ```
        """
        result = await self.create_user_validated(user_id, upsert_user_request, **kwargs)
        return result

    async def upsert_group(
        self, group_id: str, upsert_group_request: UpsertGroupRequestAdapter, **kwargs
    ) -> Optional[GroupAdapter]:
        """Create or update a group (upsert operation).

        This is an alias for create_group_validated/update_group.

        Args:
            group_id: Unique identifier for the group
            upsert_group_request: Group details to create or update
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            GroupAdapter instance containing the group details, or None if operation failed

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.upsert_group_request_adapter import UpsertGroupRequestAdapter

            request = UpsertGroupRequestAdapter(description="Engineering team", roles=["WORKER"])
            group = await auth_client.upsert_group("engineering", request)
            ```
        """
        result = await self.create_group_validated(group_id, upsert_group_request, **kwargs)
        return result

    async def set_application_tags(
        self, tags: List[TagAdapter], application_id: str, **kwargs
    ) -> None:
        """Set tags for an application.

        Args:
            tags: List of TagAdapter instances to set on the application
            application_id: Unique identifier for the application
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [TagAdapter(type="METADATA", key="environment", value="production")]
            await auth_client.set_application_tags(tags, "app-123")
            ```
        """
        await self._application_api.put_tag_for_application(id=application_id, tag=tags, **kwargs)

    async def get_application_tags(self, application_id: str, **kwargs) -> List[TagAdapter]:
        """Get tags for an application.

        Args:
            application_id: Unique identifier for the application
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of TagAdapter instances representing tags on the application

        Example:
            ```python
            tags = await auth_client.get_application_tags("app-123")
            for tag in tags:
                print(f"Tag: {tag.key}={tag.value}")
            ```
        """
        return await self._application_api.get_tags_for_application(id=application_id, **kwargs)

    async def delete_application_tags(
        self, tags: List[TagAdapter], application_id: str, **kwargs
    ) -> None:
        """Delete tags from an application.

        Args:
            tags: List of TagAdapter instances to delete from the application
            application_id: Unique identifier for the application
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [TagAdapter(type="METADATA", key="environment", value="production")]
            await auth_client.delete_application_tags(tags, "app-123")
            ```
        """
        await self._application_api.delete_tag_for_application(
            id=application_id, tag=tags, **kwargs
        )

    @deprecated("create_access_key is deprecated; use create_access_key_validated instead")
    @typing_deprecated("create_access_key is deprecated; use create_access_key_validated instead")
    async def create_access_key(self, application_id: str) -> object:
        """Create an access key for an application.

        .. deprecated::
            Use create_access_key_validated instead for type-safe validated responses.

        Args:
            application_id: Unique identifier for the application

        Returns:
            Raw response object from the API containing the created access key

        Example:
            ```python
            key = await auth_client.create_access_key("app-123")
            ```
        """
        key_obj = await self._application_api.create_access_key(application_id)
        return key_obj

    async def create_access_key_validated(
        self, application_id: str, **kwargs
    ) -> CreatedAccessKeyAdapter:
        """Create an access key for an application.

        Args:
            application_id: Unique identifier for the application
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            CreatedAccessKeyAdapter instance containing the access key details including the secret

        Example:
            ```python
            key = await auth_client.create_access_key_validated("app-123")
            print(f"Key ID: {key.id}, Secret: {key.secret}")
            # Note: The secret is only returned once during creation
            ```
        """
        result = await self._application_api.create_access_key(id=application_id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = CreatedAccessKeyAdapter.from_dict(result_dict)

        return result_model

    @deprecated("get_access_keys is deprecated; use get_access_keys_validated instead")
    @typing_deprecated("get_access_keys is deprecated; use get_access_keys_validated instead")
    async def get_access_keys(self, application_id: str) -> object:
        """Get access keys for an application.

        .. deprecated::
            Use get_access_keys_validated instead for type-safe validated responses.

        Args:
            application_id: Unique identifier for the application

        Returns:
            Raw response object from the API containing list of access keys

        Example:
            ```python
            keys = await auth_client.get_access_keys("app-123")
            ```
        """
        access_keys_obj = await self._application_api.get_access_keys(application_id)
        return access_keys_obj

    async def get_access_keys_validated(
        self, application_id: str, **kwargs
    ) -> List[AccessKeyAdapter]:
        """Get access keys for an application.

        Args:
            application_id: Unique identifier for the application
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of AccessKeyAdapter instances representing all access keys for the application

        Example:
            ```python
            keys = await auth_client.get_access_keys_validated("app-123")
            for key in keys:
                print(f"Key ID: {key.id}, Active: {key.enabled}")
            ```
        """
        result = await self._application_api.get_access_keys(application_id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = [AccessKeyAdapter.from_dict(_item) for _item in result_dict]

        return result_model

    @deprecated(
        "toggle_access_key_status is deprecated; use toggle_access_key_status_validated instead"
    )
    @typing_deprecated(
        "toggle_access_key_status is deprecated; use toggle_access_key_status_validated instead"
    )
    async def toggle_access_key_status(self, application_id: str, key_id: str) -> object:
        """Toggle the status (active/inactive) of an access key.

        .. deprecated::
            Use toggle_access_key_status_validated instead for type-safe validated responses.

        Args:
            application_id: Unique identifier for the application
            key_id: Unique identifier for the access key

        Returns:
            Raw response object from the API

        Example:
            ```python
            await auth_client.toggle_access_key_status("app-123", "key-456")
            ```
        """
        key_obj = await self._application_api.toggle_access_key_status(application_id, key_id)
        return key_obj

    async def toggle_access_key_status_validated(
        self, application_id: str, key_id: str, **kwargs
    ) -> AccessKeyAdapter:
        """Toggle the status (active/inactive) of an access key.

        Args:
            application_id: Unique identifier for the application
            key_id: Unique identifier for the access key
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            AccessKeyAdapter instance with the updated status

        Example:
            ```python
            key = await auth_client.toggle_access_key_status_validated("app-123", "key-456")
            print(f"Key is now: {'enabled' if key.enabled else 'disabled'}")
            ```
        """
        result = await self._application_api.toggle_access_key_status(
            application_id=application_id, key_id=key_id, **kwargs
        )

        result_dict = cast(Dict[str, Any], result)
        result_model = AccessKeyAdapter.from_dict(result_dict)

        return result_model

    async def delete_access_key(self, application_id: str, key_id: str, **kwargs) -> None:
        """Delete an access key from an application.

        Args:
            application_id: Unique identifier for the application
            key_id: Unique identifier for the access key to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await auth_client.delete_access_key("app-123", "key-456")
            ```
        """
        await self._application_api.delete_access_key(
            application_id=application_id, key_id=key_id, **kwargs
        )

    async def add_role_to_application_user(self, application_id: str, role: str, **kwargs) -> None:
        """Add a role to an application user.

        Args:
            application_id: Unique identifier for the application
            role: Role name to add (e.g., "WORKER", "ADMIN")
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await auth_client.add_role_to_application_user("app-123", "WORKER")
            ```
        """
        await self._application_api.add_role_to_application_user(
            application_id=application_id, role=role, **kwargs
        )

    async def remove_role_from_application_user(
        self, application_id: str, role: str, **kwargs
    ) -> None:
        """Remove a role from an application user.

        Args:
            application_id: Unique identifier for the application
            role: Role name to remove (e.g., "WORKER", "ADMIN")
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await auth_client.remove_role_from_application_user("app-123", "WORKER")
            ```
        """
        await self._application_api.remove_role_from_application_user(
            application_id=application_id, role=role, **kwargs
        )

    async def get_granted_permissions_for_group(
        self, group_id: str, **kwargs
    ) -> List[GrantedAccessAdapter]:
        """Get granted permissions for a group in a simplified format.

        Args:
            group_id: Unique identifier for the group
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of GrantedAccessAdapter instances containing target and access information

        Example:
            ```python
            permissions = await auth_client.get_granted_permissions_for_group("engineering")
            for perm in permissions:
                print(f"Access {perm.access} on {perm.target.type}:{perm.target.id}")
            ```
        """
        granted_access_obj = await self.get_group_permissions(group_id=group_id, **kwargs)

        if not granted_access_obj.granted_access:
            return []

        granted_permissions = []
        for ga in granted_access_obj.granted_access:
            if not ga.target:
                continue

            target = TargetRefAdapter(type=ga.target.type, id=ga.target.id)
            access = ga.access
            granted_permissions.append(GrantedAccessAdapter(target=target, access=access))

        return granted_permissions

    async def get_granted_permissions_for_user(
        self, user_id: str, **kwargs
    ) -> List[GrantedAccessAdapter]:
        """Get granted permissions for a user in a simplified format.

        Args:
            user_id: Unique identifier for the user
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of GrantedAccessAdapter instances containing target and access information

        Example:
            ```python
            permissions = await auth_client.get_granted_permissions_for_user("john.doe@example.com")
            for perm in permissions:
                print(f"User has {perm.access} access to {perm.target.type}:{perm.target.id}")
            ```
        """
        granted_access_obj = await self.get_user_permissions(user_id=user_id, **kwargs)

        if granted_access_obj is None or granted_access_obj.granted_access is None:
            return []

        granted_permissions = []
        for ga in granted_access_obj.granted_access:
            if ga.target is None:
                continue

            target = TargetRefAdapter(type=ga.target.type, id=ga.target.id)
            access = ga.access
            granted_permissions.append(GrantedAccessAdapter(target=target, access=access))

        return granted_permissions

    async def get_app_by_access_key_id(
        self, access_key_id: str, **kwargs
    ) -> Optional[ExtendedConductorApplicationAdapter]:
        """Get an application by its access key ID.

        Args:
            access_key_id: Unique identifier for the access key
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ExtendedConductorApplicationAdapter instance for the application, or None if not found

        Example:
            ```python
            app = await auth_client.get_app_by_access_key_id("key-123")
            if app:
                print(f"Application: {app.name}, Owner: {app.owner}")
            ```
        """
        result = await self._application_api.get_app_by_access_key_id(
            access_key_id=access_key_id, **kwargs
        )

        result_dict = cast(Dict[str, Any], result)
        result_model = ExtendedConductorApplicationAdapter.from_dict(result_dict)

        return result_model

    async def check_permissions(
        self, user_id: str, type: str, id: str, **kwargs
    ) -> Dict[str, bool]:
        """Check what permissions a user has on a specific resource.

        Args:
            user_id: Unique identifier for the user
            type: Type of resource (e.g., "WORKFLOW_DEF", "TASK_DEF")
            id: Unique identifier for the resource
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping permission types (READ, EXECUTE, UPDATE, DELETE) to boolean values

        Example:
            ```python
            permissions = await auth_client.check_permissions(
                "john.doe@example.com",
                "WORKFLOW_DEF",
                "my_workflow"
            )
            if permissions.get("EXECUTE"):
                print("User can execute this workflow")
            if permissions.get("UPDATE"):
                print("User can update this workflow")
            ```
        """
        result = await self._user_api.check_permissions(user_id=user_id, type=type, id=id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = {k: v for k, v in result_dict.items() if isinstance(v, bool)}

        return result_model
