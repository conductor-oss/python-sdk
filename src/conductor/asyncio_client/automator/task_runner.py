from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
import traceback
from typing import Optional

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.api.task_resource_api import (
    TaskResourceApiAdapter,
)
from conductor.asyncio_client.adapters.models.task_adapter import TaskAdapter
from conductor.asyncio_client.adapters.models.task_exec_log_adapter import (
    TaskExecLogAdapter,
)
from conductor.asyncio_client.adapters.models.task_result_adapter import (
    TaskResultAdapter,
)
from conductor.asyncio_client.configuration import Configuration
from conductor.asyncio_client.http.exceptions import UnauthorizedException
from conductor.asyncio_client.telemetry.metrics_collector import AsyncMetricsCollector
from conductor.asyncio_client.worker.worker_interface import WorkerInterface
from conductor.shared.configuration.settings.metrics_settings import MetricsSettings

logger = logging.getLogger(Configuration.get_logging_formatted_name(__name__))


class AsyncTaskRunner:
    def __init__(
        self,
        worker: WorkerInterface,
        configuration: Configuration = None,
        metrics_settings: MetricsSettings = None,
    ):
        if not isinstance(worker, WorkerInterface):
            raise Exception("Invalid worker")
        self.worker = worker
        self.__set_worker_properties()
        if not isinstance(configuration, Configuration):
            configuration = Configuration()
        self.configuration = configuration
        self.metrics_collector = None
        if metrics_settings is not None:
            self.metrics_collector = AsyncMetricsCollector(metrics_settings)
        self.task_client = TaskResourceApiAdapter(ApiClient(configuration=self.configuration))

    async def run(self) -> None:
        if self.configuration is not None:
            self.configuration.apply_logging_config()
        else:
            logger.setLevel(logging.DEBUG)

        task_names = ",".join(self.worker.task_definition_names)
        logger.info(
            "Polling tasks task_names: %s; domain: %s; polling_interval: %s",
            task_names,
            self.worker.get_domain(),
            self.worker.get_polling_interval_in_seconds(),
        )

        while True:
            # Check if worker should stop due to 401 policy
            if (
                hasattr(self.task_client, "api_client")
                and hasattr(self.task_client.api_client, "auth_401_handler")
                and hasattr(self.task_client.api_client.auth_401_handler, "is_worker_stopped")
                and self.task_client.api_client.auth_401_handler.is_worker_stopped()
            ):
                logger.error("Worker stopped due to persistent 401 authentication failures")
                break
            await self.run_once()

    async def run_once(self) -> None:
        try:
            task = await self.__poll_task()
            if task is not None and task.task_id is not None:
                task_result = await self.__execute_task(task)
                await self.__update_task(task_result)
            await self.__wait_for_polling_interval()
            self.worker.clear_task_definition_name_cache()
        except Exception:
            pass

    async def __poll_task(self) -> Optional[TaskAdapter]:
        task_definition_name = self.worker.get_task_definition_name()
        if self.worker.paused():
            logger.debug("Stop polling task: %s", task_definition_name)
            return None
        if self.metrics_collector is not None:
            await self.metrics_collector.increment_task_poll(task_definition_name)

        try:
            start_time = time.time()
            domain = self.worker.get_domain()
            params = {"workerid": self.worker.get_identity()}
            if domain is not None:
                params["domain"] = domain
            task = await self.task_client.poll(tasktype=task_definition_name, **params)
            finish_time = time.time()
            time_spent = finish_time - start_time
            if self.metrics_collector is not None:
                await self.metrics_collector.record_task_poll_time(task_definition_name, time_spent)
        except UnauthorizedException as auth_exception:
            if self.metrics_collector is not None:
                await self.metrics_collector.increment_task_poll_error(task_definition_name, auth_exception)
            logger.error(
                "Failed to poll task: %s; reason: %s; status: %s",
                task_definition_name,
                auth_exception.reason,
                auth_exception.status,
            )
            return None
        except Exception as e:
            if self.metrics_collector is not None:
                await self.metrics_collector.increment_task_poll_error(task_definition_name, e)
            logger.error(
                "Failed to poll task: %s, reason: %s",
                task_definition_name,
                traceback.format_exc(),
            )
            return None
        if task is not None:
            logger.debug(
                "Polled task: %s; worker_id: %s; domain: %s",
                task_definition_name,
                self.worker.get_identity(),
                self.worker.get_domain(),
            )
        return task

    async def __execute_task(self, task: TaskAdapter) -> Optional[TaskResultAdapter]:
        if not isinstance(task, TaskAdapter):
            return None
        task_definition_name = self.worker.get_task_definition_name()
        logger.debug(
            "Executing task task_id: %s; workflow_instance_id: %s; task_definition_name: %s",
            task.task_id,
            task.workflow_instance_id,
            task_definition_name,
        )
        try:
            start_time = time.time()
            task_result = self.worker.execute(task)
            finish_time = time.time()
            time_spent = finish_time - start_time
            if self.metrics_collector is not None:
                await self.metrics_collector.record_task_execute_time(task_definition_name, time_spent)
                await self.metrics_collector.record_task_result_payload_size(
                    task_definition_name, sys.getsizeof(task_result)
                )
            logger.debug(
                "Executed task task_id: %s; workflow_instance_id: %s; task_definition_name: %s",
                task.task_id,
                task.workflow_instance_id,
                task_definition_name,
            )
        except Exception as e:
            if self.metrics_collector is not None:
                await self.metrics_collector.increment_task_execution_error(task_definition_name, e)
            task_result = TaskResultAdapter(
                task_id=task.task_id,
                workflow_instance_id=task.workflow_instance_id,
                worker_id=self.worker.get_identity(),
            )
            task_result.status = "FAILED"
            task_result.reason_for_incompletion = str(e)
            task_result.logs = [
                TaskExecLogAdapter(
                    log=traceback.format_exc(),
                    task_id=task_result.task_id,
                    created_time=(time.time()),
                )
            ]
            logger.error(
                "Failed to execute task task_id: %s; workflow_instance_id: %s; task_definition_name: %s; reason: %s",
                task.task_id,
                task.workflow_instance_id,
                task_definition_name,
                traceback.format_exc(),
            )
        return task_result

    async def __update_task(self, task_result: TaskResultAdapter):
        if not isinstance(task_result, TaskResultAdapter):
            return None
        task_definition_name = self.worker.get_task_definition_name()
        logger.debug(
            "Updating task task_id: %s, workflow_instance_id: %s, task_definition_name: %s",
            task_result.task_id,
            task_result.workflow_instance_id,
            task_definition_name,
        )
        for attempt in range(4):
            if attempt > 0:
                # Wait for [10s, 20s, 30s] before next attempt
                await asyncio.sleep(attempt * 10)
            try:
                response = await self.task_client.update_task(task_result=task_result)
                logger.debug(
                    "Updated task task_id: %s; workflow_instance_id: %s; task_definition_name: %s; response: %s",
                    task_result.task_id,
                    task_result.workflow_instance_id,
                    task_definition_name,
                    response,
                )
                return response
            except Exception as e:
                if self.metrics_collector is not None:
                    await self.metrics_collector.increment_task_update_error(task_definition_name, e)
                logger.error(
                    "Failed to update task task_id: %s; workflow_instance_id: %s; task_definition_name: %s; reason: %s",
                    task_result.task_id,
                    task_result.workflow_instance_id,
                    task_definition_name,
                    traceback.format_exc(),
                )
        return None

    async def __wait_for_polling_interval(self) -> None:
        polling_interval = self.worker.get_polling_interval_in_seconds()
        await asyncio.sleep(polling_interval)

    def __set_worker_properties(self) -> None:
        # If multiple tasks are supplied to the same worker, then only first
        # task will be considered for setting worker properties
        task_type = self.worker.get_task_definition_name()

        domain = self.__get_property_value_from_env("domain", task_type)
        if domain:
            self.worker.domain = domain
        else:
            self.worker.domain = self.worker.get_domain()

        polling_interval = self.__get_property_value_from_env("polling_interval", task_type)

        if polling_interval:
            try:
                self.worker.poll_interval = float(polling_interval)
            except Exception as e:
                logger.error(
                    "Error converting polling_interval to float value: %s, exception: %s",
                    polling_interval,
                    e,
                )
                self.worker.poll_interval = self.worker.get_polling_interval_in_seconds()

    def __get_property_value_from_env(self, prop, task_type):
        """
        get the property from the env variable
        e.g. conductor_worker_"prop" or conductor_worker_"task_type"_"prop"
        """
        prefix = "conductor_worker"
        # Look for generic property in both case environment variables
        key = prefix + "_" + prop
        value_all = os.getenv(key, os.getenv(key.upper()))

        # Look for task specific property in both case environment variables
        key_small = prefix + "_" + task_type + "_" + prop
        key_upper = prefix.upper() + "_" + task_type + "_" + prop.upper()
        value = os.getenv(key_small, os.getenv(key_upper, value_all))
        return value
