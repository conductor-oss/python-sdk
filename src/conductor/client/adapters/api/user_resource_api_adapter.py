from conductor.client.codegen.api.user_resource_api import UserResourceApi


class UserResourceApiAdapter(UserResourceApi):
    def get_granted_permissions(self, user_id, **kwargs):
        if not user_id:
            user_id = None
        return super().get_granted_permissions(user_id=user_id, **kwargs)
