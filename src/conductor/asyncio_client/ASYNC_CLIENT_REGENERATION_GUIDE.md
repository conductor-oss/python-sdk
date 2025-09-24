# Async Client Regeneration Guide

This guide provides step-by-step instructions for regenerating the Conductor Python SDK async client code when updating to a new Orkes version.

## Overview

The async client regeneration process involves:
1. Creating a new `swagger.json` file with API specifications for the new Orkes version
2. Generating async client code using OpenAPI Generator
3. Replacing old models and API clients in the `/asyncio_client/http` folder
4. Creating adapters in the `/asyncio_client/adapters` folder
5. Running async tests to verify backward compatibility and handle any breaking changes

## Prerequisites

- Access to the new Orkes version's API documentation or OpenAPI specification
- OpenAPI Generator installed and configured
- Python development environment with async support
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

## Step 2: Generate Async Client Using OpenAPI Generator

### 2.1 Install OpenAPI Generator

```bash
# Using npm
npm install -g @openapitools/openapi-generator-cli

# Or using Docker
docker pull openapitools/openapi-generator-cli
```

### 2.2 Generate Async Client Code

```bash
# Using openapi-generator-cli with async support
openapi-generator-cli generate \
  -i swagger.json \
  -g python \
  -o ./generated_async_client \
  --package-name conductor.asyncio_client.http \
  --additional-properties=packageName=conductor.asyncio_client.http,projectName=conductor-python-async-sdk,library=asyncio

# Or using Docker with async configuration
docker run --rm \
  -v ${PWD}:/local openapitools/openapi-generator-cli generate \
  -i /local/swagger.json \
  -g python \
  -o /local/generated_async_client \
  --package-name conductor.asyncio_client.http \
  --additional-properties=packageName=conductor.asyncio_client.http,library=asyncio
```

### 2.3 Verify Generated Code

Check that the generated code includes:
- Async API client classes in `generated_async_client/conductor/asyncio_client/http/api/`
- Model classes in `generated_async_client/conductor/asyncio_client/http/models/`
- Proper async/await patterns
- All required dependencies
- Pydantic model validation

## Step 3: Replace Old Models and API Clients

### 3.1 Backup Current HTTP Code

```bash
# Create backup of current http folder
cp -r src/conductor/asyncio_client/http src/conductor/asyncio_client/http.backup
```

### 3.2 Replace Generated Code

```bash
# Remove old http content
rm -rf src/conductor/asyncio_client/http/*

# Copy new generated code
cp -r generated_async_client/conductor/asyncio_client/http/* src/conductor/asyncio_client/http/

# Clean up generated client directory
rm -rf generated_async_client
```

### 3.3 Update Package Imports

Ensure all generated files have correct import statements:
- Update relative imports if needed
- Verify package structure matches expected layout
- Check for any missing async dependencies
- Ensure Pydantic imports are correct

## Step 4: Create Adapters

### 4.1 Create API Adapters

For each new or modified API client, create an adapter in `src/conductor/asyncio_client/adapters/api/`:

```python
# Example: src/conductor/asyncio_client/adapters/api/workflow_resource_api.py
from __future__ import annotations

from typing import Dict, Any, Union, Optional, Annotated, Tuple
from pydantic import validate_call, Field, StrictStr, StrictFloat, StrictInt
from conductor.asyncio_client.adapters.models.workflow_adapter import Workflow

from conductor.asyncio_client.http.api import WorkflowResourceApi

class WorkflowResourceApiAdapter(WorkflowResourceApi):
    @validate_call
    async def update_workflow_state(
        self,
        workflow_id: StrictStr,
        request_body: Dict[str, Any],
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)], 
                Annotated[StrictFloat, Field(gt=0)]
            ],
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> Workflow:
        """Update workflow variables with backward compatibility"""
        # Add any custom logic or backward compatibility methods here
        return await super().update_workflow_state(
            workflow_id=workflow_id,
            request_body=request_body,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )
```

### 4.2 Create Model Adapters (if needed)

For new or modified models, create adapters in `src/conductor/asyncio_client/adapters/models/`:

```python
# Example: src/conductor/asyncio_client/adapters/models/workflow_adapter.py
from __future__ import annotations
from typing import Optional, Dict, Any
from pydantic import Field, validator
from conductor.asyncio_client.http.models.workflow import Workflow

class WorkflowAdapter(Workflow):
    """Workflow model with backward compatibility support"""
    
    # Add backward compatibility fields if needed
    legacy_field: Optional[str] = Field(None, alias="oldFieldName")
    
    @validator('legacy_field', pre=True)
    def handle_legacy_field(cls, v, values):
        """Handle legacy field mapping"""
        if v is not None:
            # Map legacy field to new field structure
            return v
        return v
    
    def to_legacy_dict(self) -> Dict[str, Any]:
        """Convert to legacy dictionary format for backward compatibility"""
        data = self.dict()
        # Add any legacy field mappings
        if hasattr(self, 'legacy_field') and self.legacy_field:
            data['oldFieldName'] = self.legacy_field
        return data
```

### 4.3 Update Adapter Imports

Update the main adapters `__init__.py` file to include new adapters:

```python
# src/conductor/asyncio_client/adapters/__init__.py
from conductor.asyncio_client.adapters.api_client_adapter import ApiClientAdapter as ApiClient

# Import all API adapters
from conductor.asyncio_client.adapters.api.workflow_resource_api import WorkflowResourceApiAdapter
from conductor.asyncio_client.adapters.api.task_resource_api import TaskResourceApiAdapter
# ... add other adapters as needed

__all__ = [
    "ApiClient",
    "WorkflowResourceApiAdapter", 
    "TaskResourceApiAdapter",
    # ... add other adapters
]
```

### 4.4 Update Orkes Base Client

Update the `OrkesBaseClient` to use new adapters:

```python
# src/conductor/asyncio_client/orkes/orkes_base_client.py
from conductor.asyncio_client.adapters.api.workflow_resource_api import WorkflowResourceApiAdapter
from conductor.asyncio_client.adapters.api.task_resource_api import TaskResourceApiAdapter
# ... import other adapters

class OrkesBaseClient:
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        # ... existing code ...
        
        # Initialize all API clients with adapters
        self.metadata_api = MetadataResourceApiAdapter(self.api_client)
        self.task_api = TaskResourceApiAdapter(self.api_client)
        self.workflow_api = WorkflowResourceApiAdapter(self.api_client)
        # ... update other API initializations
```

## Step 5: Run Tests and Handle Breaking Changes

### 5.1 Run Async Unit Tests

```bash
# Run all async unit tests
python -m pytest tests/unit/orkes/test_async_* -v

# Run specific async client tests
python -m pytest tests/unit/orkes/test_async_workflow_client.py -v
python -m pytest tests/unit/orkes/test_async_task_client.py -v
python -m pytest tests/unit/orkes/test_async_authorization_client.py -v
```

### 5.2 Run Async Integration Tests

```bash
# Run async integration tests
python -m pytest tests/integration/client/test_async.py -v

# Run async workflow tests
python -m pytest tests/unit/workflow/test_async_workflow_executor.py -v
python -m pytest tests/unit/workflow/test_async_conductor_workflow.py -v
```

### 5.3 Run Serialization/Deserialization Tests

```bash
# Run all serdeser tests (includes async models)
python -m pytest tests/serdesertest/ -v

# Run pydantic-specific tests
python -m pytest tests/serdesertest/pydantic/ -v
```

### 5.4 Run AI and Telemetry Tests

```bash
# Run async AI orchestrator tests
python -m pytest tests/unit/ai/test_async_ai_orchestrator.py -v

# Run async metrics collector tests
python -m pytest tests/unit/telemetry/test_async_metrics_collector.py -v

# Run async event client tests
python -m pytest tests/unit/event/test_async_event_client.py -v
```

### 5.5 Handle Breaking Changes

If tests fail due to breaking changes:

1. **Identify Breaking Changes**:
   - Review async test failures
   - Check for removed async methods or changed signatures
   - Identify modified model structures
   - Verify Pydantic validation changes

2. **Update Async Adapters**:
   - Add backward compatibility methods to adapters
   - Implement deprecated method aliases
   - Handle parameter changes with default values
   - Ensure async/await patterns are maintained

3. **Example Async Adapter Update**:
   ```python
   class WorkflowResourceApiAdapter(WorkflowResourceApi):
       async def start_workflow_legacy(
           self, 
           workflow_id: str, 
           input_data: Optional[Dict] = None, 
           **kwargs
       ) -> str:
           """Backward compatibility method for old start_workflow signature"""
           # Convert old parameters to new format
           start_request = StartWorkflowRequest(
               name=workflow_id,
               input=input_data,
               **kwargs
           )
           result = await self.start_workflow(start_request)
           return result.workflow_id
       
       # Alias for backward compatibility
       start_workflow_v1 = start_workflow_legacy
   ```

4. **Update Async Tests**:
   - Add tests for new async functionality
   - Update existing async tests if needed
   - Ensure backward compatibility tests pass
   - Verify async context managers work correctly

### 5.6 Final Verification

```bash
# Run all async-related tests
python -m pytest tests/unit/orkes/test_async_* tests/unit/workflow/test_async_* tests/unit/ai/test_async_* tests/unit/telemetry/test_async_* tests/unit/event/test_async_* -v

# Run integration tests
python -m pytest tests/integration/client/test_async.py -v

# Check for any linting issues
python -m flake8 src/conductor/asyncio_client/
python -m mypy src/conductor/asyncio_client/
```

## Troubleshooting

### Common Issues

1. **Async Import Errors**: Check that all generated files have correct async imports
2. **Pydantic Validation Errors**: Ensure model adapters handle validation correctly
3. **Missing Async Dependencies**: Verify all required async packages are installed
4. **Test Failures**: Review adapter implementations for missing backward compatibility
5. **Model Changes**: Update adapters to handle structural changes in async models

### Recovery Steps

If the regeneration process fails:

1. **Restore Backup**:
   ```bash
   rm -rf src/conductor/asyncio_client/http
   mv src/conductor/asyncio_client/http.backup src/conductor/asyncio_client/http
   ```

2. **Incremental Updates**: Instead of full replacement, update specific async APIs one at a time

3. **Manual Fixes**: Apply targeted fixes to specific async adapters or models

## Best Practices

1. **Version Control**: Always commit changes before starting regeneration
2. **Async Patterns**: Maintain proper async/await patterns throughout
3. **Pydantic Validation**: Ensure all models use proper Pydantic validation
4. **Incremental Updates**: Test each async API client individually when possible
5. **Documentation**: Update API documentation for any new async features
6. **Backward Compatibility**: Prioritize maintaining existing async API contracts
7. **Testing**: Run async tests frequently during the regeneration process

## File Structure Reference

```
src/conductor/asyncio_client/
├── http/                      # Generated async client code (replaced in step 3)
│   ├── api/                   # Generated async API clients
│   ├── models/                # Generated async model classes
│   ├── api_client.py          # Generated async API client base
│   └── rest.py                # Generated async REST client
├── adapters/                  # Adapter layer (created in step 4)
│   ├── api/                   # Async API client adapters
│   ├── models/                # Async model adapters
│   └── api_client_adapter.py  # Async API client adapter
├── orkes/                     # Orkes-specific async implementations
│   ├── orkes_*_client.py      # Orkes async client implementations
│   └── orkes_base_client.py   # Base async client
├── configuration/             # Async configuration
└── workflow/                  # Async workflow components
    └── executor/              # Async workflow executor
```

## Testing Structure Reference

```
tests/
├── unit/
│   ├── orkes/
│   │   └── test_async_*_client.py    # Async client unit tests
│   ├── workflow/
│   │   └── test_async_*              # Async workflow tests
│   ├── ai/
│   │   └── test_async_ai_orchestrator.py
│   ├── telemetry/
│   │   └── test_async_metrics_collector.py
│   └── event/
│       └── test_async_event_client.py
├── integration/
│   └── client/
│       └── test_async.py             # Async integration tests
└── serdesertest/
    └── pydantic/                     # Pydantic model tests
```

## Key Differences from Sync Client

1. **No Proxy Package**: The async client uses direct imports from adapters
2. **OpenAPI Generator**: Uses OpenAPI Generator instead of Swagger Codegen
3. **Pydantic Models**: All models use Pydantic for validation
4. **Async/Await**: All methods are async and use proper async patterns
5. **Direct Adapter Usage**: Orkes clients directly use adapters without proxy layer

This guide ensures a systematic approach to async client regeneration while maintaining backward compatibility and proper async patterns.
