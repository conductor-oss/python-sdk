from typing import List

from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.codegen.api.application_resource_api import ApplicationResourceApi
from conductor.client.http.models.extended_conductor_application import ExtendedConductorApplication


class ApplicationResourceApiAdapter(ApplicationResourceApi):
    def create_access_key(self, id: str, **kwargs):
        return super().create_access_key(id, **kwargs)

    def add_role_to_application_user(self, application_id: str, role: str, **kwargs):
        return super().add_role_to_application_user(application_id, role, **kwargs)

    def delete_access_key(self, application_id: str, key_id: str, **kwargs):
        return super().delete_access_key(application_id, key_id, **kwargs)

    def remove_role_from_application_user(self, application_id: str, role: str, **kwargs):
        return super().remove_role_from_application_user(application_id, role, **kwargs)

    def get_app_by_access_key_id(
        self, access_key_id: str, **kwargs
    ) -> ExtendedConductorApplication:
        return super().get_app_by_access_key_id(access_key_id, **kwargs)

    def get_access_keys(self, id: str, **kwargs):
        return super().get_access_keys(id=id, **kwargs)

    def toggle_access_key_status(self, application_id: str, key_id: str, **kwargs):
        return super().toggle_access_key_status(application_id, key_id, **kwargs)

    def get_tags_for_application(self, application_id: str, **kwargs) -> List[MetadataTag]:  # type: ignore[override]
        return super().get_tags_for_application(application_id, **kwargs)

    def delete_tag_for_application(self, body: List[MetadataTag], id: str, **kwargs) -> None:
        return super().delete_tag_for_application(body, id, **kwargs)
