from __future__ import annotations

from conductor.client.http.models import IntegrationApiUpdate


class IntegrationApiUpdateAdapter(IntegrationApiUpdate):
    def __init__(self, configuration=None, description=None, enabled=None, *_args, **_kwargs):
        super().__init__(configuration, description, enabled)
