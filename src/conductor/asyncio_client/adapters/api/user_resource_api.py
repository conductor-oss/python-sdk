from conductor.asyncio_client.http.api import UserResourceApi


class UserResourceApiAdapter(UserResourceApi):
    async def get_granted_permissions(
        self,
        user_id,
        *args,
        **kwargs,
    ) -> object:
        if not user_id:
            user_id = None
        return await super().get_granted_permissions(user_id=user_id, *args, **kwargs)
