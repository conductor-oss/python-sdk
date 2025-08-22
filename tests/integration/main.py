import logging
import os
import sys

from client import test_async
from client.orkes.test_orkes_clients import TestOrkesClients
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api_client import ApiClient
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from metadata.test_workflow_definition import run_workflow_definition_tests
from workflow.test_workflow_execution import run_workflow_execution_tests

_logger = logging.getLogger(
    Configuration.get_logging_formatted_name(
        __name__
    )
)


def generate_configuration():
    configuration = Configuration()
    configuration.debug = False
    configuration.apply_logging_config()

    return configuration


def main():
    configuration = generate_configuration()
    api_client = ApiClient(configuration)
    workflow_executor = WorkflowExecutor(configuration)

    test_async.test_async_method(api_client)
    run_workflow_definition_tests(workflow_executor)
    run_workflow_execution_tests(configuration, workflow_executor)
    TestOrkesClients(configuration=configuration).run()


if __name__ == "__main__":
    # set the no_proxy env
    # see this thread for more context
    # https://stackoverflow.com/questions/55408047/requests-get-not-finishing-doesnt-raise-any-error
    if sys.platform == "darwin":
        os.environ['no_proxy'] = '*'

    main()
