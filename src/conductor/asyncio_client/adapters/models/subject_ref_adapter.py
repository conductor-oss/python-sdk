import re

from pydantic import field_validator

from conductor.asyncio_client.http.models import SubjectRef


class SubjectRefAdapter(SubjectRef):
    @field_validator("type")
    def type_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if value is None:
            return value

        if not re.match(r"USER|ROLE|GROUP", value):
            raise ValueError(r"must validate the regular expression /user|role|group/")
        return value
