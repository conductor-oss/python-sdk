from conductor.client.codegen.api.application_resource_api import ApplicationResourceApi


class ApplicationResourceApiAdapter(ApplicationResourceApi):
    def create_access_key(self, id, **kwargs):
        # Convert empty application id to None to prevent sending invalid data to server
        if not id:
            id = None
        return super().create_access_key(id, **kwargs)

    def add_role_to_application_user(self, application_id, role, **kwargs):
        # Convert empty application_id and role to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        if not role:
            role = None
        return super().add_role_to_application_user(application_id, role, **kwargs)

    def delete_access_key(self, application_id, key_id, **kwargs):
        # Convert empty application_id and key_id to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        if not key_id:
            key_id = None
        return super().delete_access_key(application_id, key_id, **kwargs)

    def remove_role_from_application_user(self, application_id, role, **kwargs):
        # Convert empty application_id and role to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        if not role:
            role = None
        return super().remove_role_from_application_user(application_id, role, **kwargs)

    def get_app_by_access_key_id(self, access_key_id: str, **kwargs):
        # Convert empty access_key_id to None to prevent sending invalid data to server
        if not access_key_id:
            access_key_id = None
        return super().get_app_by_access_key_id(access_key_id, **kwargs)

    def get_access_keys(self, id: str, **kwargs):
        # Convert empty application id to None to prevent sending invalid data to server
        if not id:
            id = None
        return super().get_access_keys(id=id, **kwargs)

    def toggle_access_key_status(self, application_id, key_id, **kwargs):
        # Convert empty application_id and key_id to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        if not key_id:
            key_id = None
        return super().toggle_access_key_status(application_id, key_id, **kwargs)

    def get_tags_for_application(self, application_id, **kwargs):
        # Convert empty application_id to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        return super().get_tags_for_application(application_id, **kwargs)

    def delete_tag_for_application(self, body, id, **kwargs):
        # Convert empty tag list (body) and application id to None to prevent sending invalid data to server
        if not body:
            body = None
        if not id:
            id = None
        return super().delete_tag_for_application(body, id, **kwargs)
