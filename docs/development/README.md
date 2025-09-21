# Development

This section covers development setup, client regeneration, and contributing to the Conductor Python SDK.

## Table of Contents

- [Development Setup](#development-setup)
- [Client Regeneration](#client-regeneration)
- [Testing](#testing)
- [Contributing](#contributing)

## Development Setup

### Prerequisites

- Python 3.9+
- Git
- Docker (for running Conductor server locally)

### Local Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/conductor-oss/python-sdk.git
   cd python-sdk
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv conductor-dev
   source conductor-dev/bin/activate  # On Windows: conductor-dev\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -r requirements.dev.txt
   pip install -e .
   ```

4. **Start Conductor server locally**
   ```bash
   docker run --init -p 8080:8080 -p 5000:5000 conductoross/conductor-standalone:3.15.0
   ```

5. **Run tests**
   ```bash
   pytest tests/
   ```

## Client Regeneration

When updating to a new Orkes version, you may need to regenerate the client code to support new APIs and features. The SDK provides comprehensive guides for regenerating both sync and async clients:

### Sync Client Regeneration

For the synchronous client (`conductor.client`), see the [Client Regeneration Guide](../../src/conductor/client/CLIENT_REGENERATION_GUIDE.md) which covers:

- Creating swagger.json files for new Orkes versions
- Generating client code using Swagger Codegen
- Replacing models and API clients in the codegen folder
- Creating adapters and updating the proxy package
- Running backward compatibility, serialization, and integration tests

### Async Client Regeneration

For the asynchronous client (`conductor.asyncio_client`), see the [Async Client Regeneration Guide](../../src/conductor/asyncio_client/ASYNC_CLIENT_REGENERATION_GUIDE.md) which covers:

- Creating swagger.json files for new Orkes versions
- Generating async client code using OpenAPI Generator
- Replacing models and API clients in the http folder
- Creating adapters for backward compatibility
- Running async-specific tests and handling breaking changes

Both guides include detailed troubleshooting sections, best practices, and step-by-step instructions to ensure a smooth regeneration process while maintaining backward compatibility.

### Quick Regeneration Steps

1. **Generate swagger.json**
   ```bash
   # For sync client
   python scripts/generate_swagger.py --version 3.15.0 --output src/conductor/client/swagger.json
   
   # For async client
   python scripts/generate_swagger.py --version 3.15.0 --output src/conductor/asyncio_client/swagger.json
   ```

2. **Generate client code**
   ```bash
   # Sync client
   swagger-codegen generate -i src/conductor/client/swagger.json -l python -o src/conductor/client/codegen/
   
   # Async client
   openapi-generator generate -i src/conductor/asyncio_client/swagger.json -g python -o src/conductor/asyncio_client/http/
   ```

3. **Update adapters and run tests**
   ```bash
   python scripts/update_adapters.py
   pytest tests/
   ```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/backwardcompatibility/

# Run with coverage
pytest --cov=conductor --cov-report=html

# Run specific test file
pytest tests/unit/test_workflow.py

# Run with verbose output
pytest -v
```

### Test Categories

- **Unit Tests** (`tests/unit/`): Test individual components in isolation
- **Integration Tests** (`tests/integration/`): Test integration with Conductor server
- **Backward Compatibility Tests** (`tests/backwardcompatibility/`): Ensure API compatibility
- **Serialization Tests** (`tests/serdesertest/`): Test data serialization/deserialization

### Writing Tests

Follow the repository's testing guidelines:

1. **Use functions instead of classes** for test cases
2. **Remove comments and docstrings** from test code
3. **Follow the repository's style guides**
4. **Use descriptive test names**

Example test structure:

```python
def test_workflow_creation():
    workflow_executor = WorkflowExecutor(configuration=Configuration())
    workflow = ConductorWorkflow(name='test_workflow', executor=workflow_executor)
    assert workflow.name == 'test_workflow'

def test_worker_task_execution():
    @worker_task(task_definition_name='test_task')
    def test_task(input_data: str) -> str:
        return f"processed: {input_data}"
    
    result = test_task("test_input")
    assert result == "processed: test_input"
```

### Test Configuration

Create a `conftest.py` file for shared test configuration:

```python
import pytest
from conductor.client.configuration.configuration import Configuration

@pytest.fixture
def test_config():
    return Configuration(server_api_url="http://localhost:8080/api")

@pytest.fixture
def workflow_executor(test_config):
    from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
    return WorkflowExecutor(configuration=test_config)
```

## Contributing

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write clear, self-documenting code
- Add docstrings for public APIs

### Pull Request Process

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write tests for new functionality
   - Update documentation if needed
   - Ensure all tests pass

4. **Commit your changes**
   ```bash
   git commit -m "Add feature: brief description"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure CI checks pass

### Development Workflow

1. **Start Conductor server**
   ```bash
   docker run --init -p 8080:8080 -p 5000:5000 conductoross/conductor-standalone:3.15.0
   ```

2. **Run tests before committing**
   ```bash
   pytest tests/
   ```

3. **Check code formatting**
   ```bash
   black src/ tests/
   isort src/ tests/
   ```

4. **Run linting**
   ```bash
   flake8 src/ tests/
   mypy src/
   ```

### Debugging

#### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Your code here
```

#### Debug Conductor Server Connection

```python
from conductor.client.configuration.configuration import Configuration
import httpx

# Test server connectivity
config = Configuration()
try:
    response = httpx.get(f"{config.server_api_url}/health")
    print(f"Server status: {response.status_code}")
except Exception as e:
    print(f"Connection failed: {e}")
```

#### Debug Workflow Execution

```python
# Enable workflow execution logging
import logging
logging.getLogger("conductor.client.workflow").setLevel(logging.DEBUG)

# Your workflow code
```

### Release Process

1. **Update version numbers**
   - `setup.py`
   - `pyproject.toml`
   - `src/conductor/__init__.py`

2. **Update changelog**
   - Document new features
   - List bug fixes
   - Note breaking changes

3. **Create release tag**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

4. **Build and publish**
   ```bash
   python -m build
   twine upload dist/*
   ```

### Troubleshooting

#### Common Issues

1. **Import errors**
   - Check if virtual environment is activated
   - Verify package installation: `pip list | grep conductor`

2. **Connection errors**
   - Ensure Conductor server is running
   - Check server URL configuration
   - Verify network connectivity

3. **Test failures**
   - Check test environment setup
   - Verify test data and fixtures
   - Review test logs for specific errors

#### Getting Help

- Check existing [GitHub Issues](https://github.com/conductor-oss/python-sdk/issues)
- Create a new issue with detailed information
- Join the [Conductor Community](https://www.conductor-oss.org/community)
