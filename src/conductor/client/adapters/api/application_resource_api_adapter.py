from typing import List

from conductor.client.codegen.api.application_resource_api import ApplicationResourceApi
from conductor.client.http.models.extended_conductor_application import ExtendedConductorApplication
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.http.models.create_or_update_application_request import (
    CreateOrUpdateApplicationRequest,
)


class ApplicationResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = ApplicationResourceApi(api_client)

    def create_access_key(self, id: str, **kwargs) -> object:
        """Create an access key for an application"""
        # Convert empty application id to None to prevent sending invalid data to server
        if not id:
            id = None
        return self._api.create_access_key(id, **kwargs)

    def add_role_to_application_user(self, application_id: str, role: str, **kwargs) -> object:
        """Add a role to an application user"""
        # Convert empty application_id and role to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        if not role:
            role = None
        return self._api.add_role_to_application_user(application_id, role, **kwargs)

    def create_application(self, body: CreateOrUpdateApplicationRequest, **kwargs) -> object:
        """Create an application"""
        return self._api.create_application(body, **kwargs)

    def delete_access_key(self, application_id: str, key_id: str, **kwargs) -> object:
        # Convert empty application_id and key_id to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        if not key_id:
            key_id = None
        return self._api.delete_access_key(application_id, key_id, **kwargs)

    def delete_application(self, id: str, **kwargs) -> object:
        """Delete an application"""
        return self._api.delete_application(id, **kwargs)

    def remove_role_from_application_user(self, application_id: str, role: str, **kwargs) -> object:
        """Remove a role from an application user"""
        # Convert empty application_id and role to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        if not role:
            role = None
        return self._api.remove_role_from_application_user(application_id, role, **kwargs)

    def get_app_by_access_key_id(self, access_key_id: str, **kwargs) -> object:
        """Get an application by access key id"""
        # Convert empty access_key_id to None to prevent sending invalid data to server
        if not access_key_id:
            access_key_id = None
        return self._api.get_app_by_access_key_id(access_key_id, **kwargs)

    def get_access_keys(self, id: str, **kwargs) -> object:
        """Get the access keys for an application"""
        # Convert empty application id to None to prevent sending invalid data to server
        if not id:
            id = None
        return self._api.get_access_keys(id=id, **kwargs)

    def toggle_access_key_status(self, application_id: str, key_id: str, **kwargs) -> object:
        """Toggle the status of an access key"""
        # Convert empty application_id and key_id to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        if not key_id:
            key_id = None
        return self._api.toggle_access_key_status(application_id, key_id, **kwargs)

    def get_tags_for_application(self, application_id: str, **kwargs) -> List[MetadataTag]:
        """Get the tags for an application"""
        # Convert empty application_id to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        return self._api.get_tags_for_application(application_id, **kwargs)

    def delete_tag_for_application(self, tag: List[MetadataTag], id: str, **kwargs) -> None:
        """Delete a tag for an application"""
        # Convert empty application id and tag list to None to prevent sending invalid data to server
        if not id:
            id = None
        if not tag:
            tag = None
        return self._api.delete_tag_for_application(tag, id, **kwargs)

    def get_application(self, id: str, **kwargs) -> object:
        """Get an application by id"""
        return self._api.get_application(id, **kwargs)

    def list_applications(self, **kwargs) -> List[ExtendedConductorApplication]:
        """List all applications"""
        return self._api.list_applications(**kwargs)

    def put_tag_for_application(self, tag: List[MetadataTag], id: str, **kwargs) -> None:
        """Put a tag for an application"""
        return self._api.put_tag_for_application(tag, id, **kwargs)

    def update_application(
        self, body: CreateOrUpdateApplicationRequest, id: str, **kwargs
    ) -> object:
        """Update an application"""
        return self._api.update_application(body, id, **kwargs)
