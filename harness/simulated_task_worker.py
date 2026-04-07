from __future__ import annotations

import math
import os
import random
import string
import time
from typing import Any, Dict, Optional, Tuple

from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.worker_interface import WorkerInterface

ALPHANUMERIC_CHARS = string.ascii_letters + string.digits

_instance_id: str = os.environ.get("HOSTNAME") or os.urandom(4).hex()


class SimulatedTaskWorker(WorkerInterface):

    def __init__(
        self,
        task_name: str,
        codename: str,
        sleep_seconds: int,
        batch_size: int = 5,
        poll_interval_ms: int = 1000,
    ) -> None:
        super().__init__(task_definition_name=task_name)
        self._task_name = task_name
        self._codename = codename
        self._default_delay_ms = sleep_seconds * 1000
        self.thread_count = batch_size
        self.poll_interval = poll_interval_ms
        self._worker_id = f"{task_name}-{_instance_id}"
        self._rng = random.Random()

        print(
            f"[{self._task_name}] Initialized worker "
            f"[workerId={self._worker_id}, codename={self._codename}, "
            f"batchSize={batch_size}, pollInterval={poll_interval_ms}ms]"
        )

    def get_identity(self) -> str:
        return self._worker_id

    def execute(self, task: Task) -> TaskResult:
        inp: Dict[str, Any] = task.input_data or {}
        task_id = task.task_id or ""
        task_index = _get_int(inp, "taskIndex", -1)

        print(
            f"[{self._task_name}] Starting simulated task "
            f"[id={task_id}, index={task_index}, codename={self._codename}]"
        )

        start_time = time.monotonic()

        delay_type = _get_str(inp, "delayType", "fixed")
        min_delay = _get_int(inp, "minDelay", self._default_delay_ms)
        max_delay = _get_int(inp, "maxDelay", min_delay + 100)
        mean_delay = _get_int(inp, "meanDelay", (min_delay + max_delay) // 2)
        std_deviation = _get_int(inp, "stdDeviation", 30)
        success_rate = _get_float(inp, "successRate", 1.0)
        failure_mode = _get_str(inp, "failureMode", "random")
        output_size = _get_int(inp, "outputSize", 1024)

        delay_ms = 0
        if delay_type.lower() != "wait":
            delay_ms = self._calculate_delay(delay_type, min_delay, max_delay, mean_delay, std_deviation)

            print(
                f"[{self._task_name}] Simulated task "
                f"[id={task_id}, index={task_index}] sleeping for {delay_ms} ms"
            )
            time.sleep(delay_ms / 1000.0)

        if not self._should_task_succeed(success_rate, failure_mode, inp):
            print(
                f"[{self._task_name}] Simulated task "
                f"[id={task_id}, index={task_index}] failed as configured"
            )
            result = self.get_task_result_from_task(task)
            result.status = TaskResultStatus.FAILED
            result.reason_for_incompletion = "Simulated task failure based on configuration"
            return result

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        output = self._generate_output(inp, task_id, task_index, delay_ms, elapsed_ms, output_size)

        result = self.get_task_result_from_task(task)
        result.status = TaskResultStatus.COMPLETED
        result.output_data = output
        return result

    # ── Delay calculation ─────────────────────────────────────────

    def _calculate_delay(
        self, delay_type: str, min_delay: int, max_delay: int, mean_delay: int, std_deviation: int,
    ) -> int:
        dt = delay_type.lower()
        if dt == "fixed":
            return min_delay
        if dt == "random":
            spread = max(1, max_delay - min_delay + 1)
            return min_delay + self._rng.randint(0, spread - 1)
        if dt == "normal":
            gaussian = self._next_gaussian()
            delay = round(mean_delay + gaussian * std_deviation)
            return max(1, delay)
        if dt == "exponential":
            exp = -mean_delay * math.log(1 - self._rng.random())
            return max(min_delay, min(max_delay, int(exp)))
        return min_delay

    def _next_gaussian(self) -> float:
        u1 = 1.0 - self._rng.random()
        u2 = self._rng.random()
        return math.sqrt(-2.0 * math.log(u1)) * math.sin(2.0 * math.pi * u2)

    # ── Failure simulation ────────────────────────────────────────

    def _should_task_succeed(self, success_rate: float, failure_mode: str, inp: Dict[str, Any]) -> bool:
        force_success = inp.get("forceSuccess")
        if force_success is not None:
            b, ok = _to_bool(force_success)
            if ok:
                return b
        force_fail = inp.get("forceFail")
        if force_fail is not None:
            b, ok = _to_bool(force_fail)
            if ok:
                return not b

        fm = failure_mode.lower()
        if fm == "random":
            return self._rng.random() < success_rate
        if fm == "conditional":
            return self._should_conditional_succeed(success_rate, inp)
        if fm == "sequential":
            attempt = _get_int(inp, "attempt", 1)
            fail_until_attempt = _get_int(inp, "failUntilAttempt", 2)
            return attempt >= fail_until_attempt
        return self._rng.random() < success_rate

    def _should_conditional_succeed(self, success_rate: float, inp: Dict[str, Any]) -> bool:
        task_index = _get_int(inp, "taskIndex", -1)
        if task_index >= 0:
            fail_indexes = inp.get("failIndexes")
            if isinstance(fail_indexes, list):
                for idx in fail_indexes:
                    if _to_int(idx) == task_index:
                        return False
            fail_every = _get_int(inp, "failEvery", 0)
            if fail_every > 0 and task_index % fail_every == 0:
                return False
        return self._rng.random() < success_rate

    # ── Output generation ─────────────────────────────────────────

    def _generate_output(
        self,
        inp: Dict[str, Any],
        task_id: str,
        task_index: int,
        delay_ms: int,
        elapsed_time_ms: int,
        output_size: int,
    ) -> Dict[str, Any]:
        output: Dict[str, Any] = {
            "taskId": task_id,
            "taskIndex": task_index,
            "codename": self._codename,
            "status": "completed",
            "configuredDelayMs": delay_ms,
            "actualExecutionTimeMs": elapsed_time_ms,
            "a_or_b": "a" if self._rng.randint(0, 99) > 20 else "b",
            "c_or_d": "c" if self._rng.randint(0, 99) > 33 else "d",
        }

        if _get_bool(inp, "includeInput", False):
            output["input"] = inp

        prev = inp.get("previousTaskOutput")
        if prev is not None:
            output["previousTaskData"] = prev

        if output_size > 0:
            output["data"] = _generate_random_data(self._rng, output_size)

        output_template = inp.get("outputTemplate")
        if isinstance(output_template, dict):
            output.update(output_template)

        return output


# ── Helpers ───────────────────────────────────────────────────────

def _to_int(v: Any) -> int:
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    if isinstance(v, str):
        try:
            return int(v)
        except ValueError:
            return 0
    return 0


def _to_float(v: Any) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            return 0.0
    return 0.0


def _to_bool(v: Any) -> Tuple[bool, bool]:
    if isinstance(v, bool):
        return v, True
    if isinstance(v, str):
        low = v.lower()
        if low in ("true", "1"):
            return True, True
        if low in ("false", "0"):
            return False, True
    if isinstance(v, (int, float)):
        return v != 0, True
    return False, False


def _get_int(inp: Dict[str, Any], key: str, default: int) -> int:
    v = inp.get(key)
    if v is None:
        return default
    return _to_int(v)


def _get_float(inp: Dict[str, Any], key: str, default: float) -> float:
    v = inp.get(key)
    if v is None:
        return default
    return _to_float(v)


def _get_str(inp: Dict[str, Any], key: str, default: str) -> str:
    v = inp.get(key)
    if v is None:
        return default
    if isinstance(v, str):
        return v
    return default


def _get_bool(inp: Dict[str, Any], key: str, default: bool) -> bool:
    v = inp.get(key)
    if v is None:
        return default
    b, ok = _to_bool(v)
    return b if ok else default


def _generate_random_data(rng: random.Random, size: int) -> str:
    if size <= 0:
        return ""
    return "".join(rng.choices(ALPHANUMERIC_CHARS, k=size))
