from enum import Enum

from conductor.client.codegen.models.start_workflow_request import StartWorkflowRequest


class IdempotencyStrategy(str, Enum):  # shared
    FAIL = ("FAIL",)
    RETURN_EXISTING = "RETURN_EXISTING"

    def __str__(self) -> str:
        return self.name.__str__()


class StartWorkflowRequestAdapter(StartWorkflowRequest):
    def __init__(
        self,
        correlation_id=None,
        created_by=None,
        external_input_payload_storage_path=None,
        idempotency_key=None,
        idempotency_strategy=None,
        input=None,
        name=None,
        priority=None,
        task_to_domain=None,
        version=None,
        workflow_def=None,
    ):
        """StartWorkflowRequest - a model defined in Swagger"""
        self._correlation_id = None
        self._created_by = None
        self._external_input_payload_storage_path = None
        self._idempotency_key = None
        self._idempotency_strategy = IdempotencyStrategy.FAIL
        self._input = None
        self._name = None
        self._priority = None
        self._task_to_domain = None
        self._version = None
        self._workflow_def = None
        self.discriminator = None
        if correlation_id is not None:
            self.correlation_id = correlation_id
        if created_by is not None:
            self.created_by = created_by
        if external_input_payload_storage_path is not None:
            self.external_input_payload_storage_path = external_input_payload_storage_path
        if idempotency_key is not None:
            self.idempotency_key = idempotency_key
        if idempotency_strategy is not None:
            self.idempotency_strategy = idempotency_strategy
        if input is not None:
            self.input = input
        self.name = name
        if priority is not None:
            self.priority = priority
        if task_to_domain is not None:
            self.task_to_domain = task_to_domain
        if version is not None:
            self.version = version
        if workflow_def is not None:
            self.workflow_def = workflow_def

    @StartWorkflowRequest.name.setter
    def name(self, name):
        """Sets the name of this StartWorkflowRequest.


        :param name: The name of this StartWorkflowRequest.  # noqa: E501
        :type: str
        """
        self._name = name
