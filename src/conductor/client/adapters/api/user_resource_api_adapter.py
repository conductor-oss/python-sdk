from conductor.client.codegen.api.user_resource_api import UserResourceApi


class UserResourceApiAdapter(UserResourceApi):
    def get_granted_permissions(self, user_id, **kwargs):
        # Convert empty user_id to None to prevent sending invalid data to server
        if not user_id:
            user_id = None
        return super().get_granted_permissions(user_id=user_id, **kwargs)

    def get_user(self, id, **kwargs):
        # Convert empty user id to None to prevent sending invalid data to server
        if not id:
            id = None
        return super().get_user(id=id, **kwargs)

    def upsert_user(self, upsert_user_request, id, **kwargs):
        # Convert empty user id to None to prevent sending invalid data to server
        if not id:
            id = None
        return super().upsert_user(id=id, body=upsert_user_request, **kwargs)

    def delete_user(self, id, **kwargs):
        # Convert empty user id to None to prevent sending invalid data to server
        if not id:
            id = None
        return super().delete_user(id=id, **kwargs)
