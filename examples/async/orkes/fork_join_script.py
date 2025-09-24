import asyncio

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients
from conductor.asyncio_client.workflow.conductor_workflow import AsyncConductorWorkflow
from conductor.asyncio_client.workflow.task.fork_task import ForkTask
from conductor.asyncio_client.workflow.task.http_task import HttpTask
from conductor.asyncio_client.workflow.task.join_task import JoinTask
from conductor.shared.workflow.enums import HttpMethod
from conductor.shared.workflow.models import HttpInput


async def main():
    api_config = Configuration()
    api_config.apply_logging_config()
    async with ApiClient(api_config) as api_client:
        clients = OrkesClients(configuration=api_config, api_client=api_client)
        executor = clients.get_workflow_executor()

        workflow = AsyncConductorWorkflow(
            name="fork_join_example", version=1, executor=executor
        )
        fork_size = 10
        tasks = []
        join_on = []
        for i in range(fork_size):
            http = HttpTask(
                task_ref_name=f"http_{i}",
                http_input=HttpInput(
                    uri="https://orkes-api-tester.orkesconductor.com/unknown",
                    method=HttpMethod.GET,
                ),
            )
            http.optional = True
            tasks.append([http])
            join_on.append(f"http_{i}")

        # HTTP tasks are marked as optional and the URL gives 404 error
        # the script below checks if the tasks are completed or completed with errors and completes the join task
        script = """
        (function(){
          let results = {};
          let pendingJoinsFound = false;
          if($.joinOn){
            $.joinOn.forEach((element)=>{
              if($[element] && $[element].status !== 'COMPLETED' && $[element] && $[element].status !== 'COMPLETED_WITH_ERRORS'){
                results[element] = $[element].status;
                pendingJoinsFound = true;
              }
            });
            if(pendingJoinsFound){
              return {
                "status":"IN_PROGRESS",
                "reasonForIncompletion":"Pending",
                "outputData":{
                  "scriptResults": results
                }
              };
            }
            // To complete the Join - return true OR an object with status = 'COMPLETED' like above.
            return true;
          }
        })();
        """
        join = JoinTask(task_ref_name="join", join_on_script=script, join_on=join_on)
        fork = ForkTask(task_ref_name="fork", forked_tasks=tasks)
        workflow >> fork >> join
        workflow_id = await workflow.start_workflow_with_input()
    print(f"Started workflow with id {workflow_id}")
    print(f"See the workflow execution: {api_config.ui_host}/execution/{workflow_id}\n")


if __name__ == "__main__":
    asyncio.run(main())
