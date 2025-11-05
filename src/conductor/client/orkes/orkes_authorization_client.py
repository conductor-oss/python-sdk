from __future__ import annotations

from typing import Any, Dict, List, Optional, cast

from conductor.client.authorization_client import AuthorizationClient
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import ExtendedConductorApplication
from conductor.client.http.models.authorization_request import AuthorizationRequest
from conductor.client.http.models.conductor_application import ConductorApplication
from conductor.client.http.models.conductor_user import ConductorUser
from conductor.client.http.models.create_or_update_application_request import (
    CreateOrUpdateApplicationRequest,
)
from conductor.client.http.models.group import Group
from conductor.client.http.models.subject_ref import SubjectRef
from conductor.client.http.models.target_ref import TargetRef
from conductor.client.http.models.upsert_group_request import UpsertGroupRequest
from conductor.client.http.models.upsert_user_request import UpsertUserRequest
from conductor.client.orkes.models.access_key import AccessKey
from conductor.client.orkes.models.access_type import AccessType
from conductor.client.orkes.models.created_access_key import CreatedAccessKey
from conductor.client.orkes.models.granted_permission import GrantedPermission
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.orkes.orkes_base_client import OrkesBaseClient


class OrkesAuthorizationClient(OrkesBaseClient, AuthorizationClient):
    def __init__(self, configuration: Configuration):
        """Initialize the OrkesAuthorizationClient with configuration.

        Args:
            configuration: Configuration object containing server settings and authentication

        Example:
            ```python
            from conductor.client.configuration.configuration import Configuration

            config = Configuration(server_api_url="http://localhost:8080/api")
            auth_client = OrkesAuthorizationClient(config)
            ```
        """
        super().__init__(configuration)

    # Applications
    def create_application(
        self, create_or_update_application_request: CreateOrUpdateApplicationRequest, **kwargs
    ) -> ConductorApplication:
        """Create a new application.

        Args:
            create_or_update_application_request: Application details including name and owner
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ConductorApplication instance containing the created application details

        Example:
            ```python
            from conductor.client.http.models.create_or_update_application_request import CreateOrUpdateApplicationRequest

            request = CreateOrUpdateApplicationRequest(
                name="My Application",
                owner="engineering-team"
            )
            app = auth_client.create_application(request)
            print(f"Created application: {app.name} with ID: {app.id}")
            ```
        """
        app_obj = self._application_api.create_application(
            body=create_or_update_application_request, **kwargs
        )
        return self.api_client.deserialize_class(app_obj, "ConductorApplication")

    def get_application(self, application_id: str, **kwargs) -> ConductorApplication:
        """Get an application by ID.

        Args:
            application_id: Unique identifier for the application
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ConductorApplication instance containing the application details

        Example:
            ```python
            app = auth_client.get_application("app-123")
            print(f"Application: {app.name}, Owner: {app.owner}")
            ```
        """
        app_obj = self._application_api.get_application(id=application_id, **kwargs)
        return self.api_client.deserialize_class(app_obj, "ConductorApplication")

    def get_app_by_access_key_id(self, access_key_id: str, **kwargs) -> ConductorApplication:
        """Get an application by its access key ID.

        Args:
            access_key_id: Unique identifier for the access key
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ConductorApplication instance for the application

        Example:
            ```python
            app = auth_client.get_app_by_access_key_id("key-123")
            print(f"Application: {app.name}, Owner: {app.owner}")
            ```
        """
        app_obj = self._application_api.get_app_by_access_key_id(
            access_key_id=access_key_id, **kwargs
        )
        return self.api_client.deserialize_class(app_obj, "ConductorApplication")

    def list_applications(self, **kwargs) -> List[ExtendedConductorApplication]:
        """List all applications in the system.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of ExtendedConductorApplication instances representing all applications

        Example:
            ```python
            apps = auth_client.list_applications()
            for app in apps:
                print(f"Application: {app.name}, ID: {app.id}")
            ```
        """
        return self._application_api.list_applications(**kwargs)

    def update_application(
        self,
        create_or_update_application_request: CreateOrUpdateApplicationRequest,
        application_id: str,
        **kwargs,
    ) -> ConductorApplication:
        """Update an existing application.

        Args:
            create_or_update_application_request: Updated application details
            application_id: Unique identifier for the application to update
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ConductorApplication instance containing the updated application details

        Example:
            ```python
            from conductor.client.http.models.create_or_update_application_request import CreateOrUpdateApplicationRequest

            request = CreateOrUpdateApplicationRequest(
                name="Updated Application Name",
                owner="new-owner-team"
            )
            app = auth_client.update_application(request, "app-123")
            print(f"Updated application: {app.name}")
            ```
        """
        app_obj = self._application_api.update_application(
            body=create_or_update_application_request, id=application_id, **kwargs
        )
        return self.api_client.deserialize_class(app_obj, "ConductorApplication")

    def delete_application(self, application_id: str, **kwargs) -> None:
        """Delete an application by ID.

        Args:
            application_id: Unique identifier for the application to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            auth_client.delete_application("app-123")
            ```
        """
        self._application_api.delete_application(id=application_id, **kwargs)

    def add_role_to_application_user(self, application_id: str, role: str, **kwargs) -> None:
        """Add a role to an application user.

        Args:
            application_id: Unique identifier for the application
            role: Role name to add (e.g., "ADMIN", "USER")
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            auth_client.add_role_to_application_user("app-123", "ADMIN")
            ```
        """
        self._application_api.add_role_to_application_user(
            application_id=application_id, role=role, **kwargs
        )

    def remove_role_from_application_user(self, application_id: str, role: str, **kwargs) -> None:
        """Remove a role from an application user.

        Args:
            application_id: Unique identifier for the application
            role: Role name to remove
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            auth_client.remove_role_from_application_user("app-123", "ADMIN")
            ```
        """
        self._application_api.remove_role_from_application_user(
            application_id=application_id, role=role, **kwargs
        )

    def set_application_tags(self, tags: List[MetadataTag], application_id: str, **kwargs) -> None:
        """Set tags for an application, replacing any existing tags.

        Args:
            tags: List of tags to set for the application
            application_id: Unique identifier for the application
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.orkes.models.metadata_tag import MetadataTag

            tags = [
                MetadataTag(key="environment", value="production"),
                MetadataTag(key="team", value="platform")
            ]
            auth_client.set_application_tags(tags, "app-123")
            ```
        """
        self._application_api.put_tag_for_application(tag=tags, id=application_id, **kwargs)

    def get_application_tags(self, application_id: str, **kwargs) -> List[MetadataTag]:
        """Get all tags associated with an application.

        Args:
            application_id: Unique identifier for the application
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of MetadataTag instances

        Example:
            ```python
            tags = auth_client.get_application_tags("app-123")
            for tag in tags:
                print(f"Tag: {tag.key}={tag.value}")
            ```
        """
        return self._application_api.get_tags_for_application(
            application_id=application_id, **kwargs
        )

    def delete_application_tags(
        self, tags: List[MetadataTag], application_id: str, **kwargs
    ) -> None:
        """Delete specific tags from an application.

        Args:
            tags: List of tags to delete
            application_id: Unique identifier for the application
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.orkes.models.metadata_tag import MetadataTag

            tags_to_delete = [MetadataTag(key="environment", value="staging")]
            auth_client.delete_application_tags(tags_to_delete, "app-123")
            ```
        """
        self._application_api.delete_tag_for_application(tag=tags, id=application_id, **kwargs)

    def create_access_key(self, application_id: str, **kwargs) -> CreatedAccessKey:
        """Create a new access key for an application.

        Args:
            application_id: Unique identifier for the application
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            CreatedAccessKey instance with the new key details (includes secret)

        Example:
            ```python
            key = auth_client.create_access_key("app-123")
            print(f"Access Key ID: {key.id}")
            print(f"Secret: {key.secret}")  # Store securely, won't be shown again
            ```
        """
        key_obj = self._application_api.create_access_key(id=application_id, **kwargs)

        key_obj_dict = cast(Dict[str, Any], key_obj)
        result_model = CreatedAccessKey.from_dict(key_obj_dict)

        return result_model

    def get_access_keys(self, application_id: str, **kwargs) -> List[AccessKey]:
        """Get all access keys for an application.

        Args:
            application_id: Unique identifier for the application
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of AccessKey instances (secrets are not included)

        Example:
            ```python
            keys = auth_client.get_access_keys("app-123")
            for key in keys:
                print(f"Key ID: {key.id}, Status: {key.status}")
            ```
        """
        access_keys_obj = self._application_api.get_access_keys(id=application_id, **kwargs)

        access_keys_dict = cast(List[Dict[str, Any]], access_keys_obj)
        result_model = [AccessKey.from_dict(_item) for _item in access_keys_dict]

        return result_model

    def toggle_access_key_status(self, application_id: str, key_id: str, **kwargs) -> AccessKey:
        """Toggle the status of an access key (enable/disable).

        Args:
            application_id: Unique identifier for the application
            key_id: Unique identifier for the access key
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            AccessKey instance with updated status

        Example:
            ```python
            # Toggle key status (enable if disabled, disable if enabled)
            key = auth_client.toggle_access_key_status("app-123", "key-456")
            print(f"New status: {key.status}")
            ```
        """
        key_obj = self._application_api.toggle_access_key_status(
            application_id=application_id, key_id=key_id, **kwargs
        )

        key_obj_dict = cast(Dict[str, Any], key_obj)
        result_model = AccessKey.from_dict(key_obj_dict)

        return result_model

    def delete_access_key(self, application_id: str, key_id: str, **kwargs) -> None:
        """Delete an access key for an application.

        Args:
            application_id: Unique identifier for the application
            key_id: Unique identifier for the access key
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            auth_client.delete_access_key("app-123", "key-456")
            ```
        """
        self._application_api.delete_access_key(
            application_id=application_id, key_id=key_id, **kwargs
        )

    # Users
    def upsert_user(
        self, upsert_user_request: UpsertUserRequest, user_id: str, **kwargs
    ) -> ConductorUser:
        """Create or update a user.

        Args:
            upsert_user_request: User details including name, email, and groups
            user_id: Unique identifier for the user
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ConductorUser instance containing the user details

        Example:
            ```python
            from conductor.client.http.models.upsert_user_request import UpsertUserRequest

            request = UpsertUserRequest(
                name="John Doe",
                email="john.doe@example.com",
                groups=["engineering", "admin"]
            )
            user = auth_client.upsert_user(request, "user-123")
            print(f"User: {user.name}")
            ```
        """
        user_obj = self._user_api.upsert_user(
            upsert_user_request=upsert_user_request, id=user_id, **kwargs
        )
        return self.api_client.deserialize_class(user_obj, "ConductorUser")

    def get_user(self, user_id: str, **kwargs) -> ConductorUser:
        """Get a user by ID.

        Args:
            user_id: Unique identifier for the user
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            ConductorUser instance containing the user details

        Example:
            ```python
            user = auth_client.get_user("user-123")
            print(f"User: {user.name}, Email: {user.email}")
            ```
        """
        user_obj = self._user_api.get_user(id=user_id, **kwargs)
        return self.api_client.deserialize_class(user_obj, "ConductorUser")

    def list_users(self, apps: Optional[bool] = False, **kwargs) -> List[ConductorUser]:
        """List all users in the system.

        Args:
            apps: If True, include application users
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of ConductorUser instances

        Example:
            ```python
            users = auth_client.list_users()
            for user in users:
                print(f"User: {user.name}, Email: {user.email}")
            ```
        """
        kwargs["apps"] = apps
        return self._user_api.list_users(**kwargs)

    def delete_user(self, user_id: str, **kwargs) -> None:
        """Delete a user by ID.

        Args:
            user_id: Unique identifier for the user
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            auth_client.delete_user("user-123")
            ```
        """
        self._user_api.delete_user(id=user_id, **kwargs)

    # Groups
    def upsert_group(
        self, upsert_group_request: UpsertGroupRequest, group_id: str, **kwargs
    ) -> Group:
        """Create or update a group.

        Args:
            upsert_group_request: Group details including name and description
            group_id: Unique identifier for the group
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Group instance containing the group details

        Example:
            ```python
            from conductor.client.http.models.upsert_group_request import UpsertGroupRequest

            request = UpsertGroupRequest(
                name="Engineering Team",
                description="All engineering team members"
            )
            group = auth_client.upsert_group(request, "engineering")
            print(f"Group: {group.name}")
            ```
        """
        group_obj = self._group_api.upsert_group(body=upsert_group_request, id=group_id, **kwargs)
        return self.api_client.deserialize_class(group_obj, "Group")

    def get_group(self, group_id: str, **kwargs) -> Group:
        """Get a group by ID.

        Args:
            group_id: Unique identifier for the group
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Group instance containing the group details

        Example:
            ```python
            group = auth_client.get_group("engineering")
            print(f"Group: {group.name}, Members: {len(group.members)}")
            ```
        """
        group_obj = self._group_api.get_group(id=group_id, **kwargs)
        return self.api_client.deserialize_class(group_obj, "Group")

    def list_groups(self, **kwargs) -> List[Group]:
        """List all groups in the system.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of Group instances

        Example:
            ```python
            groups = auth_client.list_groups()
            for group in groups:
                print(f"Group: {group.name}, Members: {len(group.members)}")
            ```
        """
        return self._group_api.list_groups(**kwargs)

    def delete_group(self, group_id: str, **kwargs) -> None:
        """Delete a group by ID.

        Args:
            group_id: Unique identifier for the group
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            auth_client.delete_group("old-group")
            ```
        """
        self._group_api.delete_group(id=group_id, **kwargs)

    def add_user_to_group(self, group_id: str, user_id: str, **kwargs) -> None:
        """Add a user to a group.

        Args:
            group_id: Unique identifier for the group
            user_id: Unique identifier for the user
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            auth_client.add_user_to_group("engineering", "user-123")
            ```
        """
        self._group_api.add_user_to_group(group_id=group_id, user_id=user_id, **kwargs)

    def get_users_in_group(self, group_id: str, **kwargs) -> List[ConductorUser]:
        """Get all users in a group.

        Args:
            group_id: Unique identifier for the group
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of ConductorUser instances

        Example:
            ```python
            users = auth_client.get_users_in_group("engineering")
            for user in users:
                print(f"User: {user.name}, Email: {user.email}")
            ```
        """
        user_objs = self._group_api.get_users_in_group(id=group_id, **kwargs)
        group_users: List[ConductorUser] = []
        for u in user_objs:
            c_user = self.api_client.deserialize_class(u, "ConductorUser")
            group_users.append(c_user)

        return group_users

    def remove_user_from_group(self, group_id: str, user_id: str, **kwargs) -> None:
        """Remove a user from a group.

        Args:
            group_id: Unique identifier for the group
            user_id: Unique identifier for the user
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            auth_client.remove_user_from_group("engineering", "user-123")
            ```
        """
        self._group_api.remove_user_from_group(group_id=group_id, user_id=user_id, **kwargs)

    # Permissions

    def grant_permissions(
        self, subject: SubjectRef, target: TargetRef, access: List[AccessType]
    ) -> None:
        """Grant permissions to a subject on a target resource.

        Args:
            subject: Subject (user, group, or application) to grant permissions to
            target: Target resource (workflow, task, etc.)
            access: List of access types (READ, EXECUTE, UPDATE, DELETE, etc.)

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.subject_ref import SubjectRef
            from conductor.client.http.models.target_ref import TargetRef
            from conductor.client.orkes.models.access_type import AccessType

            subject = SubjectRef(id="user-123", type="USER")
            target = TargetRef(id="workflow-456", type="WORKFLOW_DEF")
            access = [AccessType.READ, AccessType.EXECUTE]

            auth_client.grant_permissions(subject, target, access)
            ```
        """
        req = AuthorizationRequest(subject, target, access)
        self._authorization_api.grant_permissions(body=req)

    def get_permissions(self, target: TargetRef, **kwargs) -> Dict[str, List[SubjectRef]]:
        """Get all permissions for a target resource.

        Args:
            target: Target resource to get permissions for
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping access types to lists of subjects with that access

        Example:
            ```python
            from conductor.client.http.models.target_ref import TargetRef

            target = TargetRef(id="workflow-456", type="WORKFLOW_DEF")
            permissions = auth_client.get_permissions(target)

            for access_type, subjects in permissions.items():
                print(f"{access_type}: {len(subjects)} subjects")
            ```
        """
        resp_obj = self._authorization_api.get_permissions(
            type=target.type.name, id=target.id, **kwargs
        )
        permissions: Dict[str, List[SubjectRef]] = {}

        for access_type, subjects in resp_obj.items():
            subject_list = [SubjectRef(sub["id"], sub["type"]) for sub in subjects]
            permissions[access_type] = subject_list

        return permissions

    def get_granted_permissions_for_group(self, group_id: str, **kwargs) -> List[GrantedPermission]:
        """Get all permissions granted to a group.

        Args:
            group_id: Unique identifier for the group
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of GrantedPermission instances

        Example:
            ```python
            permissions = auth_client.get_granted_permissions_for_group("engineering")
            for perm in permissions:
                print(f"Target: {perm.target.id}, Access: {perm.access}")
            ```
        """
        granted_access_obj = self._group_api.get_granted_permissions1(group_id=group_id, **kwargs)
        granted_permissions: List[GrantedPermission] = []

        for ga in granted_access_obj.granted_access:
            target = TargetRef(ga.target.id, ga.target.type)
            access = ga.access
            granted_permissions.append(GrantedPermission(target, access))

        return granted_permissions

    def get_granted_permissions_for_user(self, user_id: str, **kwargs) -> List[GrantedPermission]:
        """Get all permissions granted to a user.

        Args:
            user_id: Unique identifier for the user
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of GrantedPermission instances

        Example:
            ```python
            permissions = auth_client.get_granted_permissions_for_user("user-123")
            for perm in permissions:
                print(f"Target: {perm.target.id}, Access: {perm.access}")
            ```
        """
        granted_access_obj = self._user_api.get_granted_permissions(user_id=user_id, **kwargs)

        granted_access_obj_dict = cast(Dict[str, Any], granted_access_obj)

        granted_permissions = []
        for ga in granted_access_obj_dict["grantedAccess"]:
            target = TargetRef(ga["target"]["id"], ga["target"]["type"])
            access = ga["access"]
            granted_permissions.append(GrantedPermission(target, access))
        return granted_permissions

    def remove_permissions(
        self, subject: SubjectRef, target: TargetRef, access: List[AccessType], **kwargs
    ) -> None:
        """Remove permissions from a subject on a target resource.

        Args:
            subject: Subject (user, group, or application) to remove permissions from
            target: Target resource (workflow, task, etc.)
            access: List of access types to remove
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.subject_ref import SubjectRef
            from conductor.client.http.models.target_ref import TargetRef
            from conductor.client.orkes.models.access_type import AccessType

            subject = SubjectRef(id="user-123", type="USER")
            target = TargetRef(id="workflow-456", type="WORKFLOW_DEF")
            access = [AccessType.DELETE]

            auth_client.remove_permissions(subject, target, access)
            ```
        """
        req = AuthorizationRequest(subject, target, access)
        self._authorization_api.remove_permissions(body=req, **kwargs)

    def add_users_to_group(self, body: List[str], group_id: str, **kwargs) -> None:
        """Add multiple users to a group.

        Args:
            body: List of user IDs to add to the group
            group_id: Unique identifier for the group
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            user_ids = ["user-123", "user-456", "user-789"]
            auth_client.add_users_to_group(user_ids, "engineering")
            ```
        """
        self._group_api.add_users_to_group(body=body, group_id=group_id, **kwargs)

    def remove_users_from_group(self, body: List[str], group_id: str, **kwargs) -> None:
        """Remove multiple users from a group.

        Args:
            body: List of user IDs to remove from the group
            group_id: Unique identifier for the group
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            user_ids = ["user-123", "user-456"]
            auth_client.remove_users_from_group(user_ids, "engineering")
            ```
        """
        self._group_api.remove_users_from_group(body=body, group_id=group_id, **kwargs)

    def check_permissions(self, user_id: str, type: str, id: str, **kwargs) -> Dict[str, bool]:
        """Check a user's permissions on a specific resource.

        Args:
            user_id: Unique identifier for the user
            type: Resource type (e.g., "WORKFLOW_DEF", "TASK_DEF")
            id: Resource identifier
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary mapping access types to boolean values indicating if user has that permission

        Example:
            ```python
            permissions = auth_client.check_permissions(
                "user-123",
                "WORKFLOW_DEF",
                "workflow-456"
            )

            if permissions.get("EXECUTE"):
                print("User can execute the workflow")
            if permissions.get("UPDATE"):
                print("User can update the workflow")
            ```
        """
        result = self._user_api.check_permissions(user_id=user_id, type=type, id=id, **kwargs)

        result_dict = cast(Dict[str, Any], result)
        result_model = {k: v for k, v in result_dict.items() if isinstance(v, bool)}

        return result_model
