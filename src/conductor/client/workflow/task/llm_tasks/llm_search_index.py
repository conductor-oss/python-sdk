from __future__ import annotations

from typing import Optional

from typing_extensions import Self

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class LlmSearchIndex(TaskInterface):
    """Searches a vector database index using a text query.

    Generates embeddings from the query text and searches the vector
    database for semantically similar documents.

    Args:
        task_ref_name: Reference name for the task in the workflow.
        vector_db: Vector database integration name.
        namespace: Namespace for data isolation.
        index: Index or collection name.
        embedding_model_provider: AI model integration name for embeddings.
        embedding_model: Embedding model identifier.
        query: Text query to search for.
        task_name: Optional custom task name override.
        max_results: Maximum number of results to return (default: 1).
        dimensions: Embedding vector dimensions.
    """

    def __init__(
        self,
        task_ref_name: str,
        vector_db: str,
        namespace: str,
        index: str,
        embedding_model_provider: str,
        embedding_model: str,
        query: str,
        task_name: Optional[str] = None,
        max_results: int = 1,
        dimensions: Optional[int] = None,
    ) -> Self:
        if task_name is None:
            task_name = "llm_search_index"

        input_params = {
            "vectorDB": vector_db,
            "namespace": namespace,
            "index": index,
            "embeddingModelProvider": embedding_model_provider,
            "embeddingModel": embedding_model,
            "query": query,
            "maxResults": max_results,
        }

        if dimensions is not None:
            input_params["dimensions"] = dimensions

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_SEARCH_INDEX,
            input_parameters=input_params,
        )
