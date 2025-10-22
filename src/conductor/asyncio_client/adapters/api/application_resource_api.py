from typing import List

from pydantic import StrictStr

from conductor.asyncio_client.http.api import ApplicationResourceApi
from conductor.asyncio_client.http.models import Tag


class ApplicationResourceApiAdapter(ApplicationResourceApi):
    async def create_access_key(
        self,
        id: StrictStr,
        *args,
        **kwargs,
    ):
        # Convert empty application id to None to prevent sending invalid data to server
        if not id:
            id = None
        return await super().create_access_key(id, *args, **kwargs)

    async def add_role_to_application_user(
        self, application_id: StrictStr, role: StrictStr, *args, **kwargs
    ):
        # Convert empty application_id and role to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        if not role:
            role = None
        return await super().add_role_to_application_user(application_id, role, *args, **kwargs)

    async def delete_access_key(
        self,
        application_id: StrictStr,
        key_id: StrictStr,
        *args,
        **kwargs,
    ):
        # Convert empty application_id and key_id to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        if not key_id:
            key_id = None
        return await super().delete_access_key(application_id, key_id, *args, **kwargs)

    async def remove_role_from_application_user(
        self,
        application_id: StrictStr,
        role: StrictStr,
        *args,
        **kwargs,
    ):
        # Convert empty application_id and role to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        if not role:
            role = None
        return await super().remove_role_from_application_user(
            application_id, role, *args, **kwargs
        )

    async def get_app_by_access_key_id(self, access_key_id: StrictStr, *args, **kwargs):
        # Convert empty access_key_id to None to prevent sending invalid data to server
        if not access_key_id:
            access_key_id = None
        return await super().get_app_by_access_key_id(access_key_id, *args, **kwargs)

    async def get_access_keys(self, id: StrictStr, *args, **kwargs):
        # Convert empty application id to None to prevent sending invalid data to server
        if not id:
            id = None
        return await super().get_access_keys(id, *args, **kwargs)

    async def toggle_access_key_status(
        self, application_id: StrictStr, key_id: StrictStr, *args, **kwargs
    ):
        # Convert empty application_id and key_id to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        if not key_id:
            key_id = None
        return await super().toggle_access_key_status(application_id, key_id, *args, **kwargs)

    async def get_tags_for_application(self, application_id: StrictStr, *args, **kwargs):
        # Convert empty application_id to None to prevent sending invalid data to server
        if not application_id:
            application_id = None
        return await super().get_tags_for_application(application_id, *args, **kwargs)

    async def delete_tag_for_application(
        self, id: StrictStr, tag: List[Tag], *args, **kwargs
    ) -> None:
        # Convert empty application id and tag list to None to prevent sending invalid data to server
        if not id:
            id = None
        if not tag:
            tag = None
        return await super().delete_tag_for_application(id, tag, *args, **kwargs)
