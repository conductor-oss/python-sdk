from __future__ import annotations

import json
from typing import Optional

from deprecated import deprecated

from conductor.client.helpers.helper import ObjectMapper
from conductor.client.http.models.workflow_def import WorkflowDef

object_mapper = ObjectMapper()


class WorkflowDefAdapter(WorkflowDef):
    def toJSON(self):
        return object_mapper.to_json(obj=self)

    @property
    @deprecated("This field is deprecated and will be removed in a future version")
    def owner_app(self):
        """Gets the owner_app of this WorkflowDef.  # noqa: E501


        :return: The owner_app of this WorkflowDef.  # noqa: E501
        :rtype: str
        """
        return self._owner_app

    @owner_app.setter
    @deprecated("This field is deprecated and will be removed in a future version")
    def owner_app(self, owner_app):
        """Sets the owner_app of this WorkflowDef.


        :param owner_app: The owner_app of this WorkflowDef.  # noqa: E501
        :type: str
        """

        self._owner_app = owner_app

    @property
    @deprecated("This field is deprecated and will be removed in a future version")
    def create_time(self):
        """Gets the create_time of this WorkflowDef.  # noqa: E501


        :return: The create_time of this WorkflowDef.  # noqa: E501
        :rtype: int
        """
        return self._create_time

    @create_time.setter
    @deprecated("This field is deprecated and will be removed in a future version")
    def create_time(self, create_time):
        """Sets the create_time of this WorkflowDef.


        :param create_time: The create_time of this WorkflowDef.  # noqa: E501
        :type: int
        """

        self._create_time = create_time

    @property
    @deprecated("This field is deprecated and will be removed in a future version")
    def update_time(self):
        """Gets the update_time of this WorkflowDef.  # noqa: E501


        :return: The update_time of this WorkflowDef.  # noqa: E501
        :rtype: int
        """
        return self._update_time

    @update_time.setter
    @deprecated("This field is deprecated and will be removed in a future version")
    def update_time(self, update_time):
        """Sets the update_time of this WorkflowDef.


        :param update_time: The update_time of this WorkflowDef.  # noqa: E501
        :type: int
        """

        self._update_time = update_time

    @property
    @deprecated("This field is deprecated and will be removed in a future version")
    def created_by(self):
        """Gets the created_by of this WorkflowDef.  # noqa: E501


        :return: The created_by of this WorkflowDef.  # noqa: E501
        :rtype: str
        """
        return self._created_by

    @created_by.setter
    @deprecated("This field is deprecated and will be removed in a future version")
    def created_by(self, created_by):
        """Sets the created_by of this WorkflowDef.


        :param created_by: The created_by of this WorkflowDef.  # noqa: E501
        :type: str
        """

        self._created_by = created_by

    @property
    @deprecated("This field is deprecated and will be removed in a future version")
    def updated_by(self):
        """Gets the updated_by of this WorkflowDef.  # noqa: E501


        :return: The updated_by of this WorkflowDef.  # noqa: E501
        :rtype: str
        """
        return self._updated_by

    @updated_by.setter
    @deprecated("This field is deprecated and will be removed in a future version")
    def updated_by(self, updated_by):
        """Sets the updated_by of this WorkflowDef.


        :param updated_by: The updated_by of this WorkflowDef.  # noqa: E501
        :type: str
        """

        self._updated_by = updated_by

    @property
    def tasks(self):
        if self._tasks is None:
            self._tasks = []
        return self._tasks

    @tasks.setter
    def tasks(self, tasks):
        """Sets the tasks of this WorkflowDef.


        :param tasks: The tasks of this WorkflowDef.  # noqa: E501
        :type: list[WorkflowTask]
        """
        self._tasks = tasks

    @WorkflowDef.timeout_seconds.setter
    def timeout_seconds(self, timeout_seconds):
        """Sets the timeout_seconds of this WorkflowDef.


        :param timeout_seconds: The timeout_seconds of this WorkflowDef.  # noqa: E501
        :type: int
        """
        self._timeout_seconds = timeout_seconds

def to_workflow_def(
    data: Optional[str] = None, json_data: Optional[dict] = None
) -> WorkflowDefAdapter:
    if json_data is not None:
        return object_mapper.from_json(json_data, WorkflowDefAdapter)
    if data is not None:
        return object_mapper.from_json(json.loads(data), WorkflowDefAdapter)
    raise Exception("missing data or json_data parameter")
