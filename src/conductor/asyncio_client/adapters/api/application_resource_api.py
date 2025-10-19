from pydantic import StrictStr

from conductor.asyncio_client.http.api import ApplicationResourceApi


class ApplicationResourceApiAdapter(ApplicationResourceApi):
    async def create_access_key(
        self,
        id: StrictStr,
        *args,
        **kwargs,
    ) -> object:
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
