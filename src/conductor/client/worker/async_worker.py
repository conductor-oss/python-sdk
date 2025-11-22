from __future__ import annotations
import inspect
import logging
import traceback
import time
import dataclasses
from typing import Optional

from typing_extensions import Self

from conductor.client.automator import utils
from conductor.client.automator.utils import convert_from_dict_or_list
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api_client import ApiClient
from conductor.client.http.models import TaskExecLog
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.base_worker import BaseWorker, ExecuteTaskFunction
from conductor.client.worker.exception import NonRetryableException

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(
        __name__
    )
)

class AsyncWorker(BaseWorker):
    def __init__(self,
                 task_definition_name: str,
                 execute_function: ExecuteTaskFunction,
                 poll_interval: Optional[float] = None,
                 domain: Optional[str] = None,
                 worker_id: Optional[str] = None,
                 ) -> Self:
        super().__init__(
            task_definition_name,
            execute_function,
            poll_interval,
            domain,
            worker_id
        )
        self.api_client = ApiClient()

    async def async_execute(self, task: Task) -> TaskResult:
        task_input = {}
        task_output = None
        task_result: TaskResult = self.get_task_result_from_task(task)

        try:
            if self._is_execute_function_input_parameter_a_task:
                task_output = self.execute_function(task)
            else:
                params = inspect.signature(self.execute_function).parameters
                for input_name in params:
                    typ = params[input_name].annotation
                    default_value = params[input_name].default
                    if input_name in task.input_data:
                        if typ in utils.simple_types:
                            task_input[input_name] = task.input_data[input_name]
                        else:
                            task_input[input_name] = convert_from_dict_or_list(typ, task.input_data[input_name])
                    elif default_value is not inspect.Parameter.empty:
                        task_input[input_name] = default_value
                    else:
                        task_input[input_name] = None
                task_output = self.execute_function(**task_input)

            if inspect.iscoroutine(task_output):
                task_output = await task_output

            if isinstance(task_output, TaskResult):
                return task_output
            
            from conductor.client.context.task_context import TaskInProgress
            if isinstance(task_output, TaskInProgress):
                return task_output

            task_result.status = TaskResultStatus.COMPLETED
            task_result.output_data = task_output

        except NonRetryableException as ne:
            task_result.status = TaskResultStatus.FAILED_WITH_TERMINAL_ERROR
            if len(ne.args) > 0:
                task_result.reason_for_incompletion = ne.args[0]

        except Exception as ne:
            logger.error(
                "Error executing task %s with id %s. error = %s",
                task.task_def_name,
                task.task_id,
                traceback.format_exc()
            )

            task_result.logs = [TaskExecLog(
                traceback.format_exc(), task_result.task_id, int(time.time()))]
            task_result.status = TaskResultStatus.FAILED
            if len(ne.args) > 0:
                task_result.reason_for_incompletion = ne.args[0]
        
        if dataclasses.is_dataclass(type(task_result.output_data)):
            task_output = dataclasses.asdict(task_result.output_data)
            task_result.output_data = task_output
            return task_result
        if not isinstance(task_result.output_data, dict):
            task_output = task_result.output_data
            try:
                task_result.output_data = self.api_client.sanitize_for_serialization(task_output)
                if not isinstance(task_result.output_data, dict):
                    task_result.output_data = {"result": task_result.output_data}
            except (RecursionError, TypeError, AttributeError) as e:
                logger.warning(
                    "Task output of type %s could not be serialized: %s. "
                    "Converting to string. Consider returning serializable data "
                    "(e.g., response.json() instead of response object).",
                    type(task_output).__name__,
                    str(e)[:100]
                )
                task_result.output_data = {
                    "result": str(task_output),
                    "type": type(task_output).__name__,
                    "error": "Object could not be serialized. Please return JSON-serializable data."
                }

        return task_result
    
    def execute(self, task: Task) -> TaskResult:
        raise Exception('execute() is not supported in ASyncWorker, please use async_execute')
