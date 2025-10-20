from __future__ import annotations

from typing import Optional

from conductor.client.codegen.models.workflow_schedule import WorkflowSchedule


class WorkflowScheduleAdapter(WorkflowSchedule):
    def __init__(
        self,
        name: Optional[str] = None,
        cron_expression: Optional[str] = None,
        run_catchup_schedule_instances: Optional[bool] = None,
        paused: Optional[bool] = None,
        start_workflow_request=None,
        schedule_start_time: Optional[int] = None,
        schedule_end_time: Optional[int] = None,
        create_time: Optional[int] = None,
        updated_time: Optional[int] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
        paused_reason: Optional[str] = None,
        description: Optional[str] = None,
        tags=None,
        zone_id=None,
    ):
        self._create_time = None
        self._created_by = None
        self._cron_expression = None
        self._description = None
        self._name = None
        self._paused = None
        self._paused_reason = None
        self._run_catchup_schedule_instances = None
        self._schedule_end_time = None
        self._schedule_start_time = None
        self._start_workflow_request = None
        self._tags = None
        self._updated_by = None
        self._updated_time = None
        self._zone_id = None
        self.discriminator = None
        if create_time is not None:
            self.create_time = create_time
        if created_by is not None:
            self.created_by = created_by
        if cron_expression is not None:
            self.cron_expression = cron_expression
        if description is not None:
            self.description = description
        if name is not None:
            self.name = name
        if paused is not None:
            self.paused = paused
        if paused_reason is not None:
            self.paused_reason = paused_reason
        if run_catchup_schedule_instances is not None:
            self.run_catchup_schedule_instances = run_catchup_schedule_instances
        if schedule_end_time is not None:
            self.schedule_end_time = schedule_end_time
        if schedule_start_time is not None:
            self.schedule_start_time = schedule_start_time
        if start_workflow_request is not None:
            self.start_workflow_request = start_workflow_request
        if tags is not None:
            self.tags = tags
        if updated_by is not None:
            self.updated_by = updated_by
        if updated_time is not None:
            self.updated_time = updated_time
        if zone_id is not None:
            self.zone_id = zone_id
