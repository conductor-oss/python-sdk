from pydantic import StrictStr

from conductor.asyncio_client.http.api import UserResourceApi


class UserResourceApiAdapter(UserResourceApi):
    async def get_granted_permissions(
        self,
        user_id: StrictStr,
        *args,
        **kwargs,
    ) -> object:
        if not user_id:
            user_id = None
        return await super().get_granted_permissions(user_id=user_id, *args, **kwargs)

    async def get_user(
        self,
        id: StrictStr,
        *args,
        **kwargs,
    ) -> object:
        if not id:
            id = None
        return await super().get_user(id=id, *args, **kwargs)
