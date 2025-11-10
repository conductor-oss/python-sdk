"""
Notification workers
"""

from conductor.client.worker.worker_task import worker_task


@worker_task(
    task_definition_name='send_email',
    thread_count=20
)
async def send_email(to: str, subject: str, body: str) -> dict:
    """Send an email notification."""
    print(f"Sending email to {to}: {subject}")
    return {
        'to': to,
        'subject': subject,
        'status': 'sent'
    }


@worker_task(
    task_definition_name='send_sms',
    thread_count=20
)
async def send_sms(phone: str, message: str) -> dict:
    """Send an SMS notification."""
    print(f"Sending SMS to {phone}: {message}")
    return {
        'phone': phone,
        'status': 'sent'
    }
