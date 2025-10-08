# Conductor OSS Python SDK
[![CI Status](https://github.com/conductor-oss/python-sdk/actions/workflows/pull_request.yml/badge.svg)](https://github.com/conductor-oss/python-sdk/actions/workflows/pull_request.yml)
[![codecov](https://codecov.io/gh/conductor-oss/python-sdk/branch/main/graph/badge.svg?token=K10D161X4R)](https://codecov.io/gh/conductor-oss/python-sdk)

Python SDK for working with https://github.com/conductor-oss/conductor.

[Conductor](https://www.conductor-oss.org/) is the leading open-source orchestration platform allowing developers to build highly scalable distributed applications.

Check out the [official documentation for Conductor](https://orkes.io/content).

## ⭐ Conductor OSS

Show support for the Conductor OSS.  Please help spread the awareness by starring Conductor repo.

[![GitHub stars](https://img.shields.io/github/stars/conductor-oss/conductor.svg?style=social&label=Star&maxAge=)](https://GitHub.com/conductor-oss/conductor/)

## Conductor-OSS vs. Orkes Conductor

Conductor-OSS is the open-source version of the Conductor orchestration platform, maintained by the community and available for self-hosting. It provides a robust, extensible framework for building and managing workflows, ideal for developers who want full control over their deployment and customization.

Orkes Conductor, built on top of Conductor-OSS, is a fully-managed, cloud-hosted service provided by Orkes. It offers additional features such as a user-friendly UI, enterprise-grade security, scalability, and support, making it suitable for organizations seeking a turnkey solution without managing infrastructure.

## Quick Start

- [Installation](#installation)
- [Configuration](#configuration)
- [Hello World Example](#hello-world-example)
- [Documentation](#documentation)

## Installation

The SDK requires Python 3.9+. To install the SDK, use the following command:

```shell
python3 -m pip install conductor-python
```

For development setup, it's recommended to use a virtual environment:

```shell
virtualenv conductor
source conductor/bin/activate
python3 -m pip install conductor-python
```

## Configuration

### Basic Configuration

The SDK connects to `http://localhost:8080/api` by default. For other configurations:

```python
from conductor.client.configuration.configuration import Configuration

# Default configuration (localhost:8080)
config = Configuration()

# Custom server URL
config = Configuration(server_api_url="https://your-conductor-server.com/api")

# With authentication (for Orkes Conductor)
from conductor.shared.configuration.settings.authentication_settings import AuthenticationSettings
config = Configuration(
    server_api_url="https://your-cluster.orkesconductor.io/api",
    authentication_settings=AuthenticationSettings(
        key_id="your_key",
        key_secret="your_secret"
    )
)
```

### Environment Variables

You can also configure using environment variables:

```shell
export CONDUCTOR_SERVER_URL=https://your-conductor-server.com/api
export CONDUCTOR_AUTH_KEY=your_key
export CONDUCTOR_AUTH_SECRET=your_secret
```

## Hello World Example

Create a simple "Hello World" application that executes a "greetings" workflow:

### 1. Create a Worker

```python
from conductor.client.worker.worker_task import worker_task

@worker_task(task_definition_name='greet')
def greet(name: str) -> str:
    return f'Hello {name}'
```

### 2. Create a Workflow

```python
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from greetings_worker import greet

def greetings_workflow(workflow_executor: WorkflowExecutor) -> ConductorWorkflow:
    name = 'greetings'
    workflow = ConductorWorkflow(name=name, executor=workflow_executor)
    workflow.version = 1
    workflow >> greet(task_ref_name='greet_ref', name=workflow.input('name'))
    return workflow
```

### 3. Run the Application

```python
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from greetings_workflow import greetings_workflow

def main():
    # Connect to Conductor server
    api_config = Configuration()
    workflow_executor = WorkflowExecutor(configuration=api_config)
    
    # Register and create workflow
    workflow = greetings_workflow(workflow_executor)
    workflow.register(True)
    
    # Start workers
    task_handler = TaskHandler(configuration=api_config)
    task_handler.start_processes()
    
    # Execute workflow
    workflow_run = workflow_executor.execute(
        name=workflow.name, 
        version=workflow.version,
        workflow_input={'name': 'Orkes'}
    )
    
    print(f'Workflow result: {workflow_run.output["result"]}')
    task_handler.stop_processes()

if __name__ == '__main__':
    main()
```

### 4. Start Conductor Server

For local development, start Conductor using Docker:

```shell
docker run --init -p 8080:8080 -p 5000:5000 conductoross/conductor-standalone:3.15.0
```

View the workflow execution in the Conductor UI at http://localhost:5000.

## Documentation

For detailed information on specific topics, see the following documentation:

### Core Concepts
- **[Workers](docs/worker/README.md)** - Creating and managing Conductor workers
- **[Workflows](docs/workflow/README.md)** - Building and executing Conductor workflows
- **[Configuration](docs/configuration/)** - Advanced configuration options
  - [SSL/TLS Configuration](docs/configuration/ssl-tls.md) - Secure connections and certificates
  - [Proxy Configuration](docs/configuration/proxy.md) - Network proxy setup

### Development & Testing
- **[Testing](docs/testing/README.md)** - Testing workflows and workers
- **[Development](docs/development/README.md)** - Development setup and client regeneration
- **[Examples](docs/examples/)** - Complete working examples

### Production & Deployment
- **[Production](docs/production/)** - Production deployment guidelines
- **[Metadata](docs/metadata/README.md)** - Workflow and task metadata management
- **[Authorization](docs/authorization/README.md)** - Authentication and authorization
- **[Secrets](docs/secret/README.md)** - Secret management
- **[Scheduling](docs/schedule/README.md)** - Workflow scheduling

### Advanced Topics
- **[Advanced](docs/advanced/)** - Advanced features and patterns

## Examples

Check out the [examples directory](examples/) for complete working examples:

- [Hello World](examples/helloworld/) - Basic workflow example
- [Dynamic Workflow](examples/dynamic_workflow.py) - Dynamic workflow creation
- [Kitchen Sink](examples/kitchensink.py) - Comprehensive workflow features
- [Async Examples](examples/async/) - Asynchronous client examples
