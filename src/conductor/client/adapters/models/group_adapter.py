from conductor.client.http.models import Group


class GroupAdapter(Group):
    @property
    def default_access(self):
        return super().subject

    @default_access.setter
    def default_access(self, default_access):
        self._default_access = default_access
