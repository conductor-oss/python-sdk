from __future__ import annotations

from typing import List, Optional

from typing_extensions import Self

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class LlmQueryEmbeddings(TaskInterface):
    """Queries a vector database using pre-computed embeddings.

    Searches the vector database for the nearest neighbors to the
    provided embedding vector.

    Args:
        task_ref_name: Reference name for the task in the workflow.
        vector_db: Vector database integration name.
        index: Index or collection name.
        embeddings: Embedding vector (list of floats) to search with.
        task_name: Optional custom task name override.
        namespace: Optional namespace for data isolation.
    """

    def __init__(
        self,
        task_ref_name: str,
        vector_db: str,
        index: str,
        embeddings: List[float],
        task_name: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> Self:
        if task_name is None:
            task_name = "llm_get_embeddings"

        input_params = {
            "vectorDB": vector_db,
            "index": index,
            "embeddings": embeddings,
        }

        if namespace is not None:
            input_params["namespace"] = namespace

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_GET_EMBEDDINGS,
            input_parameters=input_params,
        )
