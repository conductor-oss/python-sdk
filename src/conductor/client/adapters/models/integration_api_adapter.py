from conductor.client.http.models import IntegrationApi


class IntegrationApiAdapter(IntegrationApi):
    def __init__(self, api=None, configuration=None, created_on=None, created_by=None, description=None, enabled=None, integration_name=None, owner_app=None, tags=None, updated_on=None, updated_by=None):
        self._api = None
        self._configuration = None
        self._create_time = None
        self._created_by = None
        self._description = None
        self._enabled = None
        self._integration_name = None
        self._owner_app = None
        self._tags = None
        self._update_time = None
        self._updated_by = None
        self.discriminator = None
        if api is not None:
            self.api = api
        if configuration is not None:
            self.configuration = configuration
        if created_on is not None:
            self.create_time = created_on
        if created_by is not None:
            self.created_by = created_by
        if description is not None:
            self.description = description
        if enabled is not None:
            self.enabled = enabled
        if integration_name is not None:
            self.integration_name = integration_name
        if owner_app is not None:
            self.owner_app = owner_app
        if tags is not None:
            self.tags = tags
        if updated_on is not None:
            self.update_time = updated_on
        if updated_by is not None:
            self.updated_by = updated_by

    @property
    def created_on(self):
        return self._create_time

    @created_on.setter
    def created_on(self, create_time):
        self._create_time = create_time

    @property
    def updated_on(self):
        return self._update_time

    @updated_on.setter
    def updated_on(self, update_time):
        self._update_time = update_time
