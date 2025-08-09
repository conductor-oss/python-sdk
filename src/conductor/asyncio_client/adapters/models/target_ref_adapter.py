from pydantic import field_validator

from conductor.asyncio_client.http.models import TargetRef


class TargetRefAdapter(TargetRef):
    @field_validator("id")
    def id_validate_enum(cls, value):
        # Bypassing validation due the src/conductor/client/http/models/target_ref.py:103
        return value
