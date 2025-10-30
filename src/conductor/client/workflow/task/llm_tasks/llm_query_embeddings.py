from __future__ import annotations

from typing import List, Optional

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class LlmQueryEmbeddings(TaskInterface):
    def __init__(
        self,
        task_ref_name: str,
        vector_db: str,
        index: str,
        embeddings: List[int],
        task_name: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> None:
        if task_name is None:
            task_name = "llm_get_embeddings"

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_GET_EMBEDDINGS,
            input_parameters={
                "vectorDB": vector_db,
                "namespace": namespace,
                "index": index,
                "embeddings": embeddings,
            },
        )
