from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, List, Dict

from conductor.client.adapters.models.workflow_run_adapter import WorkflowRunAdapter as WorkflowRun
from conductor.client.adapters.models.skip_task_request_adapter import SkipTaskRequestAdapter as SkipTaskRequest
from conductor.client.adapters.models.workflow_status_adapter import WorkflowStatusAdapter as WorkflowStatus
from conductor.client.adapters.models.scrollable_search_result_workflow_summary_adapter import ScrollableSearchResultWorkflowSummaryAdapter as ScrollableSearchResultWorkflowSummary
from conductor.client.adapters.models.signal_response_adapter import SignalResponseAdapter as SignalResponse
from conductor.client.adapters.models.correlation_ids_search_request_adapter import CorrelationIdsSearchRequestAdapter as CorrelationIdsSearchRequest
from conductor.client.adapters.models.rerun_workflow_request_adapter import RerunWorkflowRequestAdapter as RerunWorkflowRequest
from conductor.client.adapters.models.start_workflow_request_adapter import StartWorkflowRequestAdapter as StartWorkflowRequest
from conductor.client.adapters.models.workflow_adapter import WorkflowAdapter as Workflow
from conductor.client.adapters.models.workflow_state_update_adapter import WorkflowStateUpdateAdapter as WorkflowStateUpdate
from conductor.client.adapters.models.workflow_test_request_adapter import WorkflowTestRequestAdapter as WorkflowTestRequest


class WorkflowClient(ABC):
    @abstractmethod
    def start_workflow(self, start_workflow_request: StartWorkflowRequest) -> str:
        pass

    @abstractmethod
    def get_workflow(self, workflow_id: str, include_tasks: Optional[bool] = True) -> Workflow:
        pass

    @abstractmethod
    def get_workflow_status(self, workflow_id: str, include_output: Optional[bool] = None,
                            include_variables: Optional[bool] = None) -> WorkflowStatus:
        pass

    @abstractmethod
    def delete_workflow(self, workflow_id: str, archive_workflow: Optional[bool] = True):
        pass

    @abstractmethod
    def terminate_workflow(self, workflow_id: str, reason: Optional[str] = None,
                           trigger_failure_workflow: bool = False):
        pass

    @abstractmethod
    def execute_workflow(
            self,
            start_workflow_request: StartWorkflowRequest,
            request_id: Optional[str] = None,
            wait_until_task_ref: Optional[str] = None,
            wait_for_seconds: int = 30
    ) -> WorkflowRun:
        pass

    @abstractmethod
    def execute_workflow_with_return_strategy(
            self,
            start_workflow_request: StartWorkflowRequest,
            request_id: Optional[str] = None,
            wait_until_task_ref: Optional[str] = None,
            wait_for_seconds: int = 30,
            consistency: Optional[str] = None,
            return_strategy: Optional[str] = None
    ) -> SignalResponse:
        pass

    @abstractmethod
    def pause_workflow(self, workflow_id: str):
        pass

    @abstractmethod
    def resume_workflow(self, workflow_id: str):
        pass

    @abstractmethod
    def restart_workflow(self, workflow_id: str, use_latest_def: Optional[bool] = False):
        pass

    @abstractmethod
    def retry_workflow(self, workflow_id: str, resume_subworkflow_tasks: Optional[bool] = False):
        pass

    @abstractmethod
    def rerun_workflow(self, workflow_id: str, rerun_workflow_request: RerunWorkflowRequest):
        pass

    @abstractmethod
    def skip_task_from_workflow(self, workflow_id: str, task_reference_name: str, request: SkipTaskRequest):
        pass

    @abstractmethod
    def test_workflow(self, test_request: WorkflowTestRequest) -> Workflow:
        pass

    @abstractmethod
    def search(self, start: int = 0, size: int = 100, free_text: str = "*",
               query: Optional[str] = None) -> ScrollableSearchResultWorkflowSummary:
        pass

    @abstractmethod
    def get_by_correlation_ids_in_batch(
            self,
            batch_request: CorrelationIdsSearchRequest,
            include_completed: bool = False,
            include_tasks: bool = False) -> Dict[str, List[Workflow]]:
        pass

    @abstractmethod
    def get_by_correlation_ids(
            self,
            workflow_name: str,
            correlation_ids: List[str],
            include_completed: bool = False,
            include_tasks: bool = False
    ) -> Dict[str, List[Workflow]]:
        pass

    @abstractmethod
    def remove_workflow(self, workflow_id: str):
        pass

    @abstractmethod
    def update_variables(self, workflow_id: str, variables: Optional[Dict[str, object]] = None) -> None:
        pass

    @abstractmethod
    def update_state(self, workflow_id: str, update_requesst: WorkflowStateUpdate,
                     wait_until_task_ref_names: Optional[List[str]] = None, wait_for_seconds: Optional[int] = None) -> WorkflowRun:
        pass
