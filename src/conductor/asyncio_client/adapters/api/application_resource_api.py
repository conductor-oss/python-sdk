from typing import List, Optional

from pydantic import StrictStr

from conductor.asyncio_client.http.api import ApplicationResourceApi
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.adapters.models.extended_conductor_application_adapter import (
    ExtendedConductorApplicationAdapter,
)


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

    async def get_app_by_access_key_id(
        self, access_key_id: StrictStr, *args, **kwargs
    ) -> Optional[ExtendedConductorApplicationAdapter]:
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

    async def put_tag_for_application(
        self, id: StrictStr, tag: List[TagAdapter], *args, **kwargs
    ) -> None:
        # Convert empty application id and tag list to None to prevent sending invalid data to server
        if not id:
            id = None
        if not tag:
            tag = None
        return await super().put_tag_for_application(id, tag, *args, **kwargs)

    async def delete_tag_for_application(
        self, id: StrictStr, tag: List[TagAdapter], *args, **kwargs
    ) -> None:
        # Convert empty application id and tag list to None to prevent sending invalid data to server
        if not id:
            id = None
        if not tag:
            tag = None
        return await super().delete_tag_for_application(id, tag, *args, **kwargs)

    async def create_application(self, *args, **kwargs) -> ExtendedConductorApplicationAdapter:
        return await super().create_application(*args, **kwargs)

    async def update_application(self, *args, **kwargs) -> ExtendedConductorApplicationAdapter:
        return await super().update_application(*args, **kwargs)

    async def get_application(self, *args, **kwargs) -> ExtendedConductorApplicationAdapter:
        return await super().get_application(*args, **kwargs)

    async def list_applications(self, *args, **kwargs) -> List[ExtendedConductorApplicationAdapter]:
        return await super().list_applications(*args, **kwargs)
