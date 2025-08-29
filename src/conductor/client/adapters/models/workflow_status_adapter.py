from conductor.client.adapters.models.workflow_run_adapter import (  # shared
    running_status, successful_status, terminal_status)
from conductor.client.codegen.models.workflow_status import WorkflowStatus


class WorkflowStatusAdapter(WorkflowStatus):
    def is_completed(self) -> bool:
        """Checks if the workflow has completed
        :return: True if the workflow status is COMPLETED, FAILED or TERMINATED
        """
        return self._status in terminal_status

    def is_successful(self) -> bool:
        """Checks if the workflow has completed in successful state (ie COMPLETED)
        :return: True if the workflow status is COMPLETED
        """
        return self._status in successful_status

    def is_running(self) -> bool:
        return self.status in running_status
