from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from conductor.shared.worker.task_options import TaskOptions


def apply_task_options_to_task_def(task_def, task_options: TaskOptions) -> None:
    if task_options is None:
        return

    if task_options.timeout_seconds is not None:
        task_def.timeout_seconds = task_options.timeout_seconds

    if task_options.response_timeout_seconds is not None:
        task_def.response_timeout_seconds = task_options.response_timeout_seconds

    if task_options.poll_timeout_seconds is not None:
        task_def.poll_timeout_seconds = task_options.poll_timeout_seconds

    if task_options.retry_count is not None:
        task_def.retry_count = task_options.retry_count

    if task_options.retry_logic is not None:
        task_def.retry_logic = task_options.retry_logic

    if task_options.retry_delay_seconds is not None:
        task_def.retry_delay_seconds = task_options.retry_delay_seconds

    if task_options.backoff_scale_factor is not None:
        task_def.backoff_scale_factor = task_options.backoff_scale_factor

    if task_options.rate_limit_per_frequency is not None:
        task_def.rate_limit_per_frequency = task_options.rate_limit_per_frequency

    if task_options.rate_limit_frequency_in_seconds is not None:
        task_def.rate_limit_frequency_in_seconds = task_options.rate_limit_frequency_in_seconds

    if task_options.concurrent_exec_limit is not None:
        task_def.concurrent_exec_limit = task_options.concurrent_exec_limit

    if task_options.timeout_policy is not None:
        task_def.timeout_policy = task_options.timeout_policy

    if task_options.owner_email is not None:
        task_def.owner_email = task_options.owner_email

    if task_options.description is not None:
        task_def.description = task_options.description
