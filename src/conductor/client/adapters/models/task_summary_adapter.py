from __future__ import annotations

from typing import ClassVar, Dict

from conductor.client.codegen.models.task_summary import TaskSummary


class TaskSummaryAdapter(TaskSummary):
    swagger_types: ClassVar[Dict[str, str]] = {
        **TaskSummary.swagger_types,
        "domain": "str",
    }

    attribute_map: ClassVar[Dict[str, str]] = {
        **TaskSummary.attribute_map,
        "domain": "domain",
    }

    def __init__(
        self,
        correlation_id=None,
        end_time=None,
        execution_time=None,
        external_input_payload_storage_path=None,
        external_output_payload_storage_path=None,
        input=None,
        output=None,
        queue_wait_time=None,
        reason_for_incompletion=None,
        scheduled_time=None,
        start_time=None,
        status=None,
        task_def_name=None,
        task_id=None,
        task_reference_name=None,
        task_type=None,
        update_time=None,
        workflow_id=None,
        workflow_priority=None,
        workflow_type=None,
        domain=None,
    ):
        """TaskSummary - a model defined in Swagger"""
        self._correlation_id = None
        self._end_time = None
        self._execution_time = None
        self._external_input_payload_storage_path = None
        self._external_output_payload_storage_path = None
        self._input = None
        self._output = None
        self._queue_wait_time = None
        self._reason_for_incompletion = None
        self._scheduled_time = None
        self._start_time = None
        self._status = None
        self._task_def_name = None
        self._task_id = None
        self._task_reference_name = None
        self._task_type = None
        self._update_time = None
        self._workflow_id = None
        self._workflow_priority = None
        self._workflow_type = None
        self._domain = None
        self.discriminator = None
        if correlation_id is not None:
            self.correlation_id = correlation_id
        if end_time is not None:
            self.end_time = end_time
        if execution_time is not None:
            self.execution_time = execution_time
        if external_input_payload_storage_path is not None:
            self.external_input_payload_storage_path = external_input_payload_storage_path
        if external_output_payload_storage_path is not None:
            self.external_output_payload_storage_path = external_output_payload_storage_path
        if input is not None:
            self.input = input
        if output is not None:
            self.output = output
        if queue_wait_time is not None:
            self.queue_wait_time = queue_wait_time
        if reason_for_incompletion is not None:
            self.reason_for_incompletion = reason_for_incompletion
        if scheduled_time is not None:
            self.scheduled_time = scheduled_time
        if start_time is not None:
            self.start_time = start_time
        if status is not None:
            self.status = status
        if task_def_name is not None:
            self.task_def_name = task_def_name
        if task_id is not None:
            self.task_id = task_id
        if task_reference_name is not None:
            self.task_reference_name = task_reference_name
        if task_type is not None:
            self.task_type = task_type
        if update_time is not None:
            self.update_time = update_time
        if workflow_id is not None:
            self.workflow_id = workflow_id
        if workflow_priority is not None:
            self.workflow_priority = workflow_priority
        if workflow_type is not None:
            self.workflow_type = workflow_type
        if domain is not None:
            self.domain = domain

    @property
    def domain(self):
        """Gets the domain of this TaskSummary.  # noqa: E501


        :return: The domain of this TaskSummary.  # noqa: E501
        :rtype: str
        """
        return self._domain

    @domain.setter
    def domain(self, domain):
        """Sets the domain of this TaskSummary.


        :param domain: The domain of this TaskSummary.  # noqa: E501
        :type: str
        """

        self._domain = domain
