"""
Workflow Status Listener Example
=================================

Demonstrates enabling external status listeners for workflow state changes.

What it does:
-------------
- Creates a workflow with HTTP task
- Enables a Kafka status listener
- Registers the workflow with listener configuration
- Status changes will be published to specified Kafka topic

Use Cases:
----------
- Real-time workflow monitoring via message queues
- Integrating workflows with external systems (Kafka, SQS, etc.)
- Building event-driven architectures
- Audit logging and compliance tracking
- Custom notifications on workflow state changes
- Analytics and metrics collection

Status Events Published:
------------------------
- Workflow started
- Workflow completed
- Workflow failed
- Workflow paused
- Workflow resumed
- Workflow terminated
- Task status changes

Key Concepts:
-------------
- Status Listener: External sink for workflow events
- enable_status_listener(): Configure where events are sent
- Kafka Integration: Publish events to Kafka topics
- Event-Driven Architecture: React to workflow state changes
- Workflow Registration: Persist workflow with listener config

Example Kafka Topic: kafka:<topic_name>
Example SQS Queue: sqs:<queue_url>
"""
import time
import uuid

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import StartWorkflowRequest, RerunWorkflowRequest, TaskResult
from conductor.client.orkes_clients import OrkesClients
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from conductor.client.workflow.task.http_task import HttpTask
from conductor.client.workflow.task.wait_task import WaitTask


def main():
    api_config = Configuration()
    clients = OrkesClients(configuration=api_config)

    workflow = ConductorWorkflow(name='workflow_status_listener_demo', version=1,
                                 executor=clients.get_workflow_executor())
    workflow >> HttpTask(task_ref_name='http_ref', http_input={
        'uri': 'https://orkes-api-tester.orkesconductor.com/api'
    })
    workflow.enable_status_listener('kafka:abcd')
    workflow.register(overwrite=True)
    print(f'Registered {workflow.name}')


if __name__ == '__main__':
    main()
