"""
Task Workers Example
====================

Comprehensive collection of worker examples demonstrating various patterns and features.

What it does:
-------------
- Complex data types: Workers using dataclasses and custom objects
- Error handling: NonRetryableException for terminal failures
- TaskResult: Direct control over task status and output
- Type hints: Proper typing for inputs and outputs
- Various patterns: Simple returns, exceptions, TaskResult objects

Workers Demonstrated:
---------------------
1. get_user_info: Returns complex dataclass objects
2. process_order: Works with custom OrderInfo dataclass
3. check_inventory: Simple boolean return
4. ship_order: Uses TaskResult for detailed control
5. retry_example: Demonstrates retryable vs non-retryable errors
6. random_failure: Shows probabilistic failure handling

Use Cases:
----------
- Working with complex data structures in workflows
- Proper error handling and retry strategies
- Direct task result manipulation
- Integrating with existing Python data models
- Building type-safe workers

Key Concepts:
-------------
- @worker_task: Decorator to register Python functions as workers
- Dataclasses: Structured data as worker input/output
- TaskResult: Fine-grained control over task completion
- NonRetryableException: Terminal failures that skip retries
- Type Hints: Enable type checking and better IDE support
"""
import datetime
from dataclasses import dataclass
from random import random

from conductor.client.http.models import TaskResult, Task
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.exception import NonRetryableException
from conductor.client.worker.worker_task import worker_task
from examples.orkes.workers.user_details import UserDetails


@dataclass
class OrderInfo:
    """
    Python data class that uses dataclass
    """
    order_id: int
    sku: str
    quantity: int
    sku_price: float


@worker_task(task_definition_name='get_user_info')
def get_user_info(user_id: str) -> UserDetails:
    if user_id is None:
        user_id = 'none'
    return UserDetails(name='user_' + user_id, user_id=user_id, addresses=[{
        'street': '21 jump street',
        'city': 'new york'
    }])


@worker_task(task_definition_name='save_order')
async def save_order(order_details: OrderInfo) -> OrderInfo:
    order_details.sku_price = order_details.quantity * order_details.sku_price
    return order_details


@worker_task(task_definition_name='process_task')
def process_task(task: Task) -> TaskResult:
    task_result = task.to_task_result(TaskResultStatus.COMPLETED)
    task_result.add_output_data('name', 'orkes')
    task_result.add_output_data('complex', UserDetails(name='u1', addresses=[], user_id=5))
    task_result.add_output_data('time', datetime.datetime.now())
    return task_result


@worker_task(task_definition_name='failure')
def always_fail() -> dict:
    # raising NonRetryableException updates the task with FAILED_WITH_TERMINAL_ERROR status
    raise NonRetryableException('this worker task will always have a terminal failure')


@worker_task(task_definition_name='fail_but_retry')
def fail_but_retry() -> int:
    numx = random.randint(0, 10)
    if numx < 8:
        # raising NonRetryableException updates the task with FAILED_WITH_TERMINAL_ERROR status
        raise Exception(f'number {numx} is less than 4.  I am going to fail this task and retry')
    return numx
