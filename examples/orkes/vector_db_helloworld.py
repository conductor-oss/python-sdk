import os

from conductor.shared.ai.enums import VectorDB
from conductor.shared.ai.configuration import OpenAIConfig, PineconeConfig
from conductor.client.ai.orchestrator import AIOrchestrator
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients
from conductor.client.worker.worker_task import worker_task
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.llm_tasks.llm_chat_complete import LlmChatComplete, ChatMessage
from conductor.client.workflow.task.llm_tasks.llm_generate_embeddings import LlmGenerateEmbeddings
from conductor.client.workflow.task.llm_tasks.llm_index_documents import LlmIndexDocument
from conductor.client.workflow.task.llm_tasks.llm_index_text import LlmIndexText
from conductor.client.workflow.task.llm_tasks.llm_query_embeddings import LlmQueryEmbeddings
from conductor.client.workflow.task.llm_tasks.llm_search_index import LlmSearchIndex
from conductor.client.workflow.task.llm_tasks.llm_text_complete import LlmTextComplete
from conductor.client.workflow.task.llm_tasks.utils.embedding_model import EmbeddingModel


@worker_task(task_definition_name='get_friends_name')
def get_friend_name():
    name = os.getlogin()
    if name is None:
        return 'anonymous'
    else:
        return name


def start_workers(api_config):
    task_handler = TaskHandler(
        workers=[],
        configuration=api_config,
        scan_for_annotated_workers=True,
    )
    task_handler.start_processes()
    return task_handler


def main():
    vector_db = 'pinecone_' + os.getlogin()
    llm_provider = 'open_ai_' + os.getlogin()
    embedding_model = 'text-embedding-ada-002'
    text_complete_model = 'text-davinci-003'
    chat_complete_model = 'gpt-4'

    api_config = Configuration()
    api_config.apply_logging_config()
    clients = OrkesClients(configuration=api_config)
    workflow_executor = clients.get_workflow_executor()
    workflow_client = clients.get_workflow_client()
    # task_workers = start_workers(api_config)

    open_ai_config = OpenAIConfig()

    orchestrator = AIOrchestrator(api_configuration=api_config)

    orchestrator.add_vector_store(db_integration_name=vector_db, provider=VectorDB.PINECONE_DB,
                                  indices=['hello_world'],
                                  description='pinecone db',
                                  config=PineconeConfig())

    prompt_name = 'us_constitution_qna'
    prompt_text = """
    Here is the fragment of the us constitution ${text}.
    I have a question ${question}.
    Given the text fragment from the constitution - please answer the question.
    If you cannot answer from within this context of text then say I don't know.
    """

    orchestrator.add_prompt_template(prompt_name, prompt_text, 'us_constitution_qna')
    orchestrator.associate_prompt_template(prompt_name, llm_provider, [text_complete_model])

    workflow = ConductorWorkflow(name='test_vector_db', version=1, executor=workflow_executor)
    index_text = LlmIndexText(task_ref_name='index_text_ref', vector_db=vector_db, index='test', namespace='hello',
                              embedding_model=EmbeddingModel(provider=llm_provider, model=embedding_model),
                              text="hello - how are you?", doc_id="hello_1",
                              metadata={
                                  "doctype": "testing only"
                              })

    index_document = LlmIndexDocument(task_ref_name='index_text_ref', vector_db=vector_db, index='test',
                                      namespace='us_constitution',
                                      embedding_model=EmbeddingModel(provider=llm_provider, model=embedding_model),
                                      url="https://constitutioncenter.org/media/files/constitution.pdf",
                                      media_type='application/pdf',
                                      doc_id="us_constitution",
                                      metadata={
                                          "doc_url": "https://constitutioncenter.org/media/files/constitution.pdf"
                                      })
    generate_embeddings = LlmGenerateEmbeddings(task_ref_name='generate_embeddings_ref', llm_provider=llm_provider,
                                                model=embedding_model, text='xxxxxxxx')

    query_index = LlmQueryEmbeddings(task_ref_name='query_vectordb', vector_db=vector_db, index='test',
                                     namespace='us_constitution',
                                     embeddings=generate_embeddings.output('result[0]'))

    question = 'what is the first amendment to the constitution?'
    search_index = LlmSearchIndex(task_ref_name='search_vectordb', vector_db=vector_db, index='test',
                                  embedding_model=embedding_model, embedding_model_provider=llm_provider,
                                  namespace='us_constitution', query=question, max_results=2)

    text_complete = LlmTextComplete(task_ref_name='us_constitution_qna', llm_provider=llm_provider,
                                    model=text_complete_model,
                                    prompt_name=prompt_name)

    chat_complete = LlmChatComplete(task_ref_name='chat_complete_ref',
                                    llm_provider=llm_provider, model=chat_complete_model,
                                    instructions_template=prompt_name,
                                    messages=[ChatMessage(
                                        role="user", message=question
                                    )])

    chat_complete.prompt_variable('text', search_index.output("result..text"))
    chat_complete.prompt_variable('question', question)

    text_complete.prompt_variable('text', search_index.output("result..text"))
    text_complete.prompt_variable('question', question)
    workflow >> search_index >> chat_complete

    workflow_run = workflow.execute(workflow_input={})
    print(f'{workflow_run.output}')
    # cleanup and stop
    # task_workers.stop_processes()


if __name__ == '__main__':
    main()
