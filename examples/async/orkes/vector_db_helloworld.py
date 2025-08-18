import asyncio

from conductor.asyncio_client.ai.orchestrator import AsyncAIOrchestrator
from conductor.asyncio_client.automator.task_handler import TaskHandler
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.http.api_client import ApiClient
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients
from conductor.asyncio_client.worker.worker_task import worker_task
from conductor.asyncio_client.workflow.conductor_workflow import AsyncConductorWorkflow
from conductor.asyncio_client.workflow.task.llm_tasks.llm_chat_complete import (
    ChatMessage,
    LlmChatComplete,
)
from conductor.asyncio_client.workflow.task.llm_tasks.llm_search_index import (
    LlmSearchIndex,
)
from conductor.asyncio_client.workflow.task.llm_tasks.llm_text_complete import (
    LlmTextComplete,
)
from conductor.shared.ai.configuration import PineconeConfig
from conductor.shared.ai.enums import VectorDB


@worker_task(task_definition_name="get_friends_name")
def get_friend_name():
    return "anonymous"


def start_workers(api_config):
    task_handler = TaskHandler(
        workers=[],
        configuration=api_config,
        scan_for_annotated_workers=True,
    )
    task_handler.start_processes()
    return task_handler


async def main():
    vector_db = "pinecone"
    llm_provider = "openai"
    embedding_model = "text-embedding-ada-002"
    text_complete_model = "text-davinci-003"
    chat_complete_model = "gpt-5"

    api_config = Configuration()
    async with ApiClient(api_config) as api_client:
        clients = OrkesClients(configuration=api_config, api_client=api_client)
        workflow_executor = clients.get_workflow_executor()

        orchestrator = AsyncAIOrchestrator(
            api_client=api_client, api_configuration=api_config
        )

        await orchestrator.add_vector_store(
            db_integration_name=vector_db,
            provider=VectorDB.PINECONE_DB,
            indices=["hello_world"],
            description="pinecone db",
            config=PineconeConfig(),
        )

        prompt_name = "us_constitution_qna"
        prompt_text = """
        Here is the fragment of the us constitution ${text}.  
        I have a question ${question}.
        Given the text fragment from the constitution - please answer the question. 
        If you cannot answer from within this context of text then say I don't know.
        """

        await orchestrator.add_prompt_template(
            prompt_name, prompt_text, "us_constitution_qna"
        )
        await orchestrator.associate_prompt_template(
            prompt_name, llm_provider, [text_complete_model]
        )

        workflow = AsyncConductorWorkflow(
            name="test_vector_db", version=1, executor=workflow_executor
        )

        question = "what is the first amendment to the constitution?"
        search_index = LlmSearchIndex(
            task_ref_name="search_vectordb",
            vector_db=vector_db,
            index="test",
            embedding_model=embedding_model,
            embedding_model_provider=llm_provider,
            namespace="us_constitution",
            query=question,
            max_results=2,
        )

        text_complete = LlmTextComplete(
            task_ref_name="us_constitution_qna",
            llm_provider=llm_provider,
            model=text_complete_model,
            prompt_name=prompt_name,
        )

        chat_complete = LlmChatComplete(
            task_ref_name="chat_complete_ref",
            llm_provider=llm_provider,
            model=chat_complete_model,
            instructions_template=prompt_name,
            messages=[ChatMessage(role="user", message=question)],
        )

        chat_complete.prompt_variable("text", search_index.output("result..text"))
        chat_complete.prompt_variable("question", question)

        text_complete.prompt_variable("text", search_index.output("result..text"))
        text_complete.prompt_variable("question", question)
        workflow >> search_index >> chat_complete

        workflow_run = await workflow.execute(workflow_input={})
        print(f"{workflow_run.output}")


if __name__ == "__main__":
    asyncio.run(main())
