from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from greetings_workflow import greetings_workflow


def register_workflow(workflow_executor: WorkflowExecutor) -> ConductorWorkflow:
    workflow = greetings_workflow(workflow_executor=workflow_executor)
    workflow.register(True)
    return workflow


def main():
    # points to http://localhost:8080/api by default
    api_config = Configuration()
    api_config.apply_logging_config()

    workflow_executor = WorkflowExecutor(configuration=api_config)

    # Needs to be done only when registering a workflow one-time
    workflow = register_workflow(workflow_executor)

    task_handler = TaskHandler(configuration=api_config)
    task_handler.start_processes()

    workflow_run = workflow_executor.execute(name=workflow.name, version=workflow.version,
                                             workflow_input={'name': 'World'})

    print(f'\nworkflow result: {workflow_run}\n')
    print(f'see the workflow execution here: {api_config.ui_host}/execution/{workflow_run.workflow_id}\n')
    
    task_handler.stop_processes()


if __name__ == '__main__':
    main()
