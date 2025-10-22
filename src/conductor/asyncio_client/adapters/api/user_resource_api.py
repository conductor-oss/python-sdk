from typing import List

from pydantic import StrictStr

from conductor.asyncio_client.http.api import UserResourceApi
from conductor.asyncio_client.adapters.models import UpsertUserRequestAdapter as UpsertUserRequest
from conductor.asyncio_client.adapters.models.conductor_user_adapter import ConductorUserAdapter


class UserResourceApiAdapter(UserResourceApi):
    async def get_granted_permissions(
        self,
        user_id: StrictStr,
        *args,
        **kwargs,
    ) -> object:
        # Convert empty user_id to None to prevent sending invalid data to server
        if not user_id:
            user_id = None
        return await super().get_granted_permissions(user_id, *args, **kwargs)

    async def get_user(
        self,
        id: StrictStr,
        *args,
        **kwargs,
    ) -> ConductorUserAdapter:
        # Convert empty user id to None to prevent sending invalid data to server
        if not id:
            id = None
        return await super().get_user(id, *args, **kwargs)

    async def upsert_user(
        self,
        id: StrictStr,
        upsert_user_request: UpsertUserRequest,
        *args,
        **kwargs,
    ) -> ConductorUserAdapter:
        # Convert empty user id to None to prevent sending invalid data to server
        if not id:
            id = None
        return await super().upsert_user(id, upsert_user_request, *args, **kwargs)

    async def list_users(self, *args, **kwargs) -> List[ConductorUserAdapter]:
        return await super().list_users(*args, **kwargs)

    async def delete_user(
        self,
        id: StrictStr,
        *args,
        **kwargs,
    ) -> object:
        # Convert empty user id to None to prevent sending invalid data to server
        if not id:
            id = None
        return await super().delete_user(id, *args, **kwargs)
