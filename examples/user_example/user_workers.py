"""
User-related workers demonstrating HTTP calls and dataclass handling.

These workers are in a separate package to showcase worker discovery.
"""
import json
import time

from conductor.client.context import get_task_context
from conductor.client.worker.worker_task import worker_task
from user_example.models import User


@worker_task(
    task_definition_name='fetch_user',
    thread_count=10,
    poll_timeout=100
)
async def fetch_user(user_id: int) -> User:
    """
    Fetch user data from JSONPlaceholder API.

    This worker demonstrates:
    - Making HTTP calls
    - Returning dict that will be converted to User dataclass by next worker
    - Using synchronous requests (will run in thread pool in AsyncIO mode)

    Args:
        user_id: The user ID to fetch

    Returns:
        dict: User data from API
    """
    import requests

    response = requests.get(
        f'https://jsonplaceholder.typicode.com/users/{user_id}',
        timeout=10.0
    )
    # data = json.loads(response.json())
    return User(**response.json())
    # return


@worker_task(
    task_definition_name='update_user',
    thread_count=10,
    poll_timeout=100
)
async def update_user(user: User) -> dict:
    """
    Process user data - demonstrates dataclass input handling.

    This worker demonstrates:
    - Accepting User dataclass as input (SDK auto-converts from dict)
    - Type-safe worker function
    - Simple processing with sleep

    Args:
        user: User dataclass (automatically converted from previous task output)

    Returns:
        dict: Result with user ID
    """
    # Simulate some processing
    ctx = get_task_context()
    print(f'user name is {user.username} and workflow {ctx.get_workflow_instance_id()}')
    time.sleep(0.1)

    return {
        'user_id': user.id,
        'status': 'updated',
        'username': user.username,
        'email': user.email
    }
