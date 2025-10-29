from __future__ import annotations

import dataclasses
import inspect
import logging
import time
import traceback
from copy import deepcopy
from typing import Any, Callable, Optional, Union

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.models.task_adapter import TaskAdapter
from conductor.asyncio_client.adapters.models.task_exec_log_adapter import (
    TaskExecLogAdapter,
)
from conductor.asyncio_client.adapters.models.task_result_adapter import (
    TaskResultAdapter,
)
from conductor.asyncio_client.configuration import Configuration
from conductor.asyncio_client.worker.worker_interface import WorkerInterface
from conductor.shared.automator import utils
from conductor.shared.automator.utils import convert_from_dict_or_list
from conductor.shared.http.enums import TaskResultStatus
from conductor.shared.worker.exception import NonRetryableException

ExecuteTaskFunction = Callable[[Union[TaskAdapter, object]], Union[TaskResultAdapter, object]]

logger = logging.getLogger(Configuration.get_logging_formatted_name(__name__))


def is_callable_input_parameter_a_task(
    callable_exec_task_function: ExecuteTaskFunction, object_type: Any
) -> bool:
    parameters = inspect.signature(callable_exec_task_function).parameters
    if len(parameters) != 1:
        return False
    parameter = parameters[next(iter(parameters.keys()))]
    return parameter.annotation in {object_type, parameter.empty} or parameter.annotation is object


def is_callable_return_value_of_type(
    callable_exec_task_function: ExecuteTaskFunction, object_type: Any
) -> bool:
    return_annotation = inspect.signature(callable_exec_task_function).return_annotation
    return return_annotation == object_type


class Worker(WorkerInterface):
    def __init__(
        self,
        task_definition_name: str,
        execute_function: ExecuteTaskFunction,
        poll_interval: Optional[float] = None,
        domain: Optional[str] = None,
        worker_id: Optional[str] = None,
    ):
        super().__init__(task_definition_name)
        self.api_client = ApiClient()
        self.config = Configuration()
        self.poll_interval = poll_interval or self.config.get_poll_interval()
        self.domain = domain or self.config.get_domain()
        self.worker_id = worker_id or super().get_identity()
        self.execute_function = deepcopy(execute_function)

    def execute(self, task: TaskAdapter) -> TaskResultAdapter:
        task_input = {}
        task_output = None
        task_result: TaskResultAdapter = self.get_task_result_from_task(task)

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
                            task_input[input_name] = convert_from_dict_or_list(
                                typ,
                                task.input_data[input_name],
                            )
                    elif default_value is not inspect.Parameter.empty:
                        task_input[input_name] = default_value
                    else:
                        task_input[input_name] = None
                task_output = self.execute_function(**task_input)

            if isinstance(task_output, TaskResultAdapter):
                task_output.task_id = task.task_id
                task_output.workflow_instance_id = task.workflow_instance_id
                return task_output
            else:
                task_result.status = TaskResultStatus.COMPLETED
                task_result.output_data = {"result": task_output}

        except NonRetryableException as ne:
            task_result.status = TaskResultStatus.FAILED_WITH_TERMINAL_ERROR
            if len(ne.args) > 0:
                task_result.reason_for_incompletion = ne.args[0]

        except Exception as ne:
            logger.error(
                "Error executing task task_def_name: %s; task_id: %s",
                task.task_def_name,
                task.task_id,
            )

            task_result.logs = [
                TaskExecLogAdapter(
                    log=traceback.format_exc(),
                    task_id=task_result.task_id,
                    created_time=int(time.time()),
                )
            ]
            task_result.status = TaskResultStatus.FAILED
            if len(ne.args) > 0:
                task_result.reason_for_incompletion = ne.args[0]

        if dataclasses.is_dataclass(type(task_result.output_data)):
            task_output = dataclasses.asdict(task_result.output_data)
            task_result.output_data = task_output
            return task_result
        if not isinstance(task_result.output_data, dict):
            task_output = task_result.output_data
            task_result.output_data = self.api_client.sanitize_for_serialization(task_output)
            if not isinstance(task_result.output_data, dict):
                task_result.output_data = {"result": task_result.output_data}

        return task_result

    def get_identity(self) -> str:
        return self.worker_id

    @property
    def execute_function(self) -> ExecuteTaskFunction:
        return self._execute_function

    @execute_function.setter
    def execute_function(self, execute_function: ExecuteTaskFunction) -> None:
        self._execute_function = execute_function
        self._is_execute_function_input_parameter_a_task = is_callable_input_parameter_a_task(
            callable_exec_task_function=execute_function,
            object_type=TaskAdapter,
        )
        self._is_execute_function_return_value_a_task_result = is_callable_return_value_of_type(
            callable_exec_task_function=execute_function,
            object_type=TaskResultAdapter,
        )
