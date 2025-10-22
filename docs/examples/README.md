# Examples

This section contains complete working examples demonstrating various features of the Conductor Python SDK.

## Table of Contents

- [Hello World](hello-world/) - Basic workflow example
- [Dynamic Workflow](../examples/dynamic_workflow.py) - Dynamic workflow creation
- [Kitchen Sink](../examples/kitchensink.py) - Comprehensive workflow features
- [Async Examples](../examples/async/) - Asynchronous client examples

## Quick Start Examples

### Basic Worker and Workflow

```python
from conductor.client.worker.worker_task import worker_task
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration

@worker_task(task_definition_name='greet')
def greet(name: str) -> str:
    return f'Hello {name}'

def main():
    config = Configuration()
    workflow_executor = WorkflowExecutor(configuration=config)

    workflow = ConductorWorkflow(name='greetings', executor=workflow_executor)
    workflow.version = 1
    workflow >> greet(task_ref_name='greet_ref', name=workflow.input('name'))

    workflow.register(True)

    task_handler = TaskHandler(configuration=config)
    task_handler.start_processes()

    result = workflow_executor.execute(
        name=workflow.name,
        version=workflow.version,
        workflow_input={'name': 'World'}
    )

    print(f'Result: {result.output["result"]}')
    task_handler.stop_processes()

if __name__ == '__main__':
    main()
```

## Example Categories

### Basic Examples
- **Hello World** - Simple worker and workflow
- **Dynamic Workflow** - Creating workflows programmatically
- **Kitchen Sink** - All supported features

### Advanced Examples
- **Async Examples** - Asynchronous client usage
- **SSL Examples** - Secure connections
- **Proxy Examples** - Network proxy configuration

### Integration Examples
- **Orkes Examples** - Orkes Conductor specific features
- **Multi-agent Examples** - Complex multi-agent workflows
- **AI Integration** - AI and machine learning workflows

## Running Examples

1. **Start Conductor Server**
   ```bash
   docker run --init -p 8080:8080 -p 5000:5000 conductoross/conductor-standalone:3.15.0
   ```

2. **Run an Example**
   ```bash
   python examples/helloworld/helloworld.py
   ```

3. **View in UI**
   Open http://localhost:5000 to see workflow execution

## Example Structure

```
examples/
├── helloworld/           # Basic examples
│   ├── helloworld.py
│   ├── greetings_workflow.py
│   └── greetings_worker.py
├── async/                # Async examples
│   ├── async_ssl_example.py
│   └── async_proxy_example.py
├── orkes/                # Orkes specific examples
│   ├── open_ai_chat_gpt.py
│   └── multiagent_chat.py
└── dynamic_workflow.py   # Dynamic workflow example
```

## Contributing Examples

When adding new examples:

1. **Follow the naming convention** - Use descriptive names
2. **Include documentation** - Add comments explaining the example
3. **Test thoroughly** - Ensure examples work with latest SDK
4. **Update this README** - Add new examples to the table of contents

## Troubleshooting Examples

### Common Issues

1. **Connection refused**
   - Ensure Conductor server is running
   - Check server URL configuration

2. **Import errors**
   - Verify SDK installation
   - Check Python path

3. **Authentication errors**
   - Verify API keys for Orkes examples
   - Check authentication configuration

### Getting Help

- Check the [main documentation](../README.md)
- Review [configuration guides](configuration/)
- Open an issue on GitHub
