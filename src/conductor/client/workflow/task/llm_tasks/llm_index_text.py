from __future__ import annotations

from typing import Optional

from typing_extensions import Self

from conductor.client.workflow.task.llm_tasks.utils.embedding_model import EmbeddingModel
from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class LlmIndexText(TaskInterface):
    """Stores text as embeddings in a vector database.

    Generates embeddings from the provided text and indexes them.

    Args:
        task_ref_name: Reference name for the task in the workflow.
        vector_db: Vector database integration name (e.g., "pineconedb", "pgvectordb").
        index: Index or collection name in the vector database.
        embedding_model: EmbeddingModel with provider and model name.
        text: Text content to index.
        doc_id: Unique identifier for the document.
        namespace: Optional namespace for data isolation (e.g., Pinecone namespaces).
        task_name: Optional custom task name.
        metadata: Optional metadata dictionary to store with the document.
        url: Optional URL of the source document.
        chunk_size: Size of text chunks for splitting (default: 12000 on server).
        chunk_overlap: Overlap between chunks (default: 400 on server).
        dimensions: Embedding vector dimensions.
    """

    def __init__(
        self,
        task_ref_name: str,
        vector_db: str,
        index: str,
        embedding_model: EmbeddingModel,
        text: str,
        doc_id: str,
        namespace: Optional[str] = None,
        task_name: Optional[str] = None,
        metadata: Optional[dict] = None,
        url: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        dimensions: Optional[int] = None,
    ) -> Self:
        if task_name is None:
            task_name = "llm_index_text"

        input_params = {
            "vectorDB": vector_db,
            "index": index,
            "embeddingModelProvider": embedding_model.provider,
            "embeddingModel": embedding_model.model,
            "text": text,
            "docId": doc_id,
        }

        if metadata:
            input_params["metadata"] = metadata
        if namespace is not None:
            input_params["namespace"] = namespace
        if url is not None:
            input_params["url"] = url
        if chunk_size is not None:
            input_params["chunkSize"] = chunk_size
        if chunk_overlap is not None:
            input_params["chunkOverlap"] = chunk_overlap
        if dimensions is not None:
            input_params["dimensions"] = dimensions

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_INDEX_TEXT,
            input_parameters=input_params,
        )
