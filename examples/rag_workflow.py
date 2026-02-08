"""
RAG (Retrieval Augmented Generation) Workflow Example

This example demonstrates a complete RAG pipeline using Conductor:
1. User provides a file path (PDF, Word, Excel, etc.) as workflow input
2. A custom worker converts the file to markdown using markitdown
3. Conductor indexes the markdown into pgvector using OpenAI embeddings
4. A search query retrieves relevant context from the vector store
5. An LLM generates an answer grounded in the retrieved context

Prerequisites:
1. Install dependencies:
   pip install conductor-python "markitdown[pdf]"

2. Orkes Conductor server with AI/LLM support:
   This example uses LLM system tasks (LLM_INDEX_TEXT, LLM_SEARCH_INDEX,
   LLM_CHAT_COMPLETE) which require Orkes Conductor (not OSS conductor-rust).

3. Configure integrations in Conductor:
   - Vector DB integration named "postgres-prod" (pgvector)
   - LLM provider named "openai" with a valid API key
   (See Conductor docs for integration setup)

4. Set environment variables:
   export CONDUCTOR_SERVER_URL="http://localhost:7001/api"
   # If using Orkes Cloud:
   # export CONDUCTOR_AUTH_KEY="your-key"
   # export CONDUCTOR_AUTH_SECRET="your-secret"

5. Run the example:
   python examples/rag_workflow.py examples/goog-20251231.pdf "What were Google's total revenues?"

Pipeline (5 tasks):
  convert_to_markdown  (SIMPLE worker - markitdown)
  LLM_INDEX_TEXT       (index markdown into pgvector with OpenAI embeddings)
  WAIT                 (pause for pgvector to commit - eventual consistency)
  LLM_SEARCH_INDEX     (semantic search over the vector store)
  LLM_CHAT_COMPLETE    (generate a grounded answer with gpt-4o-mini)
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

from markitdown import MarkItDown

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients
from conductor.client.worker.worker_task import worker_task
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.llm_tasks.llm_chat_complete import LlmChatComplete, ChatMessage
from conductor.client.workflow.task.llm_tasks.llm_index_text import LlmIndexText
from conductor.client.workflow.task.llm_tasks.llm_search_index import LlmSearchIndex
from conductor.client.workflow.task.llm_tasks.utils.embedding_model import EmbeddingModel
from conductor.client.workflow.task.simple_task import SimpleTask
from conductor.client.workflow.task.wait_task import WaitForDurationTask


# =============================================================================
# Configuration constants
# Matches the reference workflow: postgres-prod, openai, text-embedding-3-small
# =============================================================================

VECTOR_DB = "postgres-prod"
VECTOR_INDEX = "demo_index"
EMBEDDING_PROVIDER = "openai"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
LLM_PROVIDER = "openai"
LLM_MODEL = "gpt-4o-mini"


# =============================================================================
# Workers
# =============================================================================

MAX_CHUNK_CHARS = 20000  # ~5000 tokens, well within embedding model limits


@worker_task(task_definition_name='convert_to_markdown')
def convert_to_markdown(file_path: str) -> Dict[str, Any]:
    """Convert a document to markdown using markitdown.

    Supports: PDF, Word (.docx), Excel (.xlsx), PowerPoint (.pptx),
    HTML, images (with EXIF/OCR), and more.

    For large documents the text is truncated to MAX_CHUNK_CHARS so that it
    fits within the embedding model's token limit.  In a production system
    you would split the text into multiple chunks and index each one
    separately (e.g. using a dynamic fork).

    Args:
        file_path: Absolute path to the document file.

    Returns:
        dict with keys:
            - markdown: the converted text content (may be truncated)
            - title: filename used as document title
            - doc_id: identifier derived from the file path
    """
    md = MarkItDown()
    result = md.convert(file_path)
    filename = Path(file_path).stem  # e.g. "report" from "report.pdf"
    text = result.text_content

    # Truncate to stay within embedding model token limits
    if len(text) > MAX_CHUNK_CHARS:
        text = text[:MAX_CHUNK_CHARS]

    return {
        "markdown": text,
        "title": filename,
        "doc_id": filename.lower().replace(" ", "_"),
    }


# =============================================================================
# Workflow definition
# =============================================================================

def create_rag_workflow(executor, namespace: str = "demo_namespace") -> ConductorWorkflow:
    """Build the RAG pipeline workflow.

    Pipeline:
        convert_to_markdown --> index_document --> wait --> search_index --> generate_answer

    The workflow input must contain:
        - file_path (str): path to the document to ingest
        - question (str): the user's question to answer

    Args:
        executor: WorkflowExecutor from OrkesClients.
        namespace: pgvector namespace for isolation.

    Returns:
        A ConductorWorkflow ready to register and execute.
    """
    workflow = ConductorWorkflow(
        executor=executor,
        name="rag_document_pipeline",
        version=1,
        description="RAG pipeline: convert document -> index in pgvector -> search -> answer",
    )
    workflow.timeout_seconds(600)  # 10 minutes for large documents

    # Step 1: Convert the input file to markdown (custom worker)
    convert_task = SimpleTask(
        task_def_name="convert_to_markdown",
        task_reference_name="convert_doc_ref",
    )
    convert_task.input_parameters = {
        "file_path": "${workflow.input.file_path}",
    }

    # Step 2: Index the markdown text into pgvector
    # This mirrors the reference workflow's LLM_INDEX_TEXT configuration
    index_task = LlmIndexText(
        task_ref_name="index_doc_ref",
        vector_db=VECTOR_DB,
        index=VECTOR_INDEX,
        namespace=namespace,
        embedding_model=EmbeddingModel(provider=EMBEDDING_PROVIDER, model=EMBEDDING_MODEL),
        text="${convert_doc_ref.output.markdown}",
        doc_id="${convert_doc_ref.output.doc_id}",
        dimensions=EMBEDDING_DIMENSIONS,
        chunk_size=1024,
        chunk_overlap=128,
        metadata={
            "title": "${convert_doc_ref.output.title}",
            "source": "${workflow.input.file_path}",
        },
    )

    # Step 3: Wait for pgvector to commit the new embeddings.
    # Without this pause the search may return empty results because the
    # index write has not been flushed yet (eventual consistency).
    wait_task = WaitForDurationTask(
        task_ref_name="wait_for_index_ref",
        duration_time_seconds=5,
    )

    # Step 4: Search the index with the user's question (after the wait)
    search_task = LlmSearchIndex(
        task_ref_name="search_index_ref",
        vector_db=VECTOR_DB,
        namespace=namespace,
        index=VECTOR_INDEX,
        embedding_model_provider=EMBEDDING_PROVIDER,
        embedding_model=EMBEDDING_MODEL,
        query="${workflow.input.question}",
        max_results=5,
        dimensions=EMBEDDING_DIMENSIONS,
    )

    # Step 5: Generate an answer using the retrieved context
    answer_task = LlmChatComplete(
        task_ref_name="generate_answer_ref",
        llm_provider=LLM_PROVIDER,
        model=LLM_MODEL,
        messages=[
            ChatMessage(
                role="system",
                message=(
                    "You are a helpful assistant. Answer the user's question "
                    "based ONLY on the context provided below. If the context "
                    "does not contain enough information, say so.\n\n"
                    "Context from knowledge base:\n"
                    "${search_index_ref.output.result}"
                ),
            ),
            ChatMessage(
                role="user",
                message="${workflow.input.question}",
            ),
        ],
        temperature=0.2,
        max_tokens=1024,
    )

    # Chain the tasks sequentially
    workflow >> convert_task >> index_task >> wait_task >> search_task >> answer_task

    # Define workflow outputs (mirrors the reference workflow output structure)
    workflow.output_parameters({
        "indexing_status": "${index_doc_ref.output}",
        "retrieved_context": "${search_index_ref.output.result}",
        "final_answer": "${generate_answer_ref.output.result}",
    })

    return workflow


# =============================================================================
# Main
# =============================================================================

def main():
    if len(sys.argv) < 3:
        print("Usage: python rag_workflow.py <file_path> <question>")
        print()
        print("Example:")
        print('  python examples/rag_workflow.py examples/goog-20251231.pdf "What were Google\'s total revenues?"')
        sys.exit(1)

    file_path = os.path.abspath(sys.argv[1])
    question = sys.argv[2]

    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    # --- Configuration ---
    api_config = Configuration()
    clients = OrkesClients(configuration=api_config)
    executor = clients.get_workflow_executor()
    workflow_client = clients.get_workflow_client()

    print("=" * 80)
    print("RAG WORKFLOW - Document Ingestion & Question Answering")
    print("=" * 80)
    print(f"  File:     {file_path}")
    print(f"  Question: {question}")
    print(f"  Server:   {api_config.host}")
    print()

    # --- Register and start workers ---
    # scan_for_annotated_workers=True discovers @worker_task decorated functions
    task_handler = TaskHandler(
        workers=[],
        configuration=api_config,
        scan_for_annotated_workers=True,
    )
    task_handler.start_processes()

    try:
        # --- Create and register workflow ---
        workflow = create_rag_workflow(executor)
        workflow.register(overwrite=True)
        print(f"Registered workflow: {workflow.name} v{workflow.version}")

        # --- Start the workflow ---
        # Use start_workflow_with_input so the input is set correctly on the
        # workflow execution (not nested inside the StartWorkflowRequest).
        print("Starting workflow execution...")
        workflow_id = workflow.start_workflow_with_input(
            workflow_input={
                "file_path": file_path,
                "question": question,
            },
        )

        ui_url = f"{api_config.ui_host}/execution/{workflow_id}"
        print(f"  Workflow ID: {workflow_id}")
        print(f"  View:        {ui_url}")

        # --- Poll for completion ---
        print("  Waiting for workflow to complete...")
        max_wait = 120
        poll_interval = 2
        elapsed = 0
        status = "RUNNING"
        wf_status = None
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            wf_status = workflow_client.get_workflow(workflow_id, include_tasks=False)
            status = wf_status.status
            if status in ("COMPLETED", "FAILED", "TERMINATED", "TIMED_OUT"):
                break

        print(f"  Status:      {status}")
        print()

        if status == "COMPLETED":
            output = wf_status.output or {}

            # Show retrieved context
            context = output.get("retrieved_context", [])
            if context:
                print(f"Retrieved {len(context)} chunk(s) from knowledge base")
                for i, chunk in enumerate(context, 1):
                    score = chunk.get("score", 0)
                    text_preview = chunk.get("text", "")[:120]
                    print(f"  {i}. (score={score:.3f}) {text_preview}...")
                print()

            # Show the answer
            answer = output.get("final_answer", "No answer generated.")
            print("Answer:")
            print("-" * 80)
            print(answer)
            print("-" * 80)
        else:
            print(f"Workflow did not complete successfully: {status}")
            if hasattr(wf_status, "reason_for_incompletion") and wf_status.reason_for_incompletion:
                print(f"  Reason: {wf_status.reason_for_incompletion}")

    finally:
        task_handler.stop_processes()
        print("\nWorkers stopped.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    main()
