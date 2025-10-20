from conductor.asyncio_client.workflow.task.task import TaskInterface
from conductor.shared.workflow.enums import TaskType
from conductor.shared.workflow.models import KafkaPublishInput


class KafkaPublishTask(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        kafka_publish_input: KafkaPublishInput,
    ):
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.KAFKA_PUBLISH,
            input_parameters={
                "kafka_request": kafka_publish_input.model_dump(by_alias=True, exclude_none=True)
            },
        )
