import json

import pytest

from conductor.client.adapters.models.save_schedule_request_adapter import SaveScheduleRequestAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("SaveScheduleRequest")
    return json.loads(server_json_str)


def verify_fields(model, json_data):
    assert model.name == json_data.get("name"), "Field 'name' mismatch"
    assert model.cron_expression == json_data.get(
        "cronExpression"
    ), "Field 'cron_expression' mismatch"
    assert model.run_catchup_schedule_instances == json_data.get(
        "runCatchupScheduleInstances"
    ), "Field 'run_catchup_schedule_instances' mismatch"
    assert model.paused == json_data.get("paused"), "Field 'paused' mismatch"
    if json_data.get("startWorkflowRequest") is not None:
        assert (
            model.start_workflow_request is not None
        ), "Field 'start_workflow_request' should not be None"
    assert model.created_by == json_data.get("createdBy"), "Field 'created_by' mismatch"
    assert model.updated_by == json_data.get("updatedBy"), "Field 'updated_by' mismatch"
    assert model.schedule_start_time == json_data.get(
        "scheduleStartTime"
    ), "Field 'schedule_start_time' mismatch"
    assert model.schedule_end_time == json_data.get(
        "scheduleEndTime"
    ), "Field 'schedule_end_time' mismatch"
    assert model.zone_id == json_data.get("zoneId"), "Field 'zone_id' mismatch"
    assert model.description == json_data.get(
        "description"
    ), "Field 'description' mismatch"


def verify_json_match(result_json, original_json):
    field_mapping = {
        "name": "name",
        "cron_expression": "cronExpression",
        "run_catchup_schedule_instances": "runCatchupScheduleInstances",
        "paused": "paused",
        "start_workflow_request": "startWorkflowRequest",
        "created_by": "createdBy",
        "updated_by": "updatedBy",
        "schedule_start_time": "scheduleStartTime",
        "schedule_end_time": "scheduleEndTime",
        "zone_id": "zoneId",
        "description": "description",
    }
    for py_field, json_field in field_mapping.items():
        if py_field in result_json and json_field in original_json:
            assert (
                result_json[py_field] == original_json[json_field]
            ), f"Field mismatch: {py_field}/{json_field}"


def test_save_schedule_request_serde(server_json):
    request = SaveScheduleRequestAdapter(
        name=server_json.get("name"),
        cron_expression=server_json.get("cronExpression"),
        run_catchup_schedule_instances=server_json.get("runCatchupScheduleInstances"),
        paused=server_json.get("paused"),
        start_workflow_request=server_json.get("startWorkflowRequest"),
        created_by=server_json.get("createdBy"),
        updated_by=server_json.get("updatedBy"),
        schedule_start_time=server_json.get("scheduleStartTime"),
        schedule_end_time=server_json.get("scheduleEndTime"),
        zone_id=server_json.get("zoneId"),
        description=server_json.get("description"),
    )
    verify_fields(request, server_json)
    result_json = request.to_dict()
    verify_json_match(result_json, server_json)
