from pydantic import field_validator

from conductor.asyncio_client.http.models import UpsertGroupRequest


class UpsertGroupRequestAdapter(UpsertGroupRequest):
    @field_validator("default_access")
    def default_access_validate_enum(cls, value):
        # Bypassing validation due the src/conductor/client/http/models/upsert_group_request.py:123
        return value
