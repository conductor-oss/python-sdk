from conductor.client.http.models.save_schedule_request import \
    SaveScheduleRequest


class SaveScheduleRequestAdapter(SaveScheduleRequest):
    @SaveScheduleRequest.start_workflow_request.setter
    def start_workflow_request(self, start_workflow_request):
        """Sets the start_workflow_request of this SaveScheduleRequest.


        :param start_workflow_request: The start_workflow_request of this SaveScheduleRequest.  # noqa: E501
        :type: StartWorkflowRequest
        """

        self._start_workflow_request = start_workflow_request

