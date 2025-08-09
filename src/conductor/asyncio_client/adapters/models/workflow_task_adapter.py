from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from conductor.asyncio_client.adapters.models.cache_config_adapter import (
    CacheConfigAdapter,
)
from conductor.asyncio_client.adapters.models.state_change_event_adapter import (
    StateChangeEventAdapter,
)
from conductor.asyncio_client.adapters.models.sub_workflow_params_adapter import (
    SubWorkflowParamsAdapter,
)
from conductor.asyncio_client.adapters.models.task_def_adapter import TaskDefAdapter
from conductor.asyncio_client.http.models import WorkflowTask


class WorkflowTaskAdapter(WorkflowTask):
    cache_config: Optional[CacheConfigAdapter] = Field(
        default=None, alias="cacheConfig"
    )
    default_case: Optional[List[WorkflowTaskAdapter]] = Field(
        default=None, alias="defaultCase"
    )
    fork_tasks: Optional[List[List[WorkflowTaskAdapter]]] = Field(
        default=None, alias="forkTasks"
    )
    input_parameters: Optional[Dict[str, Any]] = Field(
        default=None, alias="inputParameters"
    )
    loop_over: Optional[List[WorkflowTaskAdapter]] = Field(
        default=None, alias="loopOver"
    )
    on_state_change: Optional[Dict[str, List[StateChangeEventAdapter]]] = Field(
        default=None, alias="onStateChange"
    )
    sub_workflow_param: Optional[SubWorkflowParamsAdapter] = Field(
        default=None, alias="subWorkflowParam"
    )
    task_definition: Optional[TaskDefAdapter] = Field(
        default=None, alias="taskDefinition"
    )
    decision_cases: Optional[Dict[str, List[WorkflowTaskAdapter]]] = Field(
        default=None, alias="decisionCases"
    )
