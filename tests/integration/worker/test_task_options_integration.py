import uuid

from conductor.client.http.models.task_def import TaskDefAdapter as TaskDef
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.shared.worker.task_definition_helper import apply_task_options_to_task_def
from conductor.shared.worker.task_options import TaskOptions, task_options, get_task_options


def test_task_options_decorator_basic_integration(conductor_configuration, cleanup_enabled):
    metadata_client = OrkesMetadataClient(conductor_configuration)
    test_suffix = str(uuid.uuid4())[:8]
    task_name = f"task_options_basic_{test_suffix}"

    try:
        @task_options(
            timeout_seconds=3600,
            response_timeout_seconds=120,
            retry_count=3,
            retry_logic="FIXED",
            retry_delay_seconds=5
        )
        def test_task(_task_input):
            return {"result": "success"}

        task_opts = get_task_options(test_task)
        assert task_opts is not None
        assert task_opts.timeout_seconds == 3600
        assert task_opts.response_timeout_seconds == 120
        assert task_opts.retry_count == 3
        assert task_opts.retry_logic == "FIXED"
        assert task_opts.retry_delay_seconds == 5

        task_def = TaskDef(name=task_name)
        apply_task_options_to_task_def(task_def, task_opts)

        assert task_def.timeout_seconds == 3600
        assert task_def.response_timeout_seconds == 120
        assert task_def.retry_count == 3
        assert task_def.retry_logic == "FIXED"
        assert task_def.retry_delay_seconds == 5

        metadata_client.register_task_def(task_def)

        retrieved_task = metadata_client.get_task_def(task_name)
        assert retrieved_task["name"] == task_name
        assert retrieved_task["timeoutSeconds"] == 3600
        assert retrieved_task["responseTimeoutSeconds"] == 120
        assert retrieved_task["retryCount"] == 3
        assert retrieved_task["retryLogic"] == "FIXED"
        assert retrieved_task["retryDelaySeconds"] == 5

    finally:
        if cleanup_enabled:
            try:
                metadata_client.unregister_task_def(task_name)
            except Exception:
                pass


def test_task_options_decorator_all_parameters(conductor_configuration, cleanup_enabled):
    metadata_client = OrkesMetadataClient(conductor_configuration)
    test_suffix = str(uuid.uuid4())[:8]
    task_name = f"task_options_all_params_{test_suffix}"

    try:
        @task_options(
            timeout_seconds=180,
            response_timeout_seconds=90,
            poll_timeout_seconds=45,
            retry_count=5,
            retry_logic="EXPONENTIAL_BACKOFF",
            retry_delay_seconds=10,
            backoff_scale_factor=2,
            rate_limit_per_frequency=100,
            rate_limit_frequency_in_seconds=30,
            concurrent_exec_limit=10,
            timeout_policy="RETRY",
            description="Integration test task with all options"
        )
        def test_task_all_options(_task_input):
            return {"result": "success"}

        task_opts = get_task_options(test_task_all_options)
        assert task_opts is not None

        task_def = TaskDef(name=task_name)
        apply_task_options_to_task_def(task_def, task_opts)

        assert task_def.timeout_seconds == 180
        assert task_def.response_timeout_seconds == 90
        assert task_def.poll_timeout_seconds == 45
        assert task_def.retry_count == 5
        assert task_def.retry_logic == "EXPONENTIAL_BACKOFF"
        assert task_def.retry_delay_seconds == 10
        assert task_def.backoff_scale_factor == 2
        assert task_def.rate_limit_per_frequency == 100
        assert task_def.rate_limit_frequency_in_seconds == 30
        assert task_def.concurrent_exec_limit == 10
        assert task_def.timeout_policy == "RETRY"
        assert task_def.description == "Integration test task with all options"

        metadata_client.register_task_def(task_def)

        retrieved_task = metadata_client.get_task_def(task_name)
        assert retrieved_task["name"] == task_name
        assert retrieved_task["timeoutSeconds"] == 180
        assert retrieved_task["responseTimeoutSeconds"] == 90
        assert retrieved_task["pollTimeoutSeconds"] == 45
        assert retrieved_task["retryCount"] == 5
        assert retrieved_task["retryLogic"] == "EXPONENTIAL_BACKOFF"
        assert retrieved_task["retryDelaySeconds"] == 10
        assert retrieved_task["backoffScaleFactor"] == 2
        assert retrieved_task["rateLimitPerFrequency"] == 100
        assert retrieved_task["rateLimitFrequencyInSeconds"] == 30
        assert retrieved_task["concurrentExecLimit"] == 10
        assert retrieved_task["timeoutPolicy"] == "RETRY"
        assert retrieved_task["description"] == "Integration test task with all options"

    finally:
        if cleanup_enabled:
            try:
                metadata_client.unregister_task_def(task_name)
            except Exception:
                pass


def test_task_options_decorator_partial_parameters(conductor_configuration, cleanup_enabled):
    metadata_client = OrkesMetadataClient(conductor_configuration)
    test_suffix = str(uuid.uuid4())[:8]
    task_name = f"task_options_partial_{test_suffix}"

    try:
        @task_options(
            timeout_seconds=3600,
            response_timeout_seconds=60,
            retry_count=2,
            owner_email="partial@example.com"
        )
        def test_task_partial(_task_input):
            return {"result": "success"}

        task_opts = get_task_options(test_task_partial)
        assert task_opts is not None
        assert task_opts.timeout_seconds == 3600
        assert task_opts.response_timeout_seconds == 60
        assert task_opts.retry_count == 2
        assert task_opts.retry_logic is None

        task_def = TaskDef(name=task_name, description="Base description")
        apply_task_options_to_task_def(task_def, task_opts)

        assert task_def.timeout_seconds == 3600
        assert task_def.response_timeout_seconds == 60
        assert task_def.retry_count == 2
        assert task_def.description == "Base description"

        metadata_client.register_task_def(task_def)

        retrieved_task = metadata_client.get_task_def(task_name)
        assert retrieved_task["name"] == task_name
        assert retrieved_task["timeoutSeconds"] == 3600
        assert retrieved_task["responseTimeoutSeconds"] == 60
        assert retrieved_task["retryCount"] == 2

    finally:
        if cleanup_enabled:
            try:
                metadata_client.unregister_task_def(task_name)
            except Exception:
                pass


def test_task_options_retry_policies(conductor_configuration, cleanup_enabled):
    metadata_client = OrkesMetadataClient(conductor_configuration)
    test_suffix = str(uuid.uuid4())[:8]
    retry_policies = ["FIXED", "LINEAR_BACKOFF", "EXPONENTIAL_BACKOFF"]

    task_names = []
    try:
        for retry_policy in retry_policies:
            task_name = f"task_retry_{retry_policy.lower()}_{test_suffix}"
            task_names.append(task_name)

            task_opts = TaskOptions(
                retry_count=3,
                retry_logic=retry_policy,
                retry_delay_seconds=5
            )

            task_def = TaskDef(name=task_name)
            apply_task_options_to_task_def(task_def, task_opts)

            metadata_client.register_task_def(task_def)

            retrieved_task = metadata_client.get_task_def(task_name)
            assert retrieved_task["retryLogic"] == retry_policy
            assert retrieved_task["retryCount"] == 3
            assert retrieved_task["retryDelaySeconds"] == 5

    finally:
        if cleanup_enabled:
            for task_name in task_names:
                try:
                    metadata_client.unregister_task_def(task_name)
                except Exception:
                    pass


def test_task_options_timeout_policies(conductor_configuration, cleanup_enabled):
    metadata_client = OrkesMetadataClient(conductor_configuration)
    test_suffix = str(uuid.uuid4())[:8]
    timeout_policies = ["TIME_OUT_WF", "ALERT_ONLY", "RETRY"]

    task_names = []
    try:
        for timeout_policy in timeout_policies:
            task_name = f"task_timeout_{timeout_policy.lower()}_{test_suffix}"
            task_names.append(task_name)

            task_opts = TaskOptions(
                timeout_seconds=120,
                response_timeout_seconds=30,
                timeout_policy=timeout_policy
            )

            task_def = TaskDef(name=task_name)
            apply_task_options_to_task_def(task_def, task_opts)

            metadata_client.register_task_def(task_def)

            retrieved_task = metadata_client.get_task_def(task_name)
            assert retrieved_task["timeoutPolicy"] == timeout_policy
            assert retrieved_task["timeoutSeconds"] == 120
            assert retrieved_task["responseTimeoutSeconds"] == 30

    finally:
        if cleanup_enabled:
            for task_name in task_names:
                try:
                    metadata_client.unregister_task_def(task_name)
                except Exception:
                    pass


def test_task_options_rate_limiting(conductor_configuration, cleanup_enabled):
    metadata_client = OrkesMetadataClient(conductor_configuration)
    test_suffix = str(uuid.uuid4())[:8]
    task_name = f"task_rate_limit_{test_suffix}"

    try:
        @task_options(
            rate_limit_per_frequency=50,
            rate_limit_frequency_in_seconds=10,
            concurrent_exec_limit=5
        )
        def test_task_rate_limit(_task_input):
            return {"result": "success"}

        task_opts = get_task_options(test_task_rate_limit)
        task_def = TaskDef(name=task_name)
        apply_task_options_to_task_def(task_def, task_opts)

        metadata_client.register_task_def(task_def)

        retrieved_task = metadata_client.get_task_def(task_name)
        assert retrieved_task["rateLimitPerFrequency"] == 50
        assert retrieved_task["rateLimitFrequencyInSeconds"] == 10
        assert retrieved_task["concurrentExecLimit"] == 5

    finally:
        if cleanup_enabled:
            try:
                metadata_client.unregister_task_def(task_name)
            except Exception:
                pass


def test_task_options_update_existing_task(conductor_configuration, cleanup_enabled):
    metadata_client = OrkesMetadataClient(conductor_configuration)
    test_suffix = str(uuid.uuid4())[:8]
    task_name = f"task_update_{test_suffix}"

    try:
        initial_task_def = TaskDef(
            name=task_name,
            description="Initial task",
            timeout_seconds=120,
            response_timeout_seconds=30,
            retry_count=1
        )
        metadata_client.register_task_def(initial_task_def)

        @task_options(
            timeout_seconds=3600,
            response_timeout_seconds=120,
            retry_count=5,
            retry_logic="LINEAR_BACKOFF",
            retry_delay_seconds=10,
            description="Updated task with options"
        )
        def test_task_update(_task_input):
            return {"result": "success"}

        task_opts = get_task_options(test_task_update)
        updated_task_def = TaskDef(name=task_name)
        apply_task_options_to_task_def(updated_task_def, task_opts)

        metadata_client.update_task_def(updated_task_def)

        retrieved_task = metadata_client.get_task_def(task_name)
        assert retrieved_task["timeoutSeconds"] == 3600
        assert retrieved_task["responseTimeoutSeconds"] == 120
        assert retrieved_task["retryCount"] == 5
        assert retrieved_task["retryLogic"] == "LINEAR_BACKOFF"
        assert retrieved_task["retryDelaySeconds"] == 10
        assert retrieved_task["description"] == "Updated task with options"

    finally:
        if cleanup_enabled:
            try:
                metadata_client.unregister_task_def(task_name)
            except Exception:
                pass


def test_task_options_with_backoff_scaling(conductor_configuration, cleanup_enabled):
    metadata_client = OrkesMetadataClient(conductor_configuration)
    test_suffix = str(uuid.uuid4())[:8]
    task_name = f"task_backoff_{test_suffix}"

    try:
        @task_options(
            timeout_seconds=3600,
            response_timeout_seconds=120,
            retry_count=5,
            retry_logic="EXPONENTIAL_BACKOFF",
            retry_delay_seconds=2,
            backoff_scale_factor=3
        )
        def test_task_backoff(_task_input):
            return {"result": "success"}

        task_opts = get_task_options(test_task_backoff)
        task_def = TaskDef(name=task_name)
        apply_task_options_to_task_def(task_def, task_opts)

        metadata_client.register_task_def(task_def)

        retrieved_task = metadata_client.get_task_def(task_name)
        assert retrieved_task["retryLogic"] == "EXPONENTIAL_BACKOFF"
        assert retrieved_task["backoffScaleFactor"] == 3
        assert retrieved_task["retryDelaySeconds"] == 2

    finally:
        if cleanup_enabled:
            try:
                metadata_client.unregister_task_def(task_name)
            except Exception:
                pass


def test_task_options_preserves_function_behavior():
    @task_options(timeout_seconds=60)
    def test_function(value):
        return {"result": value * 2}

    result = test_function(5)
    assert result == {"result": 10}

    task_opts = get_task_options(test_function)
    assert task_opts is not None
    assert task_opts.timeout_seconds == 60


def test_task_options_preserves_function_metadata():
    @task_options(timeout_seconds=60, description="Test function")
    def my_test_function(value):
        return {"result": value}

    assert my_test_function.__name__ == "my_test_function"

    task_opts = get_task_options(my_test_function)
    assert task_opts is not None


def test_multiple_tasks_with_different_options(conductor_configuration, cleanup_enabled):
    metadata_client = OrkesMetadataClient(conductor_configuration)
    test_suffix = str(uuid.uuid4())[:8]
    task_names = []

    try:
        @task_options(timeout_seconds=120, response_timeout_seconds=30, retry_count=1)
        def fast_task(_task_input):
            return {"result": "fast"}

        @task_options(timeout_seconds=3600, response_timeout_seconds=300, retry_count=10, retry_logic="EXPONENTIAL_BACKOFF")
        def slow_task(_task_input):
            return {"result": "slow"}

        @task_options(
            timeout_seconds=3600,
            response_timeout_seconds=60,
            concurrent_exec_limit=100,
            rate_limit_per_frequency=1000,
            rate_limit_frequency_in_seconds=60
        )
        def high_throughput_task(_task_input):
            return {"result": "throughput"}

        tasks = [
            ("fast", fast_task, 120, 1, None),
            ("slow", slow_task, 3600, 10, "EXPONENTIAL_BACKOFF"),
            ("throughput", high_throughput_task, 3600, None, None)
        ]

        for task_type, task_func, timeout, retry_count, retry_logic in tasks:
            task_name = f"task_{task_type}_{test_suffix}"
            task_names.append(task_name)

            task_opts = get_task_options(task_func)
            task_def = TaskDef(name=task_name)
            apply_task_options_to_task_def(task_def, task_opts)

            metadata_client.register_task_def(task_def)

            retrieved_task = metadata_client.get_task_def(task_name)
            assert retrieved_task["timeoutSeconds"] == timeout
            if retry_count is not None:
                assert retrieved_task["retryCount"] == retry_count
            if retry_logic is not None:
                assert retrieved_task["retryLogic"] == retry_logic

    finally:
        if cleanup_enabled:
            for task_name in task_names:
                try:
                    metadata_client.unregister_task_def(task_name)
                except Exception:
                    pass


def test_task_options_to_dict_integration(conductor_configuration, cleanup_enabled):
    metadata_client = OrkesMetadataClient(conductor_configuration)
    test_suffix = str(uuid.uuid4())[:8]
    task_name = f"task_to_dict_{test_suffix}"

    try:
        @task_options(
            timeout_seconds=3600,
            response_timeout_seconds=90,
            retry_count=3,
            retry_logic="FIXED",
            owner_email="dict@example.com",
            description="Task for to_dict test"
        )
        def test_task_dict(_task_input):
            return {"result": "success"}

        task_opts = get_task_options(test_task_dict)
        options_dict = task_opts.to_dict()

        assert "timeout_seconds" in options_dict
        assert options_dict["timeout_seconds"] == 3600
        assert "response_timeout_seconds" in options_dict
        assert options_dict["response_timeout_seconds"] == 90
        assert "retry_count" in options_dict
        assert options_dict["retry_count"] == 3
        assert "retry_logic" in options_dict
        assert options_dict["retry_logic"] == "FIXED"
        assert "owner_email" in options_dict
        assert options_dict["owner_email"] == "dict@example.com"
        assert "description" in options_dict
        assert options_dict["description"] == "Task for to_dict test"

        assert "poll_timeout_seconds" not in options_dict

        task_def = TaskDef(name=task_name)
        apply_task_options_to_task_def(task_def, task_opts)
        metadata_client.register_task_def(task_def)

        retrieved_task = metadata_client.get_task_def(task_name)
        assert retrieved_task["name"] == task_name

    finally:
        if cleanup_enabled:
            try:
                metadata_client.unregister_task_def(task_name)
            except Exception:
                pass
