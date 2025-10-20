from __future__ import annotations

from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import TaskType
from conductor.shared.workflow.models import HttpPollInput


class HttpPollTask(TaskInterface):
    def __init__(self, task_ref_name: str, http_input: HttpPollInput):
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.HTTP_POLL,
            input_parameters={"http_request": http_input.model_dump(by_alias=True, exclude_none=True)},
        )
