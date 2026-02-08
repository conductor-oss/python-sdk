from __future__ import annotations

from typing import Optional, List, Dict, Any

from typing_extensions import Self

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class LlmSearchEmbeddings(TaskInterface):
    """Searches a vector database using pre-computed embeddings.

    Args:
        task_ref_name: Reference name for the task in the workflow.
        vector_db: Vector database integration name.
        index: Index or collection name.
        embeddings: Pre-computed embedding vector to search with.
        namespace: Optional namespace for data isolation.
        max_results: Maximum number of results to return.
        dimensions: Embedding vector dimensions.
        embedding_model: Embedding model name.
        embedding_model_provider: Embedding model provider name.
        task_name: Optional custom task name.
    """

    def __init__(
        self,
        task_ref_name: str,
        vector_db: str,
        index: str,
        embeddings: List[float],
        namespace: Optional[str] = None,
        max_results: int = 1,
        dimensions: Optional[int] = None,
        embedding_model: Optional[str] = None,
        embedding_model_provider: Optional[str] = None,
        task_name: Optional[str] = None,
    ) -> Self:
        if task_name is None:
            task_name = "llm_search_embeddings"

        input_params: Dict[str, Any] = {
            "vectorDB": vector_db,
            "index": index,
            "embeddings": embeddings,
            "maxResults": max_results,
        }

        if namespace is not None:
            input_params["namespace"] = namespace
        if dimensions is not None:
            input_params["dimensions"] = dimensions
        if embedding_model is not None:
            input_params["embeddingModel"] = embedding_model
        if embedding_model_provider is not None:
            input_params["embeddingModelProvider"] = embedding_model_provider

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_SEARCH_EMBEDDINGS,
            input_parameters=input_params,
        )
