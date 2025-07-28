import json

import pytest

from conductor.client.http.models.workflow_schedule_execution_model import (
    WorkflowScheduleExecutionModel,
)
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string(
        "WorkflowScheduleExecutionModel"
    )
    return json.loads(server_json_str)


def test_workflow_schedule_execution_model_serdes(server_json):
    # 1. Deserialize JSON into model object
    model = WorkflowScheduleExecutionModel(
        execution_id=server_json.get("executionId"),
        schedule_name=server_json.get("scheduleName"),
        scheduled_time=server_json.get("scheduledTime"),
        execution_time=server_json.get("executionTime"),
        workflow_name=server_json.get("workflowName"),
        workflow_id=server_json.get("workflowId"),
        reason=server_json.get("reason"),
        stack_trace=server_json.get("stackTrace"),
        start_workflow_request=server_json.get("startWorkflowRequest"),
        state=server_json.get("state"),
        zone_id=server_json.get("zoneId"),
        org_id=server_json.get("orgId"),
    )
    # 2. Verify all fields are properly populated
    assert model.execution_id == server_json.get("executionId")
    assert model.schedule_name == server_json.get("scheduleName")
    assert model.scheduled_time == server_json.get("scheduledTime")
    assert model.execution_time == server_json.get("executionTime")
    assert model.workflow_name == server_json.get("workflowName")
    assert model.workflow_id == server_json.get("workflowId")
    assert model.reason == server_json.get("reason")
    assert model.stack_trace == server_json.get("stackTrace")
    assert model.start_workflow_request == server_json.get("startWorkflowRequest")
    assert model.state == server_json.get("state")
    assert model.zone_id == server_json.get("zoneId")
    assert model.org_id == server_json.get("orgId")
    # Check that enum values are correctly handled
    if model.state:
        assert model.state in ["POLLED", "FAILED", "EXECUTED"]
    # 3. Serialize model back to dict
    model_dict = model.to_dict()
    # 4. Compare with original JSON to ensure no data loss
    # Handle camelCase to snake_case transformations
    assert model_dict.get("execution_id") == server_json.get("executionId")
    assert model_dict.get("schedule_name") == server_json.get("scheduleName")
    assert model_dict.get("scheduled_time") == server_json.get("scheduledTime")
    assert model_dict.get("execution_time") == server_json.get("executionTime")
    assert model_dict.get("workflow_name") == server_json.get("workflowName")
    assert model_dict.get("workflow_id") == server_json.get("workflowId")
    assert model_dict.get("reason") == server_json.get("reason")
    assert model_dict.get("stack_trace") == server_json.get("stackTrace")
    assert model_dict.get("start_workflow_request") == server_json.get(
        "startWorkflowRequest"
    )
    assert model_dict.get("state") == server_json.get("state")
    assert model_dict.get("zone_id") == server_json.get("zoneId")
    assert model_dict.get("org_id") == server_json.get("orgId")
    # Additional validation for complex structures (if any were present)
    if isinstance(model.start_workflow_request, dict):
        assert model_dict.get("start_workflow_request") == server_json.get(
            "startWorkflowRequest"
        )
