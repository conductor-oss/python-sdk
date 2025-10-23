from conductor.client.codegen.models.sub_workflow_params import SubWorkflowParams


class SubWorkflowParamsAdapter(SubWorkflowParams):
    @SubWorkflowParams.idempotency_strategy.setter  # type: ignore[attr-defined]
    def idempotency_strategy(self, idempotency_strategy):
        """Sets the idempotency_strategy of this SubWorkflowParams.


        :param idempotency_strategy: The idempotency_strategy of this SubWorkflowParams.  # noqa: E501
        :type: str
        """

        self._idempotency_strategy = idempotency_strategy
