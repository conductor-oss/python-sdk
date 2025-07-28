import json

import pytest

from conductor.client.http.models.task_exec_log import TaskExecLog
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def server_json():
    server_json_str = JsonTemplateResolver.get_json_string("TaskExecLog")
    return json.loads(server_json_str)


def test_task_exec_log_serdeser(server_json):
    """
    Test serialization and deserialization of TaskExecLog
    """
    # 1. Deserialize JSON into SDK model object
    task_exec_log = TaskExecLog(
        log=server_json.get("log"),
        task_id=server_json.get("taskId"),
        created_time=server_json.get("createdTime"),
    )
    # 2. Verify all fields are properly populated
    assert server_json.get("log") == task_exec_log.log
    assert server_json.get("taskId") == task_exec_log.task_id
    assert server_json.get("createdTime") == task_exec_log.created_time
    # 3. Serialize SDK model back to dictionary
    task_exec_log_dict = task_exec_log.to_dict()
    # 4. Verify serialized dictionary matches original JSON
    # Check the original JSON attributes are in the serialized dictionary
    assert server_json.get("log") == task_exec_log_dict.get("log")
    # Handle camelCase to snake_case transformations
    assert server_json.get("taskId") == task_exec_log_dict.get("task_id")
    assert server_json.get("createdTime") == task_exec_log_dict.get("created_time")
    # Verify no data is lost (all keys from original JSON exist in serialized output)
    for key in server_json:
        if key == "taskId":
            assert "task_id" in task_exec_log_dict
        elif key == "createdTime":
            assert "created_time" in task_exec_log_dict
        else:
            assert key in task_exec_log_dict
