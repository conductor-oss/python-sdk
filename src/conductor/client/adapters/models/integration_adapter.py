from __future__ import annotations



from conductor.client.http.models import Integration


class IntegrationAdapter(Integration):
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
