"""
Task execution context utilities.

For long-running tasks, use Union[YourType, TaskInProgress] return type:

    from typing import Union
    from conductor.client.context import TaskInProgress, get_task_context

    @worker_task(task_definition_name='long_task')
    def process_video(video_id: str) -> Union[GeneratedVideo, TaskInProgress]:
        ctx = get_task_context()
        poll_count = ctx.get_poll_count()

        if poll_count < 3:
            # Still processing - return TaskInProgress
            return TaskInProgress(
                callback_after_seconds=60,
                output={'status': 'processing', 'progress': poll_count * 33}
            )

        # Complete - return the actual result
        return GeneratedVideo(id=video_id, url="...", status="ready")
"""

from conductor.client.context.task_context import (
    TaskContext,
    get_task_context,
    TaskInProgress,
)

__all__ = [
    'TaskContext',
    'get_task_context',
    'TaskInProgress',
]
