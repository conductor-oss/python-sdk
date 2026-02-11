from __future__ import annotations

from typing import Optional, List, Dict, Any

from typing_extensions import Self

from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class LlmStoreEmbeddings(TaskInterface):
    """Stores pre-computed embeddings directly in a vector database.

    Args:
        task_ref_name: Reference name for the task in the workflow.
        vector_db: Vector database integration name.
        index: Index or collection name.
        embeddings: Pre-computed embedding vector.
        namespace: Optional namespace for data isolation.
        id: Document ID (auto-generated UUID if not provided).
        metadata: Optional metadata dictionary.
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
        id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding_model: Optional[str] = None,
        embedding_model_provider: Optional[str] = None,
        task_name: Optional[str] = None,
    ) -> Self:
        if task_name is None:
            task_name = "llm_store_embeddings"

        input_params: Dict[str, Any] = {
            "vectorDB": vector_db,
            "index": index,
            "embeddings": embeddings,
        }

        if namespace is not None:
            input_params["namespace"] = namespace
        if id is not None:
            input_params["id"] = id
        if metadata:
            input_params["metadata"] = metadata
        if embedding_model is not None:
            input_params["embeddingModel"] = embedding_model
        if embedding_model_provider is not None:
            input_params["embeddingModelProvider"] = embedding_model_provider

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_STORE_EMBEDDINGS,
            input_parameters=input_params,
        )
