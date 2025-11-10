"""
Payment processing workers
"""

from conductor.client.worker.worker_task import worker_task


@worker_task(
    task_definition_name='process_payment',
    thread_count=15,
    lease_extend_enabled=True
)
async def process_payment(order_id: str, amount: float, payment_method: str) -> dict:
    """Process a payment."""
    print(f"Processing payment of ${amount} for order {order_id} via {payment_method}")

    # Simulate payment processing
    import asyncio
    await asyncio.sleep(0.5)

    return {
        'order_id': order_id,
        'amount': amount,
        'payment_method': payment_method,
        'status': 'completed',
        'transaction_id': f"txn_{order_id}"
    }


@worker_task(
    task_definition_name='refund_payment',
    thread_count=10
)
async def refund_payment(transaction_id: str, amount: float) -> dict:
    """Process a refund."""
    print(f"Refunding ${amount} for transaction {transaction_id}")
    return {
        'transaction_id': transaction_id,
        'amount': amount,
        'status': 'refunded'
    }
