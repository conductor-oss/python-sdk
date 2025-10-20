# Client Regeneration Guide

This guide provides step-by-step instructions for regenerating the Conductor Python SDK client code when updating to a new Orkes version.

## Overview

The client regeneration process involves:
1. Creating a new `swagger.json` file with API specifications for the new Orkes version
2. Generating client code using Swagger Codegen
3. Replacing old models and API clients in the `/client/codegen` folder
4. Creating adapters in the `/client/adapters` folder and importing them in the proxy package
5. Running tests to verify backward compatibility and handle any breaking changes

## Prerequisites

- Access to the new Orkes version's API documentation or OpenAPI specification
- Swagger Codegen installed and configured
- Python development environment set up
- Access to the Conductor Python SDK repository

## Step 1: Create swagger.json File

### 1.1 Obtain API Specification

1. **From Orkes Documentation**: Download the OpenAPI/Swagger specification for the new Orkes version
2. **From API Endpoint**: If available, fetch the specification from `{orkes_url}/api-docs` or similar endpoint
3. **Manual Creation**: If needed, create the specification manually based on API documentation

### 1.2 Validate swagger.json

Ensure the `swagger.json` file:
- Is valid JSON format
- Contains all required API endpoints
- Includes proper model definitions
- Has correct version information

```bash
# Validate JSON syntax
python -m json.tool swagger.json > /dev/null

# Check for required fields
jq '.info.version' swagger.json
jq '.paths | keys | length' swagger.json
```

## Step 2: Generate Client Using Swagger Codegen

### 2.1 Install Swagger Codegen

```bash
# Using npm
npm install -g @openapitools/openapi-generator-cli

# Or using Docker
docker pull openapitools/openapi-generator-cli
```

### 2.2 Generate Client Code

```bash
# Using openapi-generator-cli
openapi-generator-cli generate \
  -i swagger.json \
  -g python \
  -o ./generated_client \
  --package-name conductor.client.codegen \
  --additional-properties=packageName=conductor.client.codegen,projectName=conductor-python-sdk

# Or using Docker
docker run --rm \
  -v ${PWD}:/local openapitools/openapi-generator-cli generate \
  -i /local/swagger.json \
  -g python \
  -o /local/generated_client \
  --package-name conductor.client.codegen
```

### 2.3 Verify Generated Code

Check that the generated code includes:
- API client classes in `generated_client/conductor/client/codegen/api/`
- Model classes in `generated_client/conductor/client/codegen/models/`
- Proper package structure
- All required dependencies

## Step 3: Replace Old Models and API Clients

### 3.1 Backup Current Codegen

```bash
# Create backup of current codegen folder
cp -r src/conductor/client/codegen src/conductor/client/codegen.backup
```

### 3.2 Replace Generated Code

```bash
# Remove old codegen content
rm -rf src/conductor/client/codegen/*

# Copy new generated code
cp -r generated_client/conductor/client/codegen/* src/conductor/client/codegen/

# Clean up generated client directory
rm -rf generated_client
```

### 3.3 Update Package Imports

Ensure all generated files have correct import statements:
- Update relative imports if needed
- Verify package structure matches expected layout
- Check for any missing dependencies

## Step 4: Create Adapters and Update Proxy Package

### 4.1 Create API Adapters

For each new or modified API client, create an adapter in `src/conductor/client/adapters/api/`:

```python
# Example: src/conductor/client/adapters/api/workflow_resource_api_adapter.py
from conductor.client.codegen.api.workflow_resource_api import WorkflowResourceApi

class WorkflowResourceApiAdapter(WorkflowResourceApi):
    # Add any custom logic or backward compatibility methods here
    pass
```

### 4.2 Create Model Adapters (if needed)

For new or modified models, create adapters in `src/conductor/client/adapters/models/`:

```python
# Example: src/conductor/client/adapters/models/workflow_adapter.py
from conductor.client.codegen.models.workflow import Workflow

class WorkflowAdapter(Workflow):
    # Add backward compatibility methods or custom logic
    pass
```

### 4.3 Update HTTP Proxy Package

Update the corresponding files in `src/conductor/client/http/api/` to import from adapters:

```python
# Example: src/conductor/client/http/api/workflow_resource_api.py
from conductor.client.adapters.api.workflow_resource_api_adapter import WorkflowResourceApiAdapter

WorkflowResourceApi = WorkflowResourceApiAdapter

__all__ = ["WorkflowResourceApi"]
```

### 4.4 Update Model Imports

Update model imports in `src/conductor/client/http/models/`:

```python
# Example: src/conductor/client/http/models/workflow.py
from conductor.client.adapters.models.workflow_adapter import WorkflowAdapter

Workflow = WorkflowAdapter

__all__ = ["Workflow"]
```

## Step 5: Run Tests and Handle Breaking Changes

### 5.1 Run Backward Compatibility Tests

```bash
# Run all backward compatibility tests
python -m pytest tests/backwardcompatibility/ -v

# Run specific test categories
python -m pytest tests/backwardcompatibility/test_bc_workflow.py -v
python -m pytest tests/backwardcompatibility/test_bc_task.py -v
```

### 5.2 Run Serialization/Deserialization Tests

```bash
# Run all serdeser tests
python -m pytest tests/serdesertest/ -v

# Run pydantic-specific tests
python -m pytest tests/serdesertest/pydantic/ -v
```

### 5.3 Run Integration Tests

```bash
# Run all integration tests
python -m pytest tests/integration/ -v

# Run specific integration tests
python -m pytest tests/integration/test_orkes_workflow_client_integration.py -v
python -m pytest tests/integration/test_orkes_task_client_integration.py -v
```

### 5.4 Handle Breaking Changes

If tests fail due to breaking changes:

1. **Identify Breaking Changes**:
   - Review test failures
   - Check for removed methods or changed signatures
   - Identify modified model structures

2. **Update Adapters**:
   - Add backward compatibility methods to adapters
   - Implement deprecated method aliases
   - Handle parameter changes with default values

3. **Example Adapter Update**:
   ```python
   class WorkflowResourceApiAdapter(WorkflowResourceApi):
       def start_workflow_legacy(self, workflow_id, input_data=None, **kwargs):
           """Backward compatibility method for old start_workflow signature"""
           # Convert old parameters to new format
           start_request = StartWorkflowRequest(
               name=workflow_id,
               input=input_data,
               **kwargs
           )
           return self.start_workflow(start_request)

       # Alias for backward compatibility
       start_workflow_v1 = start_workflow_legacy
   ```

4. **Update Tests**:
   - Add tests for new functionality
   - Update existing tests if needed
   - Ensure backward compatibility tests pass

### 5.5 Final Verification

```bash
# Run all tests to ensure everything works
python -m pytest tests/ -v

# Run specific test suites
python -m pytest tests/backwardcompatibility/ tests/serdesertest/ tests/integration/ -v

# Check for any linting issues
python -m flake8 src/conductor/client/
python -m mypy src/conductor/client/
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Check that all generated files have correct package imports
2. **Missing Dependencies**: Ensure all required packages are installed
3. **Test Failures**: Review adapter implementations for missing backward compatibility
4. **Model Changes**: Update adapters to handle structural changes in models

### Recovery Steps

If the regeneration process fails:

1. **Restore Backup**:
   ```bash
   rm -rf src/conductor/client/codegen
   mv src/conductor/client/codegen.backup src/conductor/client/codegen
   ```

2. **Incremental Updates**: Instead of full replacement, update specific APIs one at a time

3. **Manual Fixes**: Apply targeted fixes to specific adapters or models

## Best Practices

1. **Version Control**: Always commit changes before starting regeneration
2. **Incremental Updates**: Test each API client individually when possible
3. **Documentation**: Update API documentation for any new features
4. **Backward Compatibility**: Prioritize maintaining existing API contracts
5. **Testing**: Run tests frequently during the regeneration process

## File Structure Reference

```
src/conductor/client/
├── codegen/                    # Generated client code (replaced in step 3)
│   ├── api/                   # Generated API clients
│   ├── models/                # Generated model classes
│   └── api_client.py          # Generated API client base
├── adapters/                  # Adapter layer (created in step 4)
│   ├── api/                   # API client adapters
│   └── models/                # Model adapters
├── http/                      # Proxy package (updated in step 4)
│   ├── api/                   # Imports from adapters
│   └── models/                # Imports from adapters
└── orkes/                     # Orkes-specific implementations
    ├── orkes_*_client.py      # Orkes client implementations
    └── models/                # Orkes-specific models
```

## Testing Structure Reference

```
tests/
├── backwardcompatibility/     # Tests for backward compatibility
├── serdesertest/             # Serialization/deserialization tests
│   └── pydantic/             # Pydantic-specific tests
└── integration/              # Integration tests
    ├── test_orkes_*_client_integration.py
    └── test_conductor_oss_workflow_integration.py
```

This guide ensures a systematic approach to client regeneration while maintaining backward compatibility and code quality.
