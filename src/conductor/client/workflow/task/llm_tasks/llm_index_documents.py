from __future__ import annotations

from typing import Optional

from typing_extensions import Self

from conductor.client.workflow.task.llm_tasks.utils.embedding_model import EmbeddingModel
from conductor.client.workflow.task.task import TaskInterface
from conductor.client.workflow.task.task_type import TaskType


class LlmIndexDocument(TaskInterface):
    """Indexes a document from a URL into a vector database.

    Fetches the document, splits it into chunks, generates embeddings,
    and stores them in the vector database.

    Note: This class uses the LLM_INDEX_TEXT task type on the server side.
    The server's IndexDocInput model handles both inline text (via LlmIndexText)
    and URL-based document indexing (via this class) under the same task type.

    Args:
        task_ref_name: Reference name for the task in the workflow.
        vector_db: Vector database integration name.
        namespace: Namespace for data isolation.
        embedding_model: EmbeddingModel with provider and model name.
        index: Index or collection name.
        url: URL to fetch the document from (HTTP(S), S3, blob store).
        media_type: Content type (e.g., application/pdf, text/html, text/plain).
        chunk_size: Size of text chunks for splitting.
        chunk_overlap: Overlap between chunks.
        doc_id: Override the default URL-based document ID.
        task_name: Optional custom task name.
        metadata: Optional metadata dictionary to store with the document.
        dimensions: Embedding vector dimensions.
    """

    def __init__(
        self,
        task_ref_name: str,
        vector_db: str,
        namespace: str,
        embedding_model: EmbeddingModel,
        index: str,
        url: str,
        media_type: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        doc_id: Optional[str] = None,
        task_name: Optional[str] = None,
        metadata: Optional[dict] = None,
        dimensions: Optional[int] = None,
    ) -> Self:
        input_params = {
            "vectorDB": vector_db,
            "namespace": namespace,
            "index": index,
            "embeddingModelProvider": embedding_model.provider,
            "embeddingModel": embedding_model.model,
            "url": url,
            "mediaType": media_type,
        }

        if metadata:
            input_params["metadata"] = metadata
        if chunk_size is not None:
            input_params["chunkSize"] = chunk_size
        if chunk_overlap is not None:
            input_params["chunkOverlap"] = chunk_overlap
        if doc_id is not None:
            input_params["docId"] = doc_id
        if dimensions is not None:
            input_params["dimensions"] = dimensions

        if task_name is None:
            task_name = "llm_index_text"

        super().__init__(
            task_name=task_name,
            task_reference_name=task_ref_name,
            task_type=TaskType.LLM_INDEX_TEXT,
            input_parameters=input_params,
        )
