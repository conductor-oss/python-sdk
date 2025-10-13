from unittest.mock import Mock

from conductor.shared.worker.task_definition_helper import apply_task_options_to_task_def
from conductor.shared.worker.task_options import TaskOptions


def test_apply_task_options_with_none():
    task_def = Mock()
    
    apply_task_options_to_task_def(task_def, None)
    
    task_def.assert_not_called()


def test_apply_all_task_options():
    task_def = Mock()
    task_options = TaskOptions(
        timeout_seconds=3600,
        response_timeout_seconds=300,
        poll_timeout_seconds=120,
        retry_count=5,
        retry_logic="EXPONENTIAL_BACKOFF",
        retry_delay_seconds=10,
        backoff_scale_factor=3,
        rate_limit_per_frequency=100,
        rate_limit_frequency_in_seconds=60,
        concurrent_exec_limit=10,
        timeout_policy="TIME_OUT_WF",
        owner_email="test@example.com",
        description="Test task definition"
    )
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.timeout_seconds == 3600
    assert task_def.response_timeout_seconds == 300
    assert task_def.poll_timeout_seconds == 120
    assert task_def.retry_count == 5
    assert task_def.retry_logic == "EXPONENTIAL_BACKOFF"
    assert task_def.retry_delay_seconds == 10
    assert task_def.backoff_scale_factor == 3
    assert task_def.rate_limit_per_frequency == 100
    assert task_def.rate_limit_frequency_in_seconds == 60
    assert task_def.concurrent_exec_limit == 10
    assert task_def.timeout_policy == "TIME_OUT_WF"
    assert task_def.owner_email == "test@example.com"
    assert task_def.description == "Test task definition"


def test_apply_partial_task_options():
    task_def = Mock()
    task_def.timeout_seconds = None
    task_def.retry_count = None
    task_def.description = None
    
    task_options = TaskOptions(
        timeout_seconds=120,
        retry_count=3,
        description="Partial test"
    )
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.timeout_seconds == 120
    assert task_def.retry_count == 3
    assert task_def.description == "Partial test"


def test_apply_timeout_options():
    task_def = Mock()
    task_options = TaskOptions(
        timeout_seconds=3600,
        response_timeout_seconds=300,
        poll_timeout_seconds=120
    )
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.timeout_seconds == 3600
    assert task_def.response_timeout_seconds == 300
    assert task_def.poll_timeout_seconds == 120


def test_apply_retry_options():
    task_def = Mock()
    task_options = TaskOptions(
        retry_count=5,
        retry_logic="LINEAR_BACKOFF",
        retry_delay_seconds=10,
        backoff_scale_factor=2
    )
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.retry_count == 5
    assert task_def.retry_logic == "LINEAR_BACKOFF"
    assert task_def.retry_delay_seconds == 10
    assert task_def.backoff_scale_factor == 2


def test_apply_rate_limit_options():
    task_def = Mock()
    task_options = TaskOptions(
        rate_limit_per_frequency=100,
        rate_limit_frequency_in_seconds=60,
        concurrent_exec_limit=10
    )
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.rate_limit_per_frequency == 100
    assert task_def.rate_limit_frequency_in_seconds == 60
    assert task_def.concurrent_exec_limit == 10


def test_apply_timeout_policy():
    task_def = Mock()
    task_options = TaskOptions(timeout_policy="RETRY")
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.timeout_policy == "RETRY"


def test_apply_owner_email():
    task_def = Mock()
    task_options = TaskOptions(owner_email="owner@example.com")
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.owner_email == "owner@example.com"


def test_apply_description():
    task_def = Mock()
    task_options = TaskOptions(description="Test description")
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.description == "Test description"


def test_only_sets_non_none_values():
    task_def = Mock()
    task_def.timeout_seconds = 100
    task_def.retry_count = 2
    
    task_options = TaskOptions(
        timeout_seconds=200,
        retry_count=None
    )
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.timeout_seconds == 200
    assert task_def.retry_count == 2


def test_overwrites_existing_values():
    task_def = Mock()
    task_def.timeout_seconds = 100
    task_def.retry_count = 2
    task_def.description = "Old description"
    
    task_options = TaskOptions(
        timeout_seconds=3600,
        retry_count=5,
        description="New description"
    )
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.timeout_seconds == 3600
    assert task_def.retry_count == 5
    assert task_def.description == "New description"


def test_apply_fixed_retry_logic():
    task_def = Mock()
    task_options = TaskOptions(
        retry_count=3,
        retry_logic="FIXED",
        retry_delay_seconds=5
    )
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.retry_count == 3
    assert task_def.retry_logic == "FIXED"
    assert task_def.retry_delay_seconds == 5


def test_apply_linear_backoff_retry_logic():
    task_def = Mock()
    task_options = TaskOptions(
        retry_count=3,
        retry_logic="LINEAR_BACKOFF",
        retry_delay_seconds=5
    )
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.retry_count == 3
    assert task_def.retry_logic == "LINEAR_BACKOFF"
    assert task_def.retry_delay_seconds == 5


def test_apply_exponential_backoff_retry_logic():
    task_def = Mock()
    task_options = TaskOptions(
        retry_count=5,
        retry_logic="EXPONENTIAL_BACKOFF",
        retry_delay_seconds=2,
        backoff_scale_factor=3
    )
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.retry_count == 5
    assert task_def.retry_logic == "EXPONENTIAL_BACKOFF"
    assert task_def.retry_delay_seconds == 2
    assert task_def.backoff_scale_factor == 3


def test_apply_time_out_wf_policy():
    task_def = Mock()
    task_options = TaskOptions(timeout_policy="TIME_OUT_WF")
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.timeout_policy == "TIME_OUT_WF"


def test_apply_alert_only_policy():
    task_def = Mock()
    task_options = TaskOptions(timeout_policy="ALERT_ONLY")
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.timeout_policy == "ALERT_ONLY"


def test_apply_retry_timeout_policy():
    task_def = Mock()
    task_options = TaskOptions(timeout_policy="RETRY")
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.timeout_policy == "RETRY"


def test_apply_zero_values():
    task_def = Mock()
    task_options = TaskOptions(
        timeout_seconds=0,
        retry_count=0,
        rate_limit_per_frequency=0,
        concurrent_exec_limit=0
    )
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.timeout_seconds == 0
    assert task_def.retry_count == 0
    assert task_def.rate_limit_per_frequency == 0
    assert task_def.concurrent_exec_limit == 0


def test_apply_with_existing_task_def_values():
    task_def = Mock()
    task_def.timeout_seconds = 100
    task_def.response_timeout_seconds = 50
    task_def.retry_count = 1
    task_def.description = "Existing"
    
    task_options = TaskOptions(
        timeout_seconds=200
    )
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.timeout_seconds == 200
    assert task_def.response_timeout_seconds == 50
    assert task_def.retry_count == 1
    assert task_def.description == "Existing"


def test_apply_empty_task_options():
    task_def = Mock()
    task_def.timeout_seconds = None
    task_def.retry_count = None
    
    task_options = TaskOptions()
    
    apply_task_options_to_task_def(task_def, task_options)
    
    assert task_def.timeout_seconds is None
    assert task_def.retry_count is None

