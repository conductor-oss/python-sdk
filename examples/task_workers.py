import datetime
from dataclasses import dataclass
from random import random

from conductor.client.http.models import TaskResult, Task
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.shared.worker.exception import NonRetryableException
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
def save_order(order_details: OrderInfo) -> OrderInfo:
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
