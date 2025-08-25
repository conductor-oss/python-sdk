from deprecated import deprecated

from conductor.client.http.models.workflow_summary import WorkflowSummary


class WorkflowSummaryAdapter(WorkflowSummary):
    @property
    @deprecated(reason="This field is not present in the Java POJO")
    def output_size(self):
        """Gets the output_size of this WorkflowSummary.  # noqa: E501


        :return: The output_size of this WorkflowSummary.  # noqa: E501
        :rtype: int
        """
        return self._output_size

    @output_size.setter
    @deprecated(reason="This field is not present in the Java POJO")
    def output_size(self, output_size):
        """Sets the output_size of this WorkflowSummary.


        :param output_size: The output_size of this WorkflowSummary.  # noqa: E501
        :type: int
        """

        self._output_size = output_size

    @property
    @deprecated(reason="This field is not present in the Java POJO")
    def input_size(self):
        """Gets the input_size of this WorkflowSummary.  # noqa: E501


        :return: The input_size of this WorkflowSummary.  # noqa: E501
        :rtype: int
        """
        return self._input_size

    @input_size.setter
    @deprecated(reason="This field is not present in the Java POJO")
    def input_size(self, input_size):
        """Sets the input_size of this WorkflowSummary.


        :param input_size: The input_size of this WorkflowSummary.  # noqa: E501
        :type: int
        """

        self._input_size = input_size
