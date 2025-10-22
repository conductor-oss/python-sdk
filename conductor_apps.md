# Using Conductor in Your Application

Conductor SDKs are lightweight and can easily be added to your existing or new Python app. This section will dive deeper into integrating Conductor in your application.

## Content

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Adding Conductor SDK to Your Application](#adding-conductor-sdk-to-your-application)
- [Testing Workflows](#testing-workflows)
  - [Example Unit Testing Application](#example-unit-testing-application)
- [Workflow Deployments Using CI/CD](#workflow-deployments-using-cicd)
- [Versioning Workflows](#versioning-workflows)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Adding Conductor SDK to Your Application

Conductor Python SDKs are published on PyPi @ https://pypi.org/project/conductor-python/:

```shell
pip3 install conductor-python
```

## Testing Workflows

Conductor SDK for Python provides a complete feature testing framework for your workflow-based applications. The framework works well with any testing framework you prefer without imposing any specific framework.

The Conductor server provides a test endpoint `POST /api/workflow/test` that allows you to post a workflow along with the test execution data to evaluate the workflow.

The goal of the test framework is as follows:

1. Ability to test the various branches of the workflow.
2. Confirm the workflow execution and tasks given a fixed set of inputs and outputs.
3. Validate that the workflow completes or fails given specific inputs.

Here are example assertions from the test:

```python

...
test_request = WorkflowTestRequest(name=wf.name, version=wf.version,
                                       task_ref_to_mock_output=task_ref_to_mock_output,
                                       workflow_def=wf.to_workflow_def())
run = workflow_client.test_workflow(test_request=test_request)

print(f'completed the test run')
print(f'status: {run.status}')
self.assertEqual(run.status, 'COMPLETED')

...

```

> [!note]
> Workflow workers are your regular Python functions and can be tested with any available testing framework.

### Example Unit Testing Application

See [test_workflows.py](examples/test_workflows.py) for a fully functional example of how to test a moderately complex workflow with branches.

## Workflow Deployments Using CI/CD

> [!tip]
> Treat your workflow definitions just like your code. Suppose you are defining the workflows using UI. In that case, we recommend checking the JSON configuration into the version control and using your development workflow for CI/CD to promote the workflow definitions across various environments such as Dev, Test, and Prod.

Here is a recommended approach when defining workflows using JSON:

* Treat your workflow metadata as code.
* Check in the workflow and task definitions along with the application code.
* Use `POST /api/metadata/*` endpoints or MetadataClient (`from conductor.client.metadata_client import MetadataClient`) to register/update workflows as part of the deployment process.
* Version your workflows. If there is a significant change, change the version field of the workflow. See versioning workflows below for more details.


## Versioning Workflows

A powerful feature of Conductor is the ability to version workflows. You should increment the version of the workflow when there is a significant change to the definition. You can run multiple versions of the workflow at the same time. When starting a new workflow execution, use the `version` field to specify which version to use. When omitted, the latest (highest-numbered) version is used.

* Versioning allows safely testing changes by doing canary testing in production or A/B testing across multiple versions before rolling out.
* A version can also be deleted, effectively allowing for "rollback" if required.
