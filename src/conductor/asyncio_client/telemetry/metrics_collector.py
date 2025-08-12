import asyncio
import logging
import os
from typing import Any, ClassVar, Dict, List

from prometheus_client import CollectorRegistry
from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import write_to_textfile
from prometheus_client.multiprocess import MultiProcessCollector

from conductor.shared.telemetry.configuration.metrics import MetricsSettings
from conductor.shared.telemetry.enums.metric_documentation import MetricDocumentation
from conductor.shared.telemetry.enums.metric_label import MetricLabel
from conductor.shared.telemetry.enums.metric_name import MetricName

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Async metrics collector for Orkes Conductor Asyncio Client.
    
    This collector provides async metrics collection capabilities using Prometheus
    and follows the async pattern used throughout the asyncio client.
    """
    
    counters: ClassVar[Dict[str, Counter]] = {}
    gauges: ClassVar[Dict[str, Gauge]] = {}
    registry = CollectorRegistry()
    must_collect_metrics = False

    def __init__(self, settings: MetricsSettings):
        """
        Initialize the async metrics collector.
        
        Parameters:
        -----------
        settings : MetricsSettings
            Configuration settings for metrics collection.
        """
        if settings is not None:
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = settings.directory
            MultiProcessCollector(self.registry)
            self.must_collect_metrics = True
            self.settings = settings

    @staticmethod
    async def provide_metrics(settings: MetricsSettings) -> None:
        """
        Async method to provide metrics collection.
        
        This method runs continuously in the background, writing metrics
        to a file at regular intervals.
        
        Parameters:
        -----------
        settings : MetricsSettings
            Configuration settings for metrics collection.
        """
        if settings is None:
            return
            
        OUTPUT_FILE_PATH: str = os.path.join(
            settings.directory,
            settings.file_name
        )
        registry = CollectorRegistry()
        MultiProcessCollector(registry)
        
        while True:
            try:
                write_to_textfile(
                    OUTPUT_FILE_PATH,
                    registry
                )
                await asyncio.sleep(settings.update_interval)
            except Exception as e:
                logger.error(f"Error writing metrics to file: {e}")
                await asyncio.sleep(settings.update_interval)

    async def increment_task_poll(self, task_type: str) -> None:
        """Increment task poll counter."""
        await self.__increment_counter(
            name=MetricName.TASK_POLL,
            documentation=MetricDocumentation.TASK_POLL,
            labels={
                MetricLabel.TASK_TYPE: task_type
            }
        )

    async def increment_task_execution_queue_full(self, task_type: str) -> None:
        """Increment task execution queue full counter."""
        await self.__increment_counter(
            name=MetricName.TASK_EXECUTION_QUEUE_FULL,
            documentation=MetricDocumentation.TASK_EXECUTION_QUEUE_FULL,
            labels={
                MetricLabel.TASK_TYPE: task_type
            }
        )

    async def increment_uncaught_exception(self) -> None:
        """Increment uncaught exception counter."""
        await self.__increment_counter(
            name=MetricName.THREAD_UNCAUGHT_EXCEPTION,
            documentation=MetricDocumentation.THREAD_UNCAUGHT_EXCEPTION,
            labels={}
        )

    async def increment_task_poll_error(self, task_type: str, exception: Exception) -> None:
        """Increment task poll error counter."""
        await self.__increment_counter(
            name=MetricName.TASK_POLL_ERROR,
            documentation=MetricDocumentation.TASK_POLL_ERROR,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.EXCEPTION: str(exception)
            }
        )

    async def increment_task_paused(self, task_type: str) -> None:
        """Increment task paused counter."""
        await self.__increment_counter(
            name=MetricName.TASK_PAUSED,
            documentation=MetricDocumentation.TASK_PAUSED,
            labels={
                MetricLabel.TASK_TYPE: task_type
            }
        )

    async def increment_task_execution_error(self, task_type: str, exception: Exception) -> None:
        """Increment task execution error counter."""
        await self.__increment_counter(
            name=MetricName.TASK_EXECUTE_ERROR,
            documentation=MetricDocumentation.TASK_EXECUTE_ERROR,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.EXCEPTION: str(exception)
            }
        )

    async def increment_task_ack_failed(self, task_type: str) -> None:
        """Increment task ack failed counter."""
        await self.__increment_counter(
            name=MetricName.TASK_ACK_FAILED,
            documentation=MetricDocumentation.TASK_ACK_FAILED,
            labels={
                MetricLabel.TASK_TYPE: task_type
            }
        )

    async def increment_task_ack_error(self, task_type: str, exception: Exception) -> None:
        """Increment task ack error counter."""
        await self.__increment_counter(
            name=MetricName.TASK_ACK_ERROR,
            documentation=MetricDocumentation.TASK_ACK_ERROR,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.EXCEPTION: str(exception)
            }
        )

    async def increment_task_update_error(self, task_type: str, exception: Exception) -> None:
        """Increment task update error counter."""
        await self.__increment_counter(
            name=MetricName.TASK_UPDATE_ERROR,
            documentation=MetricDocumentation.TASK_UPDATE_ERROR,
            labels={
                MetricLabel.TASK_TYPE: task_type,
                MetricLabel.EXCEPTION: str(exception)
            }
        )

    async def increment_external_payload_used(self, entity_name: str, operation: str, payload_type: str) -> None:
        """Increment external payload used counter."""
        await self.__increment_counter(
            name=MetricName.EXTERNAL_PAYLOAD_USED,
            documentation=MetricDocumentation.EXTERNAL_PAYLOAD_USED,
            labels={
                MetricLabel.ENTITY_NAME: entity_name,
                MetricLabel.OPERATION: operation,
                MetricLabel.PAYLOAD_TYPE: payload_type
            }
        )

    async def increment_workflow_start_error(self, workflow_type: str, exception: Exception) -> None:
        """Increment workflow start error counter."""
        await self.__increment_counter(
            name=MetricName.WORKFLOW_START_ERROR,
            documentation=MetricDocumentation.WORKFLOW_START_ERROR,
            labels={
                MetricLabel.WORKFLOW_TYPE: workflow_type,
                MetricLabel.EXCEPTION: str(exception)
            }
        )

    async def record_workflow_input_payload_size(self, workflow_type: str, version: str, payload_size: int) -> None:
        """Record workflow input payload size."""
        await self.__record_gauge(
            name=MetricName.WORKFLOW_INPUT_SIZE,
            documentation=MetricDocumentation.WORKFLOW_INPUT_SIZE,
            labels={
                MetricLabel.WORKFLOW_TYPE: workflow_type,
                MetricLabel.WORKFLOW_VERSION: version
            },
            value=payload_size
        )

    async def record_task_result_payload_size(self, task_type: str, payload_size: int) -> None:
        """Record task result payload size."""
        await self.__record_gauge(
            name=MetricName.TASK_RESULT_SIZE,
            documentation=MetricDocumentation.TASK_RESULT_SIZE,
            labels={
                MetricLabel.TASK_TYPE: task_type
            },
            value=payload_size
        )

    async def record_task_poll_time(self, task_type: str, time_spent: float) -> None:
        """Record task poll time."""
        await self.__record_gauge(
            name=MetricName.TASK_POLL_TIME,
            documentation=MetricDocumentation.TASK_POLL_TIME,
            labels={
                MetricLabel.TASK_TYPE: task_type
            },
            value=time_spent
        )

    async def record_task_execute_time(self, task_type: str, time_spent: float) -> None:
        """Record task execute time."""
        await self.__record_gauge(
            name=MetricName.TASK_EXECUTE_TIME,
            documentation=MetricDocumentation.TASK_EXECUTE_TIME,
            labels={
                MetricLabel.TASK_TYPE: task_type
            },
            value=time_spent
        )

    async def __increment_counter(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labels: Dict[MetricLabel, str]
    ) -> None:
        """Async method to increment a counter metric."""
        if not self.must_collect_metrics:
            return
        counter = await self.__get_counter(
            name=name,
            documentation=documentation,
            labelnames=labels.keys()
        )
        counter.labels(*labels.values()).inc()

    async def __record_gauge(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labels: Dict[MetricLabel, str],
            value: Any
    ) -> None:
        """Async method to record a gauge metric."""
        if not self.must_collect_metrics:
            return
        gauge = await self.__get_gauge(
            name=name,
            documentation=documentation,
            labelnames=labels.keys()
        )
        gauge.labels(*labels.values()).set(value)

    async def __get_counter(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labelnames: List[MetricLabel]
    ) -> Counter:
        """Async method to get or create a counter metric."""
        if name not in self.counters:
            self.counters[name] = await self.__generate_counter(
                name, documentation, labelnames
            )
        return self.counters[name]

    async def __get_gauge(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labelnames: List[MetricLabel]
    ) -> Gauge:
        """Async method to get or create a gauge metric."""
        if name not in self.gauges:
            self.gauges[name] = await self.__generate_gauge(
                name, documentation, labelnames
            )
        return self.gauges[name]

    async def __generate_counter(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labelnames: List[MetricLabel]
    ) -> Counter:
        """Async method to generate a new counter metric."""
        return Counter(
            name=name,
            documentation=documentation,
            labelnames=labelnames,
            registry=self.registry
        )

    async def __generate_gauge(
            self,
            name: MetricName,
            documentation: MetricDocumentation,
            labelnames: List[MetricLabel]
    ) -> Gauge:
        """Async method to generate a new gauge metric."""
        return Gauge(
            name=name,
            documentation=documentation,
            labelnames=labelnames,
            registry=self.registry
        )
