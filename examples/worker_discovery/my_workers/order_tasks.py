"""
Order processing workers
"""

from conductor.client.worker.worker_task import worker_task


@worker_task(
    task_definition_name='process_order',
    thread_count=10,
    poll_timeout=200
)
async def process_order(order_id: str, amount: float) -> dict:
    """Process an order."""
    print(f"Processing order {order_id} for ${amount}")
    return {
        'order_id': order_id,
        'status': 'processed',
        'amount': amount
    }


@worker_task(
    task_definition_name='validate_order',
    thread_count=5
)
def validate_order(order_id: str, items: list) -> dict:
    """Validate an order."""
    print(f"Validating order {order_id} with {len(items)} items")
    return {
        'order_id': order_id,
        'valid': True,
        'item_count': len(items)
    }


@worker_task(
    task_definition_name='cancel_order',
    thread_count=5
)
async def cancel_order(order_id: str, reason: str) -> dict:
    """Cancel an order."""
    print(f"Cancelling order {order_id}: {reason}")
    return {
        'order_id': order_id,
        'status': 'cancelled',
        'reason': reason
    }
