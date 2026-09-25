from typing import Any, Dict, Optional

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class AiDecisionTask(TaskInterface):
    """Run a Jev choice decision using server-managed credentials.

    State and question instructions must be nonempty strings. Questions must
    contain exactly one choice question with 2 to 255 choices. The server validates
    inputs after resolving workflow references.

    Output retains model, answers, usage, latencyMs and optional requestId.
    Use output("selectedCase") with a separate SwitchTask to route the result.
    """

    def __init__(
        self,
        task_ref_name: str,
        model: str,
        state: str,
        questions: Dict[str, Any],
        task_name: Optional[str] = None,
    ) -> None:
        super().__init__(
            task_reference_name=task_ref_name,
            task_type=TaskType.AI_DECISION,
            task_name=task_name or "ai_decision",
            input_parameters={
                "model": model,
                "state": state,
                "questions": questions,
            },
        )
