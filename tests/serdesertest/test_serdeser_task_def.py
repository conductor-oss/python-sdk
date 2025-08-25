import json

import pytest

from conductor.client.adapters.models.schema_def_adapter import SchemaDefAdapter
from conductor.client.adapters.models.task_def_adapter import TaskDefAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


def create_task_def_from_json(json_dict):
    owner_app = json_dict.get("ownerApp")
    create_time = json_dict.get("createTime")
    update_time = json_dict.get("updateTime")
    created_by = json_dict.get("createdBy")
    updated_by = json_dict.get("updatedBy")
    name = json_dict.get("name")
    description = json_dict.get("description")
    retry_count = json_dict.get("retryCount")
    timeout_seconds = json_dict.get("timeoutSeconds")
    input_keys = json_dict.get("inputKeys")
    output_keys = json_dict.get("outputKeys")
    timeout_policy = json_dict.get("timeoutPolicy")
    retry_logic = json_dict.get("retryLogic")
    retry_delay_seconds = json_dict.get("retryDelaySeconds")
    response_timeout_seconds = json_dict.get("responseTimeoutSeconds")
    concurrent_exec_limit = json_dict.get("concurrentExecLimit")
    input_template = json_dict.get("inputTemplate")
    rate_limit_per_frequency = json_dict.get("rateLimitPerFrequency")
    rate_limit_frequency_in_seconds = json_dict.get("rateLimitFrequencyInSeconds")
    isolation_group_id = json_dict.get("isolationGroupId")
    execution_name_space = json_dict.get("executionNameSpace")
    owner_email = json_dict.get("ownerEmail")
    poll_timeout_seconds = json_dict.get("pollTimeoutSeconds")
    backoff_scale_factor = json_dict.get("backoffScaleFactor")
    input_schema_json = json_dict.get("inputSchema")
    input_schema_obj = None
    if input_schema_json:
        input_schema_obj = SchemaDefAdapter(
            name=input_schema_json.get("name"),
            version=input_schema_json.get("version"),
            type=input_schema_json.get("type"),
            data=input_schema_json.get("data"),
        )
    output_schema_json = json_dict.get("outputSchema")
    output_schema_obj = None
    if output_schema_json:
        output_schema_obj = SchemaDefAdapter(
            name=output_schema_json.get("name"),
            version=output_schema_json.get("version"),
            type=output_schema_json.get("type"),
            data=output_schema_json.get("data"),
        )
    enforce_schema = json_dict.get("enforceSchema", False)
    base_type = json_dict.get("baseType")
    total_timeout_seconds = json_dict.get("totalTimeoutSeconds")
    return TaskDefAdapter(
        owner_app=owner_app,
        create_time=create_time,
        update_time=update_time,
        created_by=created_by,
        updated_by=updated_by,
        name=name,
        description=description,
        retry_count=retry_count,
        timeout_seconds=timeout_seconds,
        input_keys=input_keys,
        output_keys=output_keys,
        timeout_policy=timeout_policy,
        retry_logic=retry_logic,
        retry_delay_seconds=retry_delay_seconds,
        response_timeout_seconds=response_timeout_seconds,
        concurrent_exec_limit=concurrent_exec_limit,
        input_template=input_template,
        rate_limit_per_frequency=rate_limit_per_frequency,
        rate_limit_frequency_in_seconds=rate_limit_frequency_in_seconds,
        isolation_group_id=isolation_group_id,
        execution_name_space=execution_name_space,
        owner_email=owner_email,
        poll_timeout_seconds=poll_timeout_seconds,
        backoff_scale_factor=backoff_scale_factor,
        input_schema=input_schema_obj,
        output_schema=output_schema_obj,
        enforce_schema=enforce_schema,
        base_type=base_type,
        total_timeout_seconds=total_timeout_seconds,
    )


def verify_task_def_fields(task_def, json_dict):
    assert task_def.owner_app == json_dict.get("ownerApp")
    assert task_def.create_time == json_dict.get("createTime")
    assert task_def.update_time == json_dict.get("updateTime")
    assert task_def.created_by == json_dict.get("createdBy")
    assert task_def.updated_by == json_dict.get("updatedBy")
    assert task_def.name == json_dict.get("name")
    assert task_def.description == json_dict.get("description")
    assert task_def.retry_count == json_dict.get("retryCount")
    assert task_def.timeout_seconds == json_dict.get("timeoutSeconds")
    if json_dict.get("inputKeys"):
        assert task_def.input_keys == json_dict.get("inputKeys")
    if json_dict.get("outputKeys"):
        assert task_def.output_keys == json_dict.get("outputKeys")
    assert task_def.timeout_policy == json_dict.get("timeoutPolicy")
    assert task_def.retry_logic == json_dict.get("retryLogic")
    assert task_def.retry_delay_seconds == json_dict.get("retryDelaySeconds")
    assert task_def.response_timeout_seconds == json_dict.get("responseTimeoutSeconds")
    assert task_def.concurrent_exec_limit == json_dict.get("concurrentExecLimit")
    if json_dict.get("inputTemplate"):
        assert task_def.input_template == json_dict.get("inputTemplate")
    assert task_def.rate_limit_per_frequency == json_dict.get("rateLimitPerFrequency")
    assert task_def.rate_limit_frequency_in_seconds == json_dict.get(
        "rateLimitFrequencyInSeconds"
    )
    assert task_def.isolation_group_id == json_dict.get("isolationGroupId")
    assert task_def.execution_name_space == json_dict.get("executionNameSpace")
    assert task_def.owner_email == json_dict.get("ownerEmail")
    assert task_def.poll_timeout_seconds == json_dict.get("pollTimeoutSeconds")
    assert task_def.backoff_scale_factor == json_dict.get("backoffScaleFactor")
    if json_dict.get("inputSchema"):
        assert task_def.input_schema is not None
        input_schema_json = json_dict.get("inputSchema")
        assert task_def.input_schema.name == input_schema_json.get("name")
        assert task_def.input_schema.type == input_schema_json.get("type")
    if json_dict.get("outputSchema"):
        assert task_def.output_schema is not None
        output_schema_json = json_dict.get("outputSchema")
        assert task_def.output_schema.name == output_schema_json.get("name")
        assert task_def.output_schema.type == output_schema_json.get("type")
    assert task_def.enforce_schema == json_dict.get("enforceSchema", False)
    assert task_def.base_type == json_dict.get("baseType")
    assert task_def.total_timeout_seconds == json_dict.get("totalTimeoutSeconds")


def compare_json_objects(original, result):
    key_mapping = {json_key: attr for (attr, json_key) in TaskDefAdapter.attribute_map.items()}
    for camel_key, orig_value in original.items():
        if camel_key not in key_mapping:
            continue
        snake_key = key_mapping[camel_key]
        result_value = result.get(snake_key)
        if camel_key in ["inputSchema", "outputSchema"]:
            if orig_value is not None:
                assert result_value is not None
                if orig_value and result_value:
                    assert orig_value.get("name") == result_value.get("name")
                    assert orig_value.get("type") == result_value.get("type")
            continue
        if isinstance(orig_value, list):
            assert orig_value == result_value
        elif isinstance(orig_value, dict):
            if orig_value:
                assert result_value is not None
        else:
            assert orig_value == result_value


@pytest.fixture
def server_json():
    return json.loads(JsonTemplateResolver.get_json_string("TaskDef"))


def test_task_def_serdes(server_json):
    task_def = create_task_def_from_json(server_json)
    verify_task_def_fields(task_def, server_json)
    result_json = task_def.to_dict()
    compare_json_objects(server_json, result_json)
