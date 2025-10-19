from pydantic import StrictStr

from conductor.asyncio_client.http.api import ApplicationResourceApi


class ApplicationResourceApiAdapter(ApplicationResourceApi):
    async def create_access_key(
        self,
        id: StrictStr,
        *args,
        **kwargs,
    ):
        if not id:
            id = None
        return await super().create_access_key(id=id, *args, **kwargs)

    async def add_role_to_application_user(
        self, application_id: StrictStr, role: StrictStr, *args, **kwargs
    ):
        if not application_id:
            application_id = None
        if not role:
            role = None
        return await super().add_role_to_application_user(
            application_id=application_id, role=role, *args, **kwargs
        )

    async def delete_access_key(
        self,
        application_id: StrictStr,
        key_id: StrictStr,
        *args,
        **kwargs,
    ):
        if not application_id:
            application_id = None
        if not key_id:
            key_id = None
        return await super().delete_access_key(
            application_id=application_id, key_id=key_id, *args, **kwargs
        )

    async def remove_role_from_application_user(
        self,
        application_id: StrictStr,
        role: StrictStr,
        *args,
        **kwargs,
    ):
        if not application_id:
            application_id = None
        if not role:
            role = None
        return await super().remove_role_from_application_user(
            application_id=application_id, role=role, *args, **kwargs
        )

    async def get_app_by_access_key_id(self, access_key_id: StrictStr, *args, **kwargs):
        if not access_key_id:
            access_key_id = None
        return await super().get_app_by_access_key_id(access_key_id=access_key_id, *args, **kwargs)

    async def get_access_keys(self, id: StrictStr, *args, **kwargs):
        if not id:
            id = None
        return await super().get_access_keys(id=id, *args, **kwargs)

    async def toggle_access_key_status(
        self, application_id: StrictStr, key_id: StrictStr, *args, **kwargs
    ):
        if not application_id:
            application_id = None
        if not key_id:
            key_id = None
        return await super().toggle_access_key_status(
            application_id=application_id, key_id=key_id, *args, **kwargs
        )
