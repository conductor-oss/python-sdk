from __future__ import annotations

import functools
from typing import Callable, Optional


_TASK_OPTIONS_ATTR = "_conductor_task_options"


class TaskOptions:
    def __init__(
        self,
        timeout_seconds: Optional[int] = None,
        response_timeout_seconds: Optional[int] = None,
        poll_timeout_seconds: Optional[int] = None,
        retry_count: Optional[int] = None,
        retry_logic: Optional[str] = None,
        retry_delay_seconds: Optional[int] = None,
        backoff_scale_factor: Optional[int] = None,
        rate_limit_per_frequency: Optional[int] = None,
        rate_limit_frequency_in_seconds: Optional[int] = None,
        concurrent_exec_limit: Optional[int] = None,
        timeout_policy: Optional[str] = None,
        owner_email: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self._validate_parameters(
            timeout_seconds=timeout_seconds,
            response_timeout_seconds=response_timeout_seconds,
            poll_timeout_seconds=poll_timeout_seconds,
            retry_count=retry_count,
            retry_logic=retry_logic,
            retry_delay_seconds=retry_delay_seconds,
            backoff_scale_factor=backoff_scale_factor,
            rate_limit_per_frequency=rate_limit_per_frequency,
            rate_limit_frequency_in_seconds=rate_limit_frequency_in_seconds,
            concurrent_exec_limit=concurrent_exec_limit,
            timeout_policy=timeout_policy,
        )

        self.timeout_seconds = timeout_seconds
        self.response_timeout_seconds = response_timeout_seconds
        self.poll_timeout_seconds = poll_timeout_seconds
        self.retry_count = retry_count
        self.retry_logic = retry_logic
        self.retry_delay_seconds = retry_delay_seconds
        self.backoff_scale_factor = backoff_scale_factor
        self.rate_limit_per_frequency = rate_limit_per_frequency
        self.rate_limit_frequency_in_seconds = rate_limit_frequency_in_seconds
        self.concurrent_exec_limit = concurrent_exec_limit
        self.timeout_policy = timeout_policy
        self.owner_email = owner_email
        self.description = description

    @staticmethod
    def _validate_parameters(
        timeout_seconds: Optional[int] = None,
        response_timeout_seconds: Optional[int] = None,
        poll_timeout_seconds: Optional[int] = None,
        retry_count: Optional[int] = None,
        retry_logic: Optional[str] = None,
        retry_delay_seconds: Optional[int] = None,
        backoff_scale_factor: Optional[int] = None,
        rate_limit_per_frequency: Optional[int] = None,
        rate_limit_frequency_in_seconds: Optional[int] = None,
        concurrent_exec_limit: Optional[int] = None,
        timeout_policy: Optional[str] = None,
    ):
        if timeout_seconds is not None and timeout_seconds < 0:
            raise ValueError("timeout_seconds must be >= 0")

        if response_timeout_seconds is not None and response_timeout_seconds < 1:
            raise ValueError("response_timeout_seconds must be >= 1")

        if poll_timeout_seconds is not None and poll_timeout_seconds < 0:
            raise ValueError("poll_timeout_seconds must be >= 0")

        if retry_count is not None and retry_count < 0:
            raise ValueError("retry_count must be >= 0")

        if retry_logic is not None:
            valid_retry_logics = [
                "FIXED",
                "LINEAR_BACKOFF",
                "EXPONENTIAL_BACKOFF",
            ]
            if retry_logic not in valid_retry_logics:
                raise ValueError(
                    f"retry_logic must be one of {valid_retry_logics}, got {retry_logic}"
                )

        if retry_delay_seconds is not None and retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must be >= 0")

        if backoff_scale_factor is not None and backoff_scale_factor < 1:
            raise ValueError("backoff_scale_factor must be >= 1")

        if rate_limit_per_frequency is not None and rate_limit_per_frequency < 0:
            raise ValueError("rate_limit_per_frequency must be >= 0")

        if (
            rate_limit_frequency_in_seconds is not None
            and rate_limit_frequency_in_seconds < 0
        ):
            raise ValueError("rate_limit_frequency_in_seconds must be >= 0")

        if concurrent_exec_limit is not None and concurrent_exec_limit < 0:
            raise ValueError("concurrent_exec_limit must be >= 0")

        if timeout_policy is not None:
            valid_timeout_policies = ["TIME_OUT_WF", "ALERT_ONLY", "RETRY"]
            if timeout_policy not in valid_timeout_policies:
                raise ValueError(
                    f"timeout_policy must be one of {valid_timeout_policies}, got {timeout_policy}"
                )

    def to_dict(self):
        result = {}
        if self.timeout_seconds is not None:
            result["timeout_seconds"] = self.timeout_seconds
        if self.response_timeout_seconds is not None:
            result["response_timeout_seconds"] = self.response_timeout_seconds
        if self.poll_timeout_seconds is not None:
            result["poll_timeout_seconds"] = self.poll_timeout_seconds
        if self.retry_count is not None:
            result["retry_count"] = self.retry_count
        if self.retry_logic is not None:
            result["retry_logic"] = self.retry_logic
        if self.retry_delay_seconds is not None:
            result["retry_delay_seconds"] = self.retry_delay_seconds
        if self.backoff_scale_factor is not None:
            result["backoff_scale_factor"] = self.backoff_scale_factor
        if self.rate_limit_per_frequency is not None:
            result["rate_limit_per_frequency"] = self.rate_limit_per_frequency
        if self.rate_limit_frequency_in_seconds is not None:
            result["rate_limit_frequency_in_seconds"] = (
                self.rate_limit_frequency_in_seconds
            )
        if self.concurrent_exec_limit is not None:
            result["concurrent_exec_limit"] = self.concurrent_exec_limit
        if self.timeout_policy is not None:
            result["timeout_policy"] = self.timeout_policy
        if self.owner_email is not None:
            result["owner_email"] = self.owner_email
        if self.description is not None:
            result["description"] = self.description
        return result


def task_options(
    timeout_seconds: Optional[int] = None,
    response_timeout_seconds: Optional[int] = None,
    poll_timeout_seconds: Optional[int] = None,
    retry_count: Optional[int] = None,
    retry_logic: Optional[str] = None,
    retry_delay_seconds: Optional[int] = None,
    backoff_scale_factor: Optional[int] = None,
    rate_limit_per_frequency: Optional[int] = None,
    rate_limit_frequency_in_seconds: Optional[int] = None,
    concurrent_exec_limit: Optional[int] = None,
    timeout_policy: Optional[str] = None,
    owner_email: Optional[str] = None,
    description: Optional[str] = None,
) -> Callable:
    options = TaskOptions(
        timeout_seconds=timeout_seconds,
        response_timeout_seconds=response_timeout_seconds,
        poll_timeout_seconds=poll_timeout_seconds,
        retry_count=retry_count,
        retry_logic=retry_logic,
        retry_delay_seconds=retry_delay_seconds,
        backoff_scale_factor=backoff_scale_factor,
        rate_limit_per_frequency=rate_limit_per_frequency,
        rate_limit_frequency_in_seconds=rate_limit_frequency_in_seconds,
        concurrent_exec_limit=concurrent_exec_limit,
        timeout_policy=timeout_policy,
        owner_email=owner_email,
        description=description,
    )

    def decorator(func: Callable) -> Callable:
        setattr(func, _TASK_OPTIONS_ATTR, options)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        setattr(wrapper, _TASK_OPTIONS_ATTR, options)
        return wrapper

    return decorator


def get_task_options(func: Callable) -> Optional[TaskOptions]:
    return getattr(func, _TASK_OPTIONS_ATTR, None)
