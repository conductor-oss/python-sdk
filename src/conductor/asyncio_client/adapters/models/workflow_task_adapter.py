from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field
from typing_extensions import Self

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

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of WorkflowTask from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "asyncComplete": obj.get("asyncComplete"),
                "cacheConfig": (
                    CacheConfigAdapter.from_dict(obj["cacheConfig"])
                    if obj.get("cacheConfig") is not None
                    else None
                ),
                "caseExpression": obj.get("caseExpression"),
                "caseValueParam": obj.get("caseValueParam"),
                "decisionCases": dict(
                    (
                        _k,
                        (
                            [WorkflowTaskAdapter.from_dict(_item) for _item in _v]
                            if _v is not None
                            else None
                        ),
                    )
                    for _k, _v in obj.get("decisionCases", {}).items()
                ),
                "defaultCase": (
                    [WorkflowTaskAdapter.from_dict(_item) for _item in obj["defaultCase"]]
                    if obj.get("defaultCase") is not None
                    else None
                ),
                "defaultExclusiveJoinTask": obj.get("defaultExclusiveJoinTask"),
                "description": obj.get("description"),
                "dynamicForkJoinTasksParam": obj.get("dynamicForkJoinTasksParam"),
                "dynamicForkTasksInputParamName": obj.get(
                    "dynamicForkTasksInputParamName"
                ),
                "dynamicForkTasksParam": obj.get("dynamicForkTasksParam"),
                "dynamicTaskNameParam": obj.get("dynamicTaskNameParam"),
                "evaluatorType": obj.get("evaluatorType"),
                "expression": obj.get("expression"),
                "forkTasks": (
                    [
                        [WorkflowTaskAdapter.from_dict(_inner_item) for _inner_item in _item]
                        for _item in obj["forkTasks"]
                    ]
                    if obj.get("forkTasks") is not None
                    else None
                ),
                "inputParameters": obj.get("inputParameters"),
                "joinOn": obj.get("joinOn"),
                "joinStatus": obj.get("joinStatus"),
                "loopCondition": obj.get("loopCondition"),
                "loopOver": (
                    [WorkflowTaskAdapter.from_dict(_item) for _item in obj["loopOver"]]
                    if obj.get("loopOver") is not None
                    else None
                ),
                "name": obj.get("name"),
                "onStateChange": dict(
                    (
                        _k,
                        (
                            [StateChangeEventAdapter.from_dict(_item) for _item in _v]
                            if _v is not None
                            else None
                        ),
                    )
                    for _k, _v in obj.get("onStateChange", {}).items()
                ),
                "optional": obj.get("optional"),
                "permissive": obj.get("permissive"),
                "rateLimited": obj.get("rateLimited"),
                "retryCount": obj.get("retryCount"),
                "scriptExpression": obj.get("scriptExpression"),
                "sink": obj.get("sink"),
                "startDelay": obj.get("startDelay"),
                "subWorkflowParam": (
                    SubWorkflowParamsAdapter.from_dict(obj["subWorkflowParam"])
                    if obj.get("subWorkflowParam") is not None
                    else None
                ),
                "taskDefinition": (
                    TaskDefAdapter.from_dict(obj["taskDefinition"])
                    if obj.get("taskDefinition") is not None
                    else None
                ),
                "taskReferenceName": obj.get("taskReferenceName"),
                "type": obj.get("type"),
                "workflowTaskType": obj.get("workflowTaskType"),
            }
        )
        return _obj
