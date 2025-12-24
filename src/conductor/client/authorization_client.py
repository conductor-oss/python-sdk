from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.orkes.models.access_type import AccessType
from conductor.client.orkes.models.granted_permission import GrantedPermission
from conductor.client.orkes.models.access_key import AccessKey
from conductor.client.orkes.models.created_access_key import CreatedAccessKey
from conductor.client.http.models.group import Group
from conductor.client.http.models.target_ref import TargetRef
from conductor.client.http.models.subject_ref import SubjectRef
from conductor.client.http.models.conductor_user import ConductorUser
from conductor.client.http.models.conductor_application import ConductorApplication
from conductor.client.http.models.upsert_user_request import UpsertUserRequest
from conductor.client.http.models.upsert_group_request import UpsertGroupRequest
from conductor.client.http.models.create_or_update_application_request import CreateOrUpdateApplicationRequest


class AuthorizationClient(ABC):
    # ===========================
    # Applications
    # ===========================
    @abstractmethod
    def create_application(
            self,
            create_or_update_application_request: CreateOrUpdateApplicationRequest
    ) -> ConductorApplication:
        """Create an application."""
        pass

    @abstractmethod
    def get_application(self, application_id: str) -> ConductorApplication:
        """Get an application by id."""
        pass

    @abstractmethod
    def list_applications(self) -> List[ConductorApplication]:
        """Get all applications."""
        pass

    @abstractmethod
    def update_application(
            self,
            create_or_update_application_request: CreateOrUpdateApplicationRequest,
            application_id: str
    ) -> ConductorApplication:
        """Update an application."""
        pass

    @abstractmethod
    def delete_application(self, application_id: str):
        """Delete an application."""
        pass

    @abstractmethod
    def get_app_by_access_key_id(self, access_key_id: str) -> str:
        """Get application id by access key id."""
        pass

    # Application Roles
    @abstractmethod
    def add_role_to_application_user(self, application_id: str, role: str):
        """Add a role to application user."""
        pass

    @abstractmethod
    def remove_role_from_application_user(self, application_id: str, role: str):
        """Remove a role from application user."""
        pass

    # Application Tags
    @abstractmethod
    def set_application_tags(self, tags: List[MetadataTag], application_id: str):
        """Put a tag to application."""
        pass

    @abstractmethod
    def get_application_tags(self, application_id: str) -> List[MetadataTag]:
        """Get tags by application."""
        pass

    @abstractmethod
    def delete_application_tags(self, tags: List[MetadataTag], application_id: str):
        """Delete a tag for application."""
        pass

    # Application Access Keys
    @abstractmethod
    def create_access_key(self, application_id: str) -> CreatedAccessKey:
        """Create an access key for an application."""
        pass

    @abstractmethod
    def get_access_keys(self, application_id: str) -> List[AccessKey]:
        """Get application's access keys."""
        pass

    @abstractmethod
    def toggle_access_key_status(self, application_id: str, key_id: str) -> AccessKey:
        """Toggle the status of an access key."""
        pass

    @abstractmethod
    def delete_access_key(self, application_id: str, key_id: str):
        """Delete an access key."""
        pass

    # ===========================
    # Users
    # ===========================
    @abstractmethod
    def upsert_user(self, upsert_user_request: UpsertUserRequest, user_id: str) -> ConductorUser:
        """Create or update a user."""
        pass

    @abstractmethod
    def get_user(self, user_id: str) -> ConductorUser:
        """Get a user by id."""
        pass

    @abstractmethod
    def list_users(self, apps: Optional[bool] = False) -> List[ConductorUser]:
        """Get all users."""
        pass

    @abstractmethod
    def delete_user(self, user_id: str):
        """Delete a user."""
        pass

    @abstractmethod
    def get_granted_permissions_for_user(self, user_id: str) -> List[GrantedPermission]:
        """Get the permissions this user has over workflows and tasks."""
        pass

    @abstractmethod
    def check_permissions(self, user_id: str, target_type: str, target_id: str) -> Dict:
        """Check if user has permissions over a specific target (workflow or task)."""
        pass

    # ===========================
    # Groups
    # ===========================
    @abstractmethod
    def upsert_group(self, upsert_group_request: UpsertGroupRequest, group_id: str) -> Group:
        """Create or update a group."""
        pass

    @abstractmethod
    def get_group(self, group_id: str) -> Group:
        """Get a group by id."""
        pass

    @abstractmethod
    def list_groups(self) -> List[Group]:
        """Get all groups."""
        pass

    @abstractmethod
    def delete_group(self, group_id: str):
        """Delete a group."""
        pass

    @abstractmethod
    def get_granted_permissions_for_group(self, group_id: str) -> List[GrantedPermission]:
        """Get the permissions this group has over workflows and tasks."""
        pass

    # Group Users
    @abstractmethod
    def add_user_to_group(self, group_id: str, user_id: str):
        """Add user to group."""
        pass

    @abstractmethod
    def add_users_to_group(self, group_id: str, user_ids: List[str]):
        """Add users to group."""
        pass

    @abstractmethod
    def get_users_in_group(self, group_id: str) -> List[ConductorUser]:
        """Get all users in group."""
        pass

    @abstractmethod
    def remove_user_from_group(self, group_id: str, user_id: str):
        """Remove user from group."""
        pass

    @abstractmethod
    def remove_users_from_group(self, group_id: str, user_ids: List[str]):
        """Remove users from group."""
        pass

    # ===========================
    # Permissions / Authorization
    # ===========================
    @abstractmethod
    def grant_permissions(self, subject: SubjectRef, target: TargetRef, access: List[AccessType]):
        """Grant access to a user over the target."""
        pass

    @abstractmethod
    def get_permissions(self, target: TargetRef) -> Dict[str, List[SubjectRef]]:
        """Get the access that have been granted over the given object."""
        pass

    @abstractmethod
    def remove_permissions(self, subject: SubjectRef, target: TargetRef, access: List[AccessType]):
        """Remove user's access over the target."""
        pass

    # ===========================
    # Roles (New)
    # ===========================
    @abstractmethod
    def list_all_roles(self) -> List[Dict]:
        """Get all roles (both system and custom)."""
        pass

    @abstractmethod
    def list_system_roles(self) -> Dict[str, Dict]:
        """Get all system-defined roles."""
        pass

    @abstractmethod
    def list_custom_roles(self) -> List[Dict]:
        """Get all custom roles (excludes system roles)."""
        pass

    @abstractmethod
    def list_available_permissions(self) -> Dict[str, Dict]:
        """Get all available permissions that can be assigned to roles."""
        pass

    @abstractmethod
    def create_role(self, create_role_request: Dict) -> Dict:
        """Create a new custom role."""
        pass

    @abstractmethod
    def get_role(self, role_name: str) -> Dict:
        """Get a role by name."""
        pass

    @abstractmethod
    def update_role(self, role_name: str, update_role_request: Dict) -> Dict:
        """Update an existing custom role."""
        pass

    @abstractmethod
    def delete_role(self, role_name: str):
        """Delete a custom role."""
        pass

    # ===========================
    # Token / User Info
    # ===========================
    @abstractmethod
    def get_user_info_from_token(self) -> Dict:
        """Get the user info from the token."""
        pass

    @abstractmethod
    def generate_token(self, key_id: str, key_secret: str) -> Dict:
        """Generate JWT with the given access key."""
        pass

    # ===========================
    # API Gateway Authentication Config
    # ===========================
    @abstractmethod
    def create_gateway_auth_config(self, auth_config: Dict) -> Dict:
        """Create API Gateway authentication configuration."""
        pass

    @abstractmethod
    def get_gateway_auth_config(self, config_id: str) -> Dict:
        """Get API Gateway authentication configuration by ID."""
        pass

    @abstractmethod
    def list_gateway_auth_configs(self) -> List[Dict]:
        """List all API Gateway authentication configurations."""
        pass

    @abstractmethod
    def update_gateway_auth_config(self, config_id: str, auth_config: Dict) -> Dict:
        """Update API Gateway authentication configuration."""
        pass

    @abstractmethod
    def delete_gateway_auth_config(self, config_id: str):
        """Delete API Gateway authentication configuration."""
        pass
