from __future__ import annotations

from typing import Optional

from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import TaskType
from conductor.shared.workflow.models import HttpInput


class HttpTask(TaskInterface):
    def __init__(self, task_ref_name: str, http_input: HttpInput | dict):
        if isinstance(http_input, dict):
            http_input = HttpInput.model_validate(http_input)

        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.HTTP,
            input_parameters={
                "http_request": http_input.model_dump(by_alias=True, exclude_none=True)
            },
        )

    def status_code(self) -> str:
        return "${" + f"{self.task_reference_name}.output.response.statusCode" + "}"

    def headers(self, json_path: Optional[str] = None) -> str:
        if json_path is None:
            return "${" + f"{self.task_reference_name}.output.response.headers" + "}"
        return "${" + f"{self.task_reference_name}.output.response.headers.{json_path}" + "}"

    def body(self, json_path: Optional[str] = None) -> str:
        if json_path is None:
            return "${" + f"{self.task_reference_name}.output.response.body" + "}"
        return "${" + f"{self.task_reference_name}.output.response.body.{json_path}" + "}"
