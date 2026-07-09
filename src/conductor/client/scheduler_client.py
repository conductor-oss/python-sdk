from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import Optional, List
from conductor.client.http.models.workflow_schedule import WorkflowSchedule
from conductor.client.http.models.save_schedule_request import SaveScheduleRequest
from conductor.client.http.models.search_result_workflow_schedule_execution_model import \
    SearchResultWorkflowScheduleExecutionModel
from conductor.client.orkes.models.metadata_tag import MetadataTag

logger = logging.getLogger(__name__)


class SchedulerClient(ABC):
    @abstractmethod
    def save_schedule(self, save_schedule_request: SaveScheduleRequest):
        pass

    @abstractmethod
    def get_schedule(self, name: str) -> Optional[WorkflowSchedule]:
        pass

    @abstractmethod
    def get_all_schedules(self, workflow_name: Optional[str] = None) -> List[WorkflowSchedule]:
        pass

    @abstractmethod
    def get_next_few_schedule_execution_times(self,
                                              cron_expression: str,
                                              schedule_start_time: Optional[int] = None,
                                              schedule_end_time: Optional[int] = None,
                                              limit: Optional[int] = None,
                                              ) -> List[int]:
        pass

    @abstractmethod
    def delete_schedule(self, name: str):
        pass

    @abstractmethod
    def pause_schedule(self, name: str, reason: Optional[str] = None):
        pass

    @abstractmethod
    def pause_all_schedules(self):
        pass

    @abstractmethod
    def resume_schedule(self, name: str):
        pass

    @abstractmethod
    def resume_all_schedules(self):
        pass

    @abstractmethod
    def search_schedule_executions(self,
                                   start: Optional[int] = None,
                                   size: Optional[int] = None,
                                   sort: Optional[str] = None,
                                   free_text: Optional[str] = None,
                                   query: Optional[str] = None,
                                   ) -> SearchResultWorkflowScheduleExecutionModel:
        pass

    @abstractmethod
    def requeue_all_execution_records(self):
        pass

    @abstractmethod
    def set_scheduler_tags(self, tags: List[MetadataTag], name: str):
        pass

    @abstractmethod
    def get_scheduler_tags(self, name: str) -> List[MetadataTag]:
        pass

    @abstractmethod
    def delete_scheduler_tags(self, tags: List[MetadataTag], name: str) -> List[MetadataTag]:
        pass

    # ── schedule lifecycle (concrete domain surface) ─────────────────────
    #
    # Implemented over the abstract endpoint methods above, so every
    # SchedulerClient implementation gets them for free. Reads/writes/lists
    # have NO domain twins by design — get_schedule/save_schedule/
    # get_all_schedules are the source of truth. These methods raise the
    # typed errors from conductor.client.ai.schedule_errors (ScheduleNotFound,
    # InvalidCronExpression, ...) instead of raw ApiException.
    # The conductor.client.ai imports are deliberately lazy: this module is on
    # virtually every SDK program's import path and must not pull the agent
    # surface (httpx etc.) at import time.

    def pause(self, wire_name: str, reason: Optional[str] = None) -> None:
        """Pause one schedule by wire name (typed errors; ``reason`` is OSS-only)."""
        from conductor.client.ai.schedule import _translate

        try:
            if reason is None:
                self.pause_schedule(wire_name)
            else:
                self.pause_schedule(wire_name, reason=reason)
        except Exception as exc:  # noqa: BLE001
            raise _translate(exc) from exc

    def resume(self, wire_name: str) -> None:
        """Resume one schedule by wire name (typed errors)."""
        from conductor.client.ai.schedule import _translate

        try:
            self.resume_schedule(wire_name)
        except Exception as exc:  # noqa: BLE001
            raise _translate(exc) from exc

    def delete(self, wire_name: str) -> None:
        """Delete one schedule by wire name (typed errors)."""
        from conductor.client.ai.schedule import _translate

        try:
            self.delete_schedule(wire_name)
        except Exception as exc:  # noqa: BLE001
            raise _translate(exc) from exc

    def preview_next(
        self, cron: str, n: int = 5, start_at: Optional[int] = None, end_at: Optional[int] = None
    ) -> List[int]:
        """Next ``n`` epoch-ms fire times for ``cron`` (typed errors)."""
        from conductor.client.ai.schedule import _translate

        try:
            times = self.get_next_few_schedule_execution_times(
                cron_expression=cron,
                schedule_start_time=start_at,
                schedule_end_time=end_at,
                limit=n,
            )
            return list(times) if times else []
        except Exception as exc:  # noqa: BLE001
            raise _translate(exc) from exc

    def run_now(self, info: "ScheduleInfo") -> str:
        """Fire the schedule's agent once with its stored input. Returns execution id."""
        from conductor.client.ai.schedule import _translate
        from conductor.client.http.models.start_workflow_request import StartWorkflowRequest

        req = StartWorkflowRequest(name=info.agent, input=dict(info.input))
        try:
            return self._start_workflow(req)
        except Exception as exc:  # noqa: BLE001
            raise _translate(exc) from exc

    def reconcile(self, agent_name: str, desired: Optional[List["Schedule"]]) -> None:
        """Apply the declarative tri-state semantics from spec §5.1:

        - ``desired is None``: no-op
        - ``desired == []``: delete every schedule whose workflow == agent_name
        - ``desired == [...]``: upsert listed, delete others scoped to this agent
        """
        from conductor.client.ai.schedule import (
            _check_unique_names,
            _list_infos,
            _prefix,
            _to_save_request,
            _translate,
        )

        if desired is None:
            return
        _check_unique_names(desired)
        existing = _list_infos(self, agent_name)
        existing_wire_by_short = {info.short_name: info.name for info in existing}
        desired_short = {s.name for s in desired}

        for short, wire in existing_wire_by_short.items():
            if short not in desired_short:
                logger.info("Pruning schedule %s for agent %s", wire, agent_name)
                self.delete(wire)

        for s in desired:
            logger.info(
                "Upserting schedule %s for agent %s", _prefix(agent_name, s.name), agent_name
            )
            try:
                self.save_schedule(_to_save_request(s, agent_name))
            except Exception as exc:  # noqa: BLE001
                raise _translate(exc) from exc

    def _start_workflow(self, request) -> str:
        """Start a workflow from ``request`` and return the execution id.

        ``run_now`` is the only lifecycle operation needing a capability outside
        the scheduler vocabulary; concrete clients that can start workflows
        override this (``OrkesSchedulerClient`` does).
        """
        raise NotImplementedError(
            "run_now requires a workflow-start capability; use OrkesSchedulerClient "
            "or override _start_workflow(request) -> str on your SchedulerClient."
        )
