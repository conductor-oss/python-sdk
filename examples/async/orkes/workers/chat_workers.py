from typing import List

from conductor.asyncio_client.worker.worker_task import worker_task
from conductor.asyncio_client.workflow.task.llm_tasks.llm_chat_complete import (
    ChatMessage,
)


@worker_task(task_definition_name="prep", poll_interval_millis=2000)
def collect_history(
    user_input: str,
    seed_question: str,
    assistant_response: str,
    history: list[ChatMessage],
) -> List[ChatMessage]:
    all_history = []

    if history is not None:
        all_history = history

    if assistant_response is not None:
        all_history.append(ChatMessage(message=assistant_response, role="assistant"))

    if user_input is not None:
        all_history.append(ChatMessage(message=user_input, role="user"))
    else:
        all_history.append(ChatMessage(message=seed_question, role="user"))

    return all_history
