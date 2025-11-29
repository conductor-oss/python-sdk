"""
Shell Worker Example
====================

Demonstrates creating workers that execute shell commands.

What it does:
-------------
- Defines a worker that can execute shell commands with arguments
- Shows how to capture and return command output
- Uses subprocess module for safe command execution

Use Cases:
----------
- Running system commands from workflows (backups, file operations)
- Integrating with command-line tools
- Executing scripts as part of workflow tasks
- System administration automation

**Security Warning:**
--------------------
⚠️ This example is for educational purposes. In production:
- Never execute arbitrary shell commands from untrusted input
- Always validate and sanitize command inputs
- Use allowlists for permitted commands
- Consider security implications before deployment
- Review subprocess security best practices

Key Concepts:
-------------
- Worker tasks can execute any Python code
- subprocess module for command execution
- Capturing stdout for workflow results
- Type hints for worker inputs
"""
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
