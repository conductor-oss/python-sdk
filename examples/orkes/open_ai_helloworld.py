import os

from conductor.client.ai.configuration import LLMProvider
from conductor.client.ai.integrations import OpenAIConfig
from conductor.client.ai.orchestrator import AIOrchestrator
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.worker.worker_task import worker_task
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.llm_tasks.llm_text_complete import LlmTextComplete


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
    llm_provider = 'open_ai_' + os.getlogin()
    text_complete_model = 'gpt-4'
    embedding_complete_model = 'text-embedding-ada-002'

    api_config = Configuration()
    api_config.apply_logging_config()
    task_workers = start_workers(api_config)

    open_ai_config = OpenAIConfig()

    orchestrator = AIOrchestrator(api_configuration=api_config)

    orchestrator.add_ai_integration(ai_integration_name=llm_provider, provider=LLMProvider.OPEN_AI,
                                    models=[text_complete_model, embedding_complete_model],
                                    description='openai config',
                                    config=open_ai_config)

    # Define and associate prompt with the ai integration
    prompt_name = 'say_hi_to_friend'
    prompt_text = 'give an evening greeting to ${friend_name}. go: '

    orchestrator.add_prompt_template(prompt_name, prompt_text, 'test prompt')
    orchestrator.associate_prompt_template(prompt_name, llm_provider, [text_complete_model])

    # Test the prompt
    result = orchestrator.test_prompt_template('give an evening greeting to ${friend_name}. go: ',
                                               {'friend_name': 'Orkes'}, llm_provider, text_complete_model)

    print(f'test prompt: {result}')

    # Create a 2-step LLM Chain and execute it

    get_name = get_friend_name(task_ref_name='get_friend_name_ref')

    text_complete = LlmTextComplete(task_ref_name='say_hi_ref', llm_provider=llm_provider, model=text_complete_model,
                                    prompt_name=prompt_name)

    text_complete.prompt_variable(variable='friend_name', value=get_name.output('result'))

    workflow = ConductorWorkflow(executor=orchestrator.workflow_executor, name='say_hi_to_the_friend')
    workflow >> get_name >> text_complete

    workflow.output_parameters = {'greetings': text_complete.output('result')}

    # execute the workflow to get the results
    result = workflow.execute(workflow_input={}, wait_for_seconds=10)
    print(f'\nOutput of the LLM chain workflow: {result.output["result"]}\n\n')

    # cleanup and stop
    task_workers.stop_processes()


if __name__ == '__main__':
    main()
