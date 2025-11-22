import subprocess
from typing import List

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.worker.worker_task import worker_task


# @worker_task(task_definition_name='shell')
def execute_shell(command: str, args: List[str]) -> str:
    full_command = [command]
    full_command = full_command + args
    result = subprocess.run(full_command, stdout=subprocess.PIPE)

    return str(result.stdout)


@worker_task(task_definition_name='task_with_retries2')
def execute_shell() -> str:
    return "hello"


def main():
    # defaults to reading the configuration using following env variables
    # CONDUCTOR_SERVER_URL : conductor server e.g. https://developer.orkescloud.com/api
    # CONDUCTOR_AUTH_KEY : API Authentication Key
    # CONDUCTOR_AUTH_SECRET: API Auth Secret
    api_config = Configuration()

    task_handler = TaskHandler(configuration=api_config)
    task_handler.start_processes()

    task_handler.join_processes()


if __name__ == '__main__':
    main()
