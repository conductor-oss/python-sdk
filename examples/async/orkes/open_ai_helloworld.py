import asyncio

from conductor.asyncio_client.ai.orchestrator import AsyncAIOrchestrator
from conductor.asyncio_client.automator.task_handler import TaskHandler
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.worker.worker_task import worker_task
from conductor.asyncio_client.workflow.conductor_workflow import AsyncConductorWorkflow
from conductor.asyncio_client.workflow.task.llm_tasks.llm_text_complete import (
    LlmTextComplete,
)
from conductor.shared.ai.configuration import OpenAIConfig
from conductor.shared.ai.enums import LLMProvider


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
    llm_provider = "openai"
    text_complete_model = "gpt-5"
    embedding_complete_model = "text-embedding-ada-002"

    api_config = Configuration()
    async with ApiClient(api_config) as api_client:
        task_workers = start_workers(api_config)

        open_ai_config = OpenAIConfig()

        orchestrator = AsyncAIOrchestrator(
            api_configuration=api_config, api_client=api_client
        )

        await orchestrator.add_ai_integration(
            ai_integration_name=llm_provider,
            provider=LLMProvider.OPEN_AI,
            models=[text_complete_model, embedding_complete_model],
            description="openai config",
            config=open_ai_config,
        )

        # Define and associate prompt with the ai integration
        prompt_name = "say_hi_to_friend"
        prompt_text = "give an evening greeting to ${friend_name}. go: "

        await orchestrator.add_prompt_template(prompt_name, prompt_text, "test prompt")
        await orchestrator.associate_prompt_template(
            prompt_name, llm_provider, [text_complete_model]
        )

        # Test the prompt
        result = await orchestrator.test_prompt_template(
            "give an evening greeting to ${friend_name}. go: ",
            {"friend_name": "Orkes"},
            llm_provider,
            text_complete_model,
        )

        print(f"test prompt: {result}")

        # Create a 2-step LLM Chain and execute it

        get_name = get_friend_name(task_ref_name="get_friend_name_ref")

        text_complete = LlmTextComplete(
            task_ref_name="say_hi_ref",
            llm_provider=llm_provider,
            model=text_complete_model,
            prompt_name=prompt_name,
        )

        workflow = AsyncConductorWorkflow(
            executor=orchestrator.workflow_executor, name="say_hi_to_the_friend"
        )

        workflow >> get_name >> text_complete

        workflow.output_parameters = {"greetings": text_complete.output("result")}

        # execute the workflow to get the results
        result = await workflow.execute(workflow_input={}, wait_for_seconds=10)
        print(f'\nOutput of the LLM chain workflow: {result.output["result"]}\n\n')

    # cleanup and stop
    task_workers.stop_processes()


if __name__ == "__main__":
    asyncio.run(main())
