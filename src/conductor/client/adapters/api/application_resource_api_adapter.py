from conductor.client.codegen.api.application_resource_api import ApplicationResourceApi


class ApplicationResourceApiAdapter(ApplicationResourceApi):
    def create_access_key(self, id, **kwargs):
        if not id:
            id = None
        return super().create_access_key(id, **kwargs)

    def add_role_to_application_user(self, application_id, role, **kwargs):
        if not application_id:
            application_id = None
        if not role:
            role = None
        return super().add_role_to_application_user(application_id, role, **kwargs)

    def delete_access_key(self, application_id, key_id, **kwargs):
        if not application_id:
            application_id = None
        if not key_id:
            key_id = None
        return super().delete_access_key(application_id, key_id, **kwargs)

    def remove_role_from_application_user(self, application_id, role, **kwargs):
        if not application_id:
            application_id = None
        if not role:
            role = None
        return super().remove_role_from_application_user(application_id, role, **kwargs)

    def get_app_by_access_key_id(self, access_key_id: str, **kwargs):
        if not access_key_id:
            access_key_id = None
        return super().get_app_by_access_key_id(access_key_id=access_key_id, **kwargs)

    def get_access_keys(self, id: str, **kwargs):
        if not id:
            id = None
        return super().get_access_keys(id=id, **kwargs)
