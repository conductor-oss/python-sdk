import json

import pytest

from conductor.client.adapters.models.start_workflow_request_adapter import StartWorkflowRequestAdapter
from conductor.client.adapters.models.tag_object_adapter import TagObjectAdapter
from conductor.client.adapters.models.workflow_schedule_adapter import WorkflowScheduleAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("WorkflowSchedule")
    return json.loads(server_json_str)


def test_workflow_schedule_serialization(server_json):
    # 1. Test deserialization from server JSON to SDK model
    schedule = WorkflowScheduleAdapter(
        name=server_json.get("name"),
        cron_expression=server_json.get("cronExpression"),
        run_catchup_schedule_instances=server_json.get("runCatchupScheduleInstances"),
        paused=server_json.get("paused"),
        schedule_start_time=server_json.get("scheduleStartTime"),
        schedule_end_time=server_json.get("scheduleEndTime"),
        create_time=server_json.get("createTime"),
        updated_time=server_json.get("updatedTime"),
        created_by=server_json.get("createdBy"),
        updated_by=server_json.get("updatedBy"),
        zone_id=server_json.get("zoneId"),
        paused_reason=server_json.get("pausedReason"),
        description=server_json.get("description"),
    )
    # Process special fields that require conversion: startWorkflowRequest and tags
    if "startWorkflowRequest" in server_json:
        start_req_json = server_json.get("startWorkflowRequest")
        if start_req_json:
            start_req = StartWorkflowRequestAdapter(
                name=start_req_json.get("name"),
                version=start_req_json.get("version"),
                correlation_id=start_req_json.get("correlationId"),
                input=start_req_json.get("input"),
            )
            schedule.start_workflow_request = start_req
    if "tags" in server_json:
        tags_json = server_json.get("tags")
        if tags_json:
            tags = []
            for tag_json in tags_json:
                tag = TagObjectAdapter(key=tag_json.get("key"), value=tag_json.get("value"))
                tags.append(tag)
            schedule.tags = tags
    # 2. Verify all fields are properly populated
    _verify_all_fields(schedule, server_json)
    # 3. Test serialization back to JSON
    serialized_json = schedule.to_dict()
    # 4. Verify the serialized JSON matches the original
    _verify_json_match(serialized_json, server_json)


def _verify_all_fields(schedule, json_data):
    # Verify simple fields
    assert schedule.name == json_data.get("name")
    assert schedule.cron_expression == json_data.get("cronExpression")
    assert schedule.run_catchup_schedule_instances == json_data.get(
        "runCatchupScheduleInstances"
    )
    assert schedule.paused == json_data.get("paused")
    assert schedule.schedule_start_time == json_data.get("scheduleStartTime")
    assert schedule.schedule_end_time == json_data.get("scheduleEndTime")
    assert schedule.create_time == json_data.get("createTime")
    assert schedule.updated_time == json_data.get("updatedTime")
    assert schedule.created_by == json_data.get("createdBy")
    assert schedule.updated_by == json_data.get("updatedBy")
    assert schedule.zone_id == json_data.get("zoneId")
    assert schedule.paused_reason == json_data.get("pausedReason")
    assert schedule.description == json_data.get("description")
    # Verify StartWorkflowRequest
    if (
        "startWorkflowRequest" in json_data
        and json_data["startWorkflowRequest"] is not None
    ):
        start_req_json = json_data["startWorkflowRequest"]
        start_req = schedule.start_workflow_request
        assert start_req
        assert start_req.name == start_req_json.get("name")
        assert start_req.version == start_req_json.get("version")
        assert start_req.correlation_id == start_req_json.get("correlationId")
        assert start_req.input == start_req_json.get("input")
    # Verify Tags
    if "tags" in json_data and json_data["tags"] is not None:
        tags_json = json_data["tags"]
        tags = schedule.tags
        assert tags
        assert len(tags) == len(tags_json)
        for i, tag_json in enumerate(tags_json):
            tag = tags[i]
            assert tag.key == tag_json.get("key")
            assert tag.value == tag_json.get("value")


def _verify_json_match(serialized_json, original_json):
    # Check field by field to handle camelCase to snake_case conversion
    assert serialized_json.get("name") == original_json.get("name")
    assert serialized_json.get("cron_expression") == original_json.get("cronExpression")
    assert serialized_json.get("run_catchup_schedule_instances") == original_json.get(
        "runCatchupScheduleInstances"
    )
    assert serialized_json.get("paused") == original_json.get("paused")
    assert serialized_json.get("schedule_start_time") == original_json.get(
        "scheduleStartTime"
    )
    assert serialized_json.get("schedule_end_time") == original_json.get(
        "scheduleEndTime"
    )
    assert serialized_json.get("create_time") == original_json.get("createTime")
    assert serialized_json.get("updated_time") == original_json.get("updatedTime")
    assert serialized_json.get("created_by") == original_json.get("createdBy")
    assert serialized_json.get("updated_by") == original_json.get("updatedBy")
    assert serialized_json.get("zone_id") == original_json.get("zoneId")
    assert serialized_json.get("paused_reason") == original_json.get("pausedReason")
    assert serialized_json.get("description") == original_json.get("description")
    # Check StartWorkflowRequest
    if (
        "startWorkflowRequest" in original_json
        and original_json["startWorkflowRequest"] is not None
    ):
        orig_req = original_json["startWorkflowRequest"]
        serial_req = serialized_json.get("start_workflow_request")
        assert serial_req
        assert serial_req.get("name") == orig_req.get("name")
        assert serial_req.get("version") == orig_req.get("version")
        assert serial_req.get("correlation_id") == orig_req.get("correlationId")
        assert serial_req.get("input") == orig_req.get("input")
    # Check Tags
    if "tags" in original_json and original_json["tags"] is not None:
        orig_tags = original_json["tags"]
        serial_tags = serialized_json.get("tags")
        assert serial_tags
        assert len(serial_tags) == len(orig_tags)
        for i, orig_tag in enumerate(orig_tags):
            serial_tag = serial_tags[i]
            assert serial_tag.get("key") == orig_tag.get("key")
            assert serial_tag.get("value") == orig_tag.get("value")
