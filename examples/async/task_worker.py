import datetime
from dataclasses import dataclass
from random import randint
import asyncio

from conductor.asyncio_client.adapters.models import TaskResult, Task
from conductor.shared.http.enums import TaskResultStatus
from conductor.shared.worker.exception import NonRetryableException
from conductor.asyncio_client.worker.worker_task import worker_task
from conductor.asyncio_client.http.api_client import ApiClient
from conductor.asyncio_client.automator.task_handler import TaskHandler
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients
from conductor.asyncio_client.workflow.conductor_workflow import AsyncConductorWorkflow


class UserDetails:
    """
    User info data class with constructor to set properties
    """

    swagger_types = {
        '_name': 'str',
        '_user_id': 'str',
        '_phone': 'str',
        '_email': 'str',
        '_addresses': 'object',
    }

    attribute_map = {
        '_name': 'name',
        '_user_id': 'user_id',
        '_phone': 'phone',
        '_email': 'email',
        '_addresses': 'addresses'
    }

    def __init__(self, name: str, user_id: int, phone: str, email: str, addresses: list[object]) -> None:
        self._name = name
        self._user_id = user_id
        self._phone = phone
        self._email = email
        self._addresses = addresses

    @property
    def name(self) -> str:
        return self._name

    @property
    def phone(self) -> str:
        return self._phone

    @property
    def email(self) -> str:
        return self._email

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def address(self) -> list[object]:
        return self._addresses


@dataclass
class OrderInfo:
    """
    Python data class that uses dataclass
    """

    order_id: int
    sku: str
    quantity: int
    sku_price: float


@worker_task(task_definition_name="get_user_info")
def get_user_info(user_id: str) -> UserDetails:
    if user_id is None:
        user_id = "none"
    return UserDetails(
        name="user_" + user_id,
        user_id=user_id,
        phone="555-123-4567",
        email=f"{user_id}@example.com",
        addresses=[{"street": "21 jump street", "city": "new york"}],
    )


@worker_task(task_definition_name="save_order")
def save_order(order_details: OrderInfo) -> OrderInfo:
    order_details.sku_price = order_details.quantity * order_details.sku_price
    return order_details


@worker_task(task_definition_name="process_task")
def process_task(task: Task) -> TaskResult:
    task_result = task.to_task_result(TaskResultStatus.COMPLETED)
    task_result.add_output_data("name", "orkes")
    task_result.add_output_data(
        "complex",
        UserDetails(
            name="u1",
            user_id=5,
            phone="555-123-4567",
            email="u1@example.com",
            addresses=[],
        ),
    )
    task_result.add_output_data("time", datetime.datetime.now())
    return task_result


@worker_task(task_definition_name="failure")
def always_fail() -> dict:
    # raising NonRetryableException updates the task with FAILED_WITH_TERMINAL_ERROR status
    raise NonRetryableException("this worker task will always have a terminal failure")


@worker_task(task_definition_name="fail_but_retry")
def fail_but_retry() -> int:
    numx = randint(0, 10)
    if numx < 8:
        # raising NonRetryableException updates the task with FAILED_WITH_TERMINAL_ERROR status
        raise Exception(
            f"number {numx} is less than 4.  I am going to fail this task and retry"
        )
    return numx


async def main():
    """
    Main function to demonstrate running a workflow with the tasks defined in this file.
    This example creates a workflow that:
    1. Gets user information
    2. Processes an order
    3. Handles potential failures with retry logic
    """
    # Configuration - defaults to reading from environment variables:
    # CONDUCTOR_SERVER_URL : conductor server e.g. https://play.orkes.io/api
    # CONDUCTOR_AUTH_KEY : API Authentication Key  
    # CONDUCTOR_AUTH_SECRET: API Auth Secret
    api_config = Configuration()
    
    task_handler = TaskHandler(configuration=api_config)
    task_handler.start_processes()
    
    async with ApiClient(api_config) as api_client:
        clients = OrkesClients(api_client=api_client, configuration=api_config)
        workflow_executor = clients.get_workflow_executor()
        
        # Create a workflow that demonstrates the tasks
        workflow = AsyncConductorWorkflow(
            name="task_worker_demo", 
            version=1, 
            executor=workflow_executor
        )
        
        # Create task instances
        user_info_task = get_user_info(
            task_ref_name="get_user_info_ref", 
            user_id=workflow.input("user_id")
        )
        
        # Create an order for processing
        order_info = OrderInfo(
            order_id=12345,
            sku="PROD-001",
            quantity=2,
            sku_price=29.99
        )
        
        save_order_task = save_order(
            task_ref_name="save_order_ref",
            order_details=order_info
        )
        
        # Add a task that might fail but can retry
        retry_task = fail_but_retry(task_ref_name="retry_task_ref")
        
        # Define workflow execution order
        workflow >> user_info_task >> save_order_task >> retry_task
        
        # Configure workflow output
        workflow.output_parameters(output_parameters={
            "user_details": user_info_task.output("result"),
            "order_info": save_order_task.output("result"),
            "retry_result": retry_task.output("result")
        })
        
        # Execute the workflow
        print("Starting workflow execution...")
        workflow_run = await workflow.execute(workflow_input={"user_id": "user_123"})
        
        print(f"\nWorkflow completed successfully!")
        print(f"Workflow ID: {workflow_run.workflow_id}")
        print(f"Workflow output: {workflow_run.output}")
        print(f"View execution details at: {api_config.ui_host}/execution/{workflow_run.workflow_id}")
            
        task_handler.stop_processes()


if __name__ == "__main__":
    asyncio.run(main())
