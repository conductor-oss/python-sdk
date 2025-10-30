from typing import List

from conductor.client.codegen.api.application_resource_api import ApplicationResourceApi
from conductor.client.http.models.extended_conductor_application import ExtendedConductorApplication
from conductor.client.orkes.models.metadata_tag import MetadataTag


class ApplicationResourceApiAdapter(ApplicationResourceApi):
    def create_access_key(self, id: str, **kwargs):
        # Convert empty application id to None to prevent sending invalid data to server
        if not id:
            id = None
        return super().create_access_key(id, **kwargs)

    def add_role_to_application_user(self, application_id: str, role: str, **kwargs):
        # Convert empty application_id and role to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        if not role:
            role = None
        return super().add_role_to_application_user(application_id, role, **kwargs)

    def delete_access_key(self, application_id: str, key_id: str, **kwargs):
        # Convert empty application_id and key_id to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        if not key_id:
            key_id = None
        return super().delete_access_key(application_id, key_id, **kwargs)

    def remove_role_from_application_user(self, application_id: str, role: str, **kwargs):
        # Convert empty application_id and role to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        if not role:
            role = None
        return super().remove_role_from_application_user(application_id, role, **kwargs)

    def get_app_by_access_key_id(
        self, access_key_id: str, **kwargs
    ) -> ExtendedConductorApplication:
        # Convert empty access_key_id to None to prevent sending invalid data to server
        if not access_key_id:
            access_key_id = None
        return super().get_app_by_access_key_id(access_key_id, **kwargs)

    def get_access_keys(self, id: str, **kwargs):
        # Convert empty application id to None to prevent sending invalid data to server
        if not id:
            id = None
        return super().get_access_keys(id=id, **kwargs)

    def toggle_access_key_status(self, application_id: str, key_id: str, **kwargs):
        # Convert empty application_id and key_id to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        if not key_id:
            key_id = None
        return super().toggle_access_key_status(application_id, key_id, **kwargs)

    def get_tags_for_application(self, application_id: str, **kwargs) -> List[MetadataTag]:
        # Convert empty application_id to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        return super().get_tags_for_application(application_id, **kwargs)

    def delete_tag_for_application(self, tag: List[MetadataTag], id: str, **kwargs) -> None:
        # Convert empty application id and tag list to None to prevent sending invalid data to server
        if not id:
            id = None
        if not tag:
            tag = None
        return super().delete_tag_for_application(tag, id, **kwargs)
