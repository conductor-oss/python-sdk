from __future__ import annotations

from typing import ClassVar, Dict, Optional

from conductor.client.http.models.workflow_task import WorkflowTask


class WorkflowTaskAdapter(WorkflowTask):
    @WorkflowTask.workflow_task_type.setter
    def workflow_task_type(self, workflow_task_type):
        """Sets the workflow_task_type of this WorkflowTask.


        :param workflow_task_type: The workflow_task_type of this WorkflowTask.  # noqa: E501
        :type: str
        """
        self._workflow_task_type = workflow_task_type

    @WorkflowTask.on_state_change.setter
    def on_state_change(self, state_change):
        """Sets the on_state_change of this WorkflowTask.


        :param state_change: The on_state_change of this WorkflowTask.  # noqa: E501
        :type: StateChangeConfig or dict
        """
        if isinstance(state_change, dict):
            # If it's already a dictionary, use it as-is
            self._on_state_change = state_change
        else:
            # If it's a StateChangeConfig object, convert it to the expected format
            self._on_state_change = {
                state_change.type: state_change.events
            }


class CacheConfig:
    swagger_types: ClassVar[Dict[str, str]] = {"key": "str", "ttl_in_second": "int"}

    attribute_map: ClassVar[Dict[str, str]] = {
        "key": "key",
        "ttl_in_second": "ttlInSecond",
    }

    def __init__(self, key: Optional[str] = None, ttl_in_second: Optional[int] = None):
        self._key = key
        self._ttl_in_second = ttl_in_second

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, key):
        self._key = key

    @property
    def ttl_in_second(self):
        return self._ttl_in_second

    @ttl_in_second.setter
    def ttl_in_second(self, ttl_in_second):
        self._ttl_in_second = ttl_in_second
