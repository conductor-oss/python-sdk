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
