from pydantic import field_validator

from conductor.asyncio_client.http.models import TargetRef


class TargetRefAdapter(TargetRef):
    @field_validator("id")
    def id_validate_enum(cls, value):
        """Validates the enum"""
        return value
