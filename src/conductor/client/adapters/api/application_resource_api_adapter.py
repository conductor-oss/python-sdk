from conductor.client.codegen.api.application_resource_api import ApplicationResourceApi


class ApplicationResourceApiAdapter(ApplicationResourceApi):
    def create_access_key(self, id, **kwargs):
        if not id:
            id = None
        return super().create_access_key(id, **kwargs)
