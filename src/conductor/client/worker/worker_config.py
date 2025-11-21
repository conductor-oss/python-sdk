"""
Worker Configuration - Hierarchical configuration resolution for worker properties

Provides a three-tier configuration hierarchy:
1. Code-level defaults (lowest priority) - decorator parameters
2. Global worker config (medium priority) - conductor.worker.all.<property>
3. Worker-specific config (highest priority) - conductor.worker.<worker_name>.<property>

Example:
    # Code level
    @worker_task(task_definition_name='process_order', poll_interval=1000, domain='dev')
    def process_order(order_id: str):
        ...

    # Environment variables
    export conductor.worker.all.poll_interval=500
    export conductor.worker.process_order.domain=production

    # Result: poll_interval=500, domain='production'
"""

from __future__ import annotations
import os
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Property mappings for environment variable names
# Maps Python parameter names to environment variable suffixes
ENV_PROPERTY_NAMES = {
    'poll_interval': 'poll_interval',
    'domain': 'domain',
    'worker_id': 'worker_id',
    'thread_count': 'thread_count',
    'register_task_def': 'register_task_def',
    'poll_timeout': 'poll_timeout',
    'lease_extend_enabled': 'lease_extend_enabled'
}


def _parse_env_value(value: str, expected_type: type) -> Any:
    """
    Parse environment variable value to the expected type.

    Args:
        value: String value from environment variable
        expected_type: Expected Python type (int, bool, str, etc.)

    Returns:
        Parsed value in the expected type
    """
    if value is None:
        return None

    # Handle boolean values
    if expected_type == bool:
        return value.lower() in ('true', '1', 'yes', 'on')

    # Handle integer values
    if expected_type == int:
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Cannot convert '{value}' to int, using as-is")
            return value

    # Handle float values
    if expected_type == float:
        try:
            return float(value)
        except ValueError:
            logger.warning(f"Cannot convert '{value}' to float, using as-is")
            return value

    # String values
    return value


def _get_env_value(worker_name: str, property_name: str, expected_type: type = str) -> Optional[Any]:
    """
    Get configuration value from environment variables with hierarchical lookup.

    Priority order (highest to lowest):
    1. conductor.worker.<worker_name>.<property>
    2. conductor.worker.all.<property>

    Args:
        worker_name: Task definition name
        property_name: Property name (e.g., 'poll_interval')
        expected_type: Expected type for parsing (int, bool, str, etc.)

    Returns:
        Configuration value if found, None otherwise
    """
    # Check worker-specific override first
    worker_specific_key = f"conductor.worker.{worker_name}.{property_name}"
    value = os.environ.get(worker_specific_key)
    if value is not None:
        logger.debug(f"Using worker-specific config: {worker_specific_key}={value}")
        return _parse_env_value(value, expected_type)

    # Check global worker config
    global_key = f"conductor.worker.all.{property_name}"
    value = os.environ.get(global_key)
    if value is not None:
        logger.debug(f"Using global worker config: {global_key}={value}")
        return _parse_env_value(value, expected_type)

    return None


def resolve_worker_config(
    worker_name: str,
    poll_interval: Optional[float] = None,
    domain: Optional[str] = None,
    worker_id: Optional[str] = None,
    thread_count: Optional[int] = None,
    register_task_def: Optional[bool] = None,
    poll_timeout: Optional[int] = None,
    lease_extend_enabled: Optional[bool] = None,
    non_blocking_async: Optional[bool] = None
) -> dict:
    """
    Resolve worker configuration with hierarchical override.

    Configuration hierarchy (highest to lowest priority):
    1. conductor.worker.<worker_name>.<property> - Worker-specific env var
    2. conductor.worker.all.<property> - Global worker env var
    3. Code-level value - Decorator parameter

    Args:
        worker_name: Task definition name
        poll_interval: Polling interval in milliseconds (code-level default)
        domain: Worker domain (code-level default)
        worker_id: Worker ID (code-level default)
        thread_count: Number of threads (code-level default)
        register_task_def: Whether to register task definition (code-level default)
        poll_timeout: Polling timeout in milliseconds (code-level default)
        lease_extend_enabled: Whether lease extension is enabled (code-level default)
        non_blocking_async: Whether non-blocking async is enabled (code-level default)

    Returns:
        Dict with resolved configuration values

    Example:
        # Code has: poll_interval=1000
        # Env has: conductor.worker.all.poll_interval=500
        # Result: poll_interval=500

        config = resolve_worker_config(
            worker_name='process_order',
            poll_interval=1000,
            domain='dev'
        )
        # config = {'poll_interval': 500, 'domain': 'dev', ...}
    """
    resolved = {}

    # Resolve poll_interval
    env_poll_interval = _get_env_value(worker_name, 'poll_interval', float)
    resolved['poll_interval'] = env_poll_interval if env_poll_interval is not None else poll_interval

    # Resolve domain
    env_domain = _get_env_value(worker_name, 'domain', str)
    resolved['domain'] = env_domain if env_domain is not None else domain

    # Resolve worker_id
    env_worker_id = _get_env_value(worker_name, 'worker_id', str)
    resolved['worker_id'] = env_worker_id if env_worker_id is not None else worker_id

    # Resolve thread_count
    env_thread_count = _get_env_value(worker_name, 'thread_count', int)
    resolved['thread_count'] = env_thread_count if env_thread_count is not None else thread_count

    # Resolve register_task_def
    env_register = _get_env_value(worker_name, 'register_task_def', bool)
    resolved['register_task_def'] = env_register if env_register is not None else register_task_def

    # Resolve poll_timeout
    env_poll_timeout = _get_env_value(worker_name, 'poll_timeout', int)
    resolved['poll_timeout'] = env_poll_timeout if env_poll_timeout is not None else poll_timeout

    # Resolve lease_extend_enabled
    env_lease_extend = _get_env_value(worker_name, 'lease_extend_enabled', bool)
    resolved['lease_extend_enabled'] = env_lease_extend if env_lease_extend is not None else lease_extend_enabled

    # Resolve non_blocking_async
    env_non_blocking = _get_env_value(worker_name, 'non_blocking_async', bool)
    resolved['non_blocking_async'] = env_non_blocking if env_non_blocking is not None else non_blocking_async

    return resolved


def get_worker_config_summary(worker_name: str, resolved_config: dict) -> str:
    """
    Generate a human-readable summary of worker configuration resolution.

    Args:
        worker_name: Task definition name
        resolved_config: Resolved configuration dict

    Returns:
        Formatted summary string

    Example:
        summary = get_worker_config_summary('process_order', config)
        print(summary)
        # Worker 'process_order' configuration:
        #   poll_interval: 500 (from conductor.worker.all.poll_interval)
        #   domain: production (from conductor.worker.process_order.domain)
        #   thread_count: 5 (from code)
    """
    lines = [f"Worker '{worker_name}' configuration:"]

    for prop_name, value in resolved_config.items():
        if value is None:
            continue

        # Check source of configuration
        worker_specific_key = f"conductor.worker.{worker_name}.{prop_name}"
        global_key = f"conductor.worker.all.{prop_name}"

        if os.environ.get(worker_specific_key) is not None:
            source = f"from {worker_specific_key}"
        elif os.environ.get(global_key) is not None:
            source = f"from {global_key}"
        else:
            source = "from code"

        lines.append(f"  {prop_name}: {value} ({source})")

    return "\n".join(lines)
