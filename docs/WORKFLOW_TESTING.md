# Workflow Testing API Reference

Complete guide for testing Conductor workflows and workers in Python SDK.

> 📚 **Complete Working Example**: See [test_workflows.py](../examples/test_workflows.py) for comprehensive testing patterns.

## Quick Start

```python
import unittest
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.workflow_test_request import WorkflowTestRequest
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient

# Initialize client
configuration = Configuration(
    server_api_url="http://localhost:8080/api",
    debug=False
)
workflow_client = OrkesWorkflowClient(configuration)

# Create test request with mocked outputs
test_request = WorkflowTestRequest(
    name="order_processing",
    version=1,
    input={"order_id": "TEST-123", "amount": 99.99},
    task_ref_to_mock_output={
        "validate_order": [{
            "status": "COMPLETED",
            "output": {"valid": True, "customer_id": "CUST-456"}
        }],
        "process_payment": [{
            "status": "COMPLETED",
            "output": {"payment_id": "PAY-789", "status": "success"}
        }]
    }
)

# Run the test
execution = workflow_client.test_workflow(test_request)

# Verify results
assert execution.status == "COMPLETED"
assert execution.output["payment_id"] == "PAY-789"
print(f"Test passed! Workflow completed with {len(execution.tasks)} tasks")
```

## Quick Links

- [Testing Strategies](#testing-strategies)
- [Workflow Testing API](#workflow-testing-api)
- [Worker Testing](#worker-testing)
- [Mocking Task Outputs](#mocking-task-outputs)
- [Test Scenarios](#test-scenarios)
- [Model Reference](#model-reference)
- [Best Practices](#best-practices)

## Testing Strategies

### Testing Pyramid

| Level | What to Test | Tools | Speed |
|-------|-------------|-------|--------|
| **Unit Tests** | Individual worker functions | unittest/pytest | Fast (ms) |
| **Integration Tests** | Workflow logic with mocks | test_workflow API | Fast (seconds) |
| **End-to-End Tests** | Complete workflow execution | Real workers | Slow (minutes) |
| **Performance Tests** | Scalability and throughput | Load testing tools | Variable |

## Workflow Testing API

Test workflows without running actual workers using mocked task outputs.

| Method | Description | Use Case |
|--------|-------------|----------|
| `test_workflow()` | Execute workflow with mocked outputs | Integration testing |

---

## API Details

### Test Workflow

Execute a workflow with mocked task outputs for testing.

```python
from conductor.client.http.models.workflow_test_request import WorkflowTestRequest
from conductor.client.http.models.workflow_def import WorkflowDef

# Option 1: Test existing workflow
test_request = WorkflowTestRequest(
    name="existing_workflow",
    version=1,
    input={"test": "data"},
    task_ref_to_mock_output={
        "task_ref_1": [{"status": "COMPLETED", "output": {"result": "success"}}]
    }
)

# Option 2: Test workflow definition
workflow_def = WorkflowDef(
    name="test_workflow",
    version=1,
    tasks=[...]  # Task definitions
)

test_request = WorkflowTestRequest(
    workflow_def=workflow_def,
    input={"test": "data"},
    task_ref_to_mock_output={...}
)

# Execute test
execution = workflow_client.test_workflow(test_request)

# Verify execution
assert execution.status == "COMPLETED"
assert len(execution.tasks) == expected_task_count
```

**Parameters:**
- `name` (str, optional): Workflow name (if testing existing)
- `version` (int, optional): Workflow version
- `workflow_def` (WorkflowDef, optional): Inline workflow definition
- `input` (dict, optional): Workflow input parameters
- `task_ref_to_mock_output` (dict, required): Mock outputs by task reference

**Returns:** `Workflow` execution object with results

---

## Worker Testing

### Unit Testing Workers

Test worker functions as regular Python functions.

```python
import unittest
from my_workers import process_order, validate_customer

class WorkerUnitTests(unittest.TestCase):

    def test_process_order_success(self):
        """Test successful order processing"""
        result = process_order(
            order_id="ORD-123",
            items=[{"sku": "ABC", "qty": 2}],
            total=49.99
        )

        self.assertEqual(result["status"], "processed")
        self.assertIn("confirmation_number", result)

    def test_process_order_invalid_input(self):
        """Test order processing with invalid input"""
        with self.assertRaises(ValueError):
            process_order(order_id=None, items=[], total=-10)

    def test_validate_customer(self):
        """Test customer validation"""
        result = validate_customer(customer_id="CUST-456")

        self.assertTrue(result["valid"])
        self.assertEqual(result["tier"], "gold")

# Run tests
if __name__ == "__main__":
    unittest.main()
```

### Testing Async Workers

Test async worker functions with asyncio.

```python
import asyncio
import unittest
from my_async_workers import fetch_user_data, send_notification

class AsyncWorkerTests(unittest.TestCase):

    def test_fetch_user_data(self):
        """Test async user data fetching"""
        async def run_test():
            result = await fetch_user_data(user_id="USER-123")
            self.assertIn("email", result)
            self.assertIn("preferences", result)

        asyncio.run(run_test())

    def test_send_notification(self):
        """Test async notification sending"""
        async def run_test():
            result = await send_notification(
                user_id="USER-123",
                message="Test notification"
            )
            self.assertTrue(result["sent"])
            self.assertIsNotNone(result["message_id"])

        asyncio.run(run_test())
```

### Testing Worker with Task Context

Test workers that use task context.

```python
from unittest.mock import MagicMock, patch
from conductor.client.http.models import Task

def test_worker_with_context():
    """Test worker that uses task context"""

    # Create mock task
    mock_task = Task(
        task_id="test-task-123",
        workflow_instance_id="wf-456",
        retry_count=2,
        poll_count=5,
        input_data={"key": "value"}
    )

    # Mock get_task_context
    with patch('conductor.client.context.task_context.get_task_context') as mock_context:
        mock_context.return_value = MagicMock(
            get_task_id=lambda: mock_task.task_id,
            get_retry_count=lambda: mock_task.retry_count,
            get_poll_count=lambda: mock_task.poll_count
        )

        # Call worker
        from my_workers import context_aware_worker
        result = context_aware_worker(input_data={"test": "data"})

        # Verify behavior based on context
        assert result["retry_count"] == 2
        assert result["poll_count"] == 5
```

---

## Mocking Task Outputs

### Basic Mocking

Mock simple task outputs for testing.

```python
# Single successful output
task_ref_to_mock_output = {
    "validate_input": [{
        "status": "COMPLETED",
        "output": {"valid": True, "score": 95}
    }],

    "process_data": [{
        "status": "COMPLETED",
        "output": {"processed_count": 100}
    }]
}
```

### Simulating Retries

Test retry behavior with multiple outputs.

```python
# First attempt fails, second succeeds
task_ref_to_mock_output = {
    "unreliable_task": [
        {
            "status": "FAILED",
            "output": {},
            "reasonForIncompletion": "Temporary network error"
        },
        {
            "status": "COMPLETED",
            "output": {"data": "success on retry"}
        }
    ]
}
```

### Testing Decision Logic

Mock outputs to test different workflow paths.

```python
# Test switch/decision branches
def test_decision_path_a():
    mock_output = {
        "check_condition": [{
            "status": "COMPLETED",
            "output": {"path": "A", "value": 100}
        }],
        "task_path_a": [{
            "status": "COMPLETED",
            "output": {"result": "path A executed"}
        }]
    }
    # Task path B should not be in mock since it won't execute

def test_decision_path_b():
    mock_output = {
        "check_condition": [{
            "status": "COMPLETED",
            "output": {"path": "B", "value": 50}
        }],
        "task_path_b": [{
            "status": "COMPLETED",
            "output": {"result": "path B executed"}
        }]
    }
```

### Testing Loops

Mock outputs for loop iterations.

```python
# Mock outputs for DO_WHILE loop
task_ref_to_mock_output = {
    "loop_task__1": [{  # First iteration
        "status": "COMPLETED",
        "output": {"continue": True, "count": 1}
    }],
    "loop_task__2": [{  # Second iteration
        "status": "COMPLETED",
        "output": {"continue": True, "count": 2}
    }],
    "loop_task__3": [{  # Third iteration
        "status": "COMPLETED",
        "output": {"continue": False, "count": 3}
    }]
}
```

---

## Test Scenarios

### Complete Integration Test

```python
import json
import unittest
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.workflow_test_request import WorkflowTestRequest
from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient

class WorkflowIntegrationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = Configuration(server_api_url="http://localhost:8080/api")
        cls.workflow_client = OrkesWorkflowClient(cls.config)

    def test_order_processing_workflow(self):
        """Test complete order processing workflow"""

        # Define workflow
        workflow_def = self._create_order_workflow()

        # Create test input
        test_input = {
            "order_id": "TEST-ORD-123",
            "customer_id": "CUST-456",
            "items": [
                {"sku": "PROD-1", "quantity": 2, "price": 29.99},
                {"sku": "PROD-2", "quantity": 1, "price": 49.99}
            ],
            "total": 109.97
        }

        # Mock task outputs
        task_mocks = {
            "validate_customer": [{
                "status": "COMPLETED",
                "output": {
                    "valid": True,
                    "customer_tier": "gold",
                    "credit_limit": 1000.00
                }
            }],

            "check_inventory": [{
                "status": "COMPLETED",
                "output": {
                    "available": True,
                    "warehouse": "EAST-1"
                }
            }],

            "calculate_discount": [{
                "status": "COMPLETED",
                "output": {
                    "discount_percent": 10,
                    "final_amount": 98.97
                }
            }],

            "process_payment": [
                {  # First attempt fails
                    "status": "FAILED",
                    "reasonForIncompletion": "Payment gateway timeout"
                },
                {  # Retry succeeds
                    "status": "COMPLETED",
                    "output": {
                        "payment_id": "PAY-789",
                        "status": "approved",
                        "charged_amount": 98.97
                    }
                }
            ],

            "create_shipment": [{
                "status": "COMPLETED",
                "output": {
                    "tracking_number": "TRACK-12345",
                    "carrier": "FedEx",
                    "estimated_delivery": "2024-01-20"
                }
            }],

            "send_confirmation": [{
                "status": "COMPLETED",
                "output": {
                    "email_sent": True,
                    "sms_sent": True
                }
            }]
        }

        # Create test request
        test_request = WorkflowTestRequest(
            workflow_def=workflow_def,
            input=test_input,
            task_ref_to_mock_output=task_mocks
        )

        # Execute test
        execution = self.workflow_client.test_workflow(test_request)

        # Assertions
        self.assertEqual(execution.status, "COMPLETED")
        self.assertEqual(execution.input["order_id"], "TEST-ORD-123")

        # Verify all expected tasks executed
        task_names = [task.reference_task_name for task in execution.tasks]
        self.assertIn("validate_customer", task_names)
        self.assertIn("process_payment", task_names)
        self.assertIn("create_shipment", task_names)

        # Verify payment retry
        payment_tasks = [t for t in execution.tasks if t.reference_task_name == "process_payment"]
        self.assertEqual(len(payment_tasks), 2)  # Failed + retry
        self.assertEqual(payment_tasks[0].status, "FAILED")
        self.assertEqual(payment_tasks[1].status, "COMPLETED")

        # Verify workflow output
        self.assertIn("tracking_number", execution.output)
        self.assertEqual(execution.output["tracking_number"], "TRACK-12345")

    def _create_order_workflow(self):
        """Helper to create workflow definition"""
        # Implementation would create actual workflow def
        # This is simplified for example
        return WorkflowDef(
            name="order_processing_test",
            version=1,
            tasks=[...]  # Task definitions
        )
```

### Testing Error Scenarios

```python
def test_workflow_failure_handling(self):
    """Test workflow behavior with failures"""

    # Mock a terminal failure
    task_mocks = {
        "critical_task": [{
            "status": "FAILED_WITH_TERMINAL_ERROR",
            "output": {},
            "reasonForIncompletion": "Critical validation failed"
        }]
    }

    test_request = WorkflowTestRequest(
        name="failure_test_workflow",
        input={"test": True},
        task_ref_to_mock_output=task_mocks
    )

    execution = self.workflow_client.test_workflow(test_request)

    # Verify workflow failed
    self.assertEqual(execution.status, "FAILED")
    self.assertIn("Critical validation failed", execution.reason_for_incompletion)
```

### Testing Timeouts

```python
def test_workflow_timeout(self):
    """Test workflow timeout behavior"""

    # Mock a task that times out
    task_mocks = {
        "long_running_task": [{
            "status": "TIMED_OUT",
            "output": {},
            "reasonForIncompletion": "Task execution timed out after 60 seconds"
        }]
    }

    test_request = WorkflowTestRequest(
        name="timeout_test_workflow",
        input={"timeout_seconds": 60},
        task_ref_to_mock_output=task_mocks
    )

    execution = self.workflow_client.test_workflow(test_request)

    # Verify timeout handling
    timed_out_task = next(t for t in execution.tasks if t.status == "TIMED_OUT")
    self.assertIsNotNone(timed_out_task)
```

---

## Model Reference

### WorkflowTestRequest

Request object for workflow testing.

```python
class WorkflowTestRequest:
    name: Optional[str]                    # Workflow name (existing)
    version: Optional[int]                  # Workflow version
    workflow_def: Optional[WorkflowDef]    # Inline workflow definition
    input: Optional[dict]                   # Workflow input
    task_ref_to_mock_output: dict          # Mock outputs by task ref
    task_to_domain: Optional[dict]         # Task domain mapping
    correlation_id: Optional[str]          # Correlation identifier
    workflow_id: Optional[str]             # Specific workflow ID
```

### Mock Output Format

Structure for mocked task outputs.

```python
{
    "task_reference_name": [
        {
            "status": "COMPLETED",              # Task status
            "output": {...},                    # Task output data
            "reasonForIncompletion": "...",     # Failure reason (optional)
            "logs": ["log1", "log2"],          # Task logs (optional)
            "externalOutputPayloadStoragePath": "..." # External storage (optional)
        }
    ]
}
```

### Task Status Values

Valid status values for mocked tasks.

| Status | Description | Workflow Continues |
|--------|-------------|-------------------|
| `COMPLETED` | Task succeeded | Yes |
| `FAILED` | Task failed (will retry) | Yes (after retries) |
| `FAILED_WITH_TERMINAL_ERROR` | Task failed (no retry) | No |
| `IN_PROGRESS` | Task still running | Wait |
| `TIMED_OUT` | Task timed out | Depends on config |
| `SKIPPED` | Task was skipped | Yes |

---

## Best Practices

### 1. Test Organization

```python
# ✅ Good: Organized test structure
tests/
├── unit/
│   ├── test_workers.py         # Worker unit tests
│   ├── test_validators.py      # Validation logic tests
│   └── test_transformers.py    # Data transformation tests
├── integration/
│   ├── test_workflows.py       # Workflow integration tests
│   ├── test_decisions.py       # Decision logic tests
│   └── test_retries.py        # Retry behavior tests
└── e2e/
    └── test_full_flow.py      # End-to-end tests
```

### 2. Test Data Management

```python
# ✅ Good: Reusable test data
class TestData:
    """Centralized test data management"""

    @staticmethod
    def valid_order():
        return {
            "order_id": "TEST-" + str(uuid.uuid4())[:8],
            "customer_id": "CUST-123",
            "items": [{"sku": "TEST-SKU", "qty": 1}],
            "total": 99.99
        }

    @staticmethod
    def invalid_order():
        return {
            "order_id": None,
            "items": [],
            "total": -1
        }

    @staticmethod
    def mock_payment_success():
        return {
            "status": "COMPLETED",
            "output": {
                "payment_id": "PAY-" + str(uuid.uuid4())[:8],
                "status": "approved"
            }
        }
```

### 3. Parameterized Testing

```python
import pytest

# ✅ Good: Test multiple scenarios
@pytest.mark.parametrize("input_data,expected_status", [
    ({"amount": 100}, "COMPLETED"),
    ({"amount": -1}, "FAILED"),
    ({"amount": None}, "FAILED"),
    ({"amount": 1000000}, "FAILED_WITH_TERMINAL_ERROR"),
])
def test_payment_processing(input_data, expected_status):
    """Test payment processing with various inputs"""
    result = process_payment(input_data)
    assert result["status"] == expected_status
```

### 4. Mock Builders

```python
# ✅ Good: Fluent mock builders
class MockBuilder:
    """Build mock task outputs fluently"""

    def __init__(self):
        self.mocks = {}

    def add_success(self, task_ref: str, output: dict):
        self.mocks[task_ref] = [{
            "status": "COMPLETED",
            "output": output
        }]
        return self

    def add_failure(self, task_ref: str, reason: str):
        self.mocks[task_ref] = [{
            "status": "FAILED",
            "reasonForIncompletion": reason
        }]
        return self

    def add_retry(self, task_ref: str, failure_reason: str, success_output: dict):
        self.mocks[task_ref] = [
            {"status": "FAILED", "reasonForIncompletion": failure_reason},
            {"status": "COMPLETED", "output": success_output}
        ]
        return self

    def build(self):
        return self.mocks

# Usage
mocks = (MockBuilder()
    .add_success("validate", {"valid": True})
    .add_retry("payment", "Timeout", {"payment_id": "123"})
    .add_success("notify", {"sent": True})
    .build())
```

### 5. Assertion Helpers

```python
# ✅ Good: Custom assertions
class WorkflowAssertions:
    """Helper assertions for workflow testing"""

    @staticmethod
    def assert_task_executed(execution, task_ref: str):
        """Assert a specific task was executed"""
        task_refs = [t.reference_task_name for t in execution.tasks]
        assert task_ref in task_refs, f"Task {task_ref} not found in execution"

    @staticmethod
    def assert_task_status(execution, task_ref: str, expected_status: str):
        """Assert task has expected status"""
        task = next((t for t in execution.tasks if t.reference_task_name == task_ref), None)
        assert task, f"Task {task_ref} not found"
        assert task.status == expected_status, f"Expected {expected_status}, got {task.status}"

    @staticmethod
    def assert_workflow_path(execution, expected_path: List[str]):
        """Assert workflow followed expected path"""
        actual_path = [t.reference_task_name for t in execution.tasks if t.status == "COMPLETED"]
        assert actual_path == expected_path, f"Path mismatch: {actual_path} != {expected_path}"
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Workflow Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install conductor-python
        pip install pytest pytest-cov

    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=workers

    - name: Run integration tests
      env:
        CONDUCTOR_SERVER_URL: ${{ secrets.CONDUCTOR_URL }}
      run: |
        pytest tests/integration/ -v

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: test-workers
        name: Test Workers
        entry: python -m pytest tests/unit/test_workers.py
        language: system
        pass_filenames: false
        always_run: true
```

---

## Debugging Failed Tests

### Enable Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_with_logging():
    """Test with detailed logging"""
    logger.debug("Starting test")

    # Log mock data
    logger.debug(f"Mock outputs: {json.dumps(task_mocks, indent=2)}")

    # Execute test
    execution = workflow_client.test_workflow(test_request)

    # Log execution details
    logger.debug(f"Execution status: {execution.status}")
    logger.debug(f"Tasks executed: {len(execution.tasks)}")

    for task in execution.tasks:
        logger.debug(f"Task {task.reference_task_name}: {task.status}")
```

### Capture Test Artifacts

```python
def test_with_artifacts(self):
    """Save test artifacts for debugging"""
    try:
        execution = self.workflow_client.test_workflow(test_request)

        # Always save execution details
        with open(f"test_execution_{execution.workflow_id}.json", "w") as f:
            json.dump(execution.to_dict(), f, indent=2)

        self.assertEqual(execution.status, "COMPLETED")

    except AssertionError:
        # Save debug info on failure
        self._save_debug_info(execution)
        raise
```

---

## Complete Working Example

```python
"""
Complete Workflow Testing Example
==================================

Demonstrates comprehensive workflow testing including:
- Worker unit tests
- Workflow integration tests
- Retry simulation
- Decision logic testing
- Error scenario testing
"""

import unittest
import json
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.workflow_test_request import WorkflowTestRequest
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.task.simple_task import SimpleTask
from conductor.client.workflow.task.switch_task import SwitchTask

# Import workers to test
from my_workers import validate_order, process_payment, ship_order

class ComprehensiveWorkflowTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up test client"""
        config = Configuration(server_api_url="http://localhost:8080/api")
        cls.workflow_client = OrkesWorkflowClient(config)

    def test_worker_unit(self):
        """Unit test for individual worker"""
        # Test valid input
        result = validate_order(order_id="ORD-123", amount=99.99)
        self.assertTrue(result["valid"])

        # Test invalid input
        result = validate_order(order_id=None, amount=-1)
        self.assertFalse(result["valid"])

    def test_workflow_happy_path(self):
        """Test successful workflow execution"""

        # Create workflow
        wf = self._create_test_workflow()

        # Mock all tasks to succeed
        mocks = {
            "validate": [{"status": "COMPLETED", "output": {"valid": True}}],
            "payment": [{"status": "COMPLETED", "output": {"payment_id": "PAY-123"}}],
            "shipping": [{"status": "COMPLETED", "output": {"tracking": "TRACK-456"}}],
            "notify": [{"status": "COMPLETED", "output": {"sent": True}}]
        }

        # Execute test
        test_request = WorkflowTestRequest(
            workflow_def=wf.to_workflow_def(),
            input={"order_id": "TEST-123"},
            task_ref_to_mock_output=mocks
        )

        execution = self.workflow_client.test_workflow(test_request)

        # Assertions
        self.assertEqual(execution.status, "COMPLETED")
        self.assertEqual(len(execution.tasks), 4)
        self.assertIn("tracking", execution.output)

    def test_workflow_with_retry(self):
        """Test workflow with task retry"""

        wf = self._create_test_workflow()

        # Payment fails first, then succeeds
        mocks = {
            "validate": [{"status": "COMPLETED", "output": {"valid": True}}],
            "payment": [
                {"status": "FAILED", "reasonForIncompletion": "Gateway timeout"},
                {"status": "COMPLETED", "output": {"payment_id": "PAY-123"}}
            ],
            "shipping": [{"status": "COMPLETED", "output": {"tracking": "TRACK-456"}}],
            "notify": [{"status": "COMPLETED", "output": {"sent": True}}]
        }

        test_request = WorkflowTestRequest(
            workflow_def=wf.to_workflow_def(),
            input={"order_id": "TEST-123"},
            task_ref_to_mock_output=mocks
        )

        execution = self.workflow_client.test_workflow(test_request)

        # Verify retry occurred
        payment_tasks = [t for t in execution.tasks if t.reference_task_name == "payment"]
        self.assertEqual(len(payment_tasks), 2)
        self.assertEqual(payment_tasks[0].status, "FAILED")
        self.assertEqual(payment_tasks[1].status, "COMPLETED")

    def test_workflow_decision_branch(self):
        """Test workflow decision logic"""

        # Create workflow with decision
        wf = ConductorWorkflow(name="decision_test", version=1)
        check = SimpleTask("check_amount", "check_ref")
        high_value = SimpleTask("high_value_process", "high_ref")
        low_value = SimpleTask("low_value_process", "low_ref")

        decision = SwitchTask("amount_switch", check.output("amount_category"))
        decision.switch_case("HIGH", high_value)
        decision.default_case(low_value)

        wf >> check >> decision

        # Test HIGH branch
        mocks = {
            "check_ref": [{"status": "COMPLETED", "output": {"amount_category": "HIGH"}}],
            "high_ref": [{"status": "COMPLETED", "output": {"result": "processed as high value"}}]
        }

        test_request = WorkflowTestRequest(
            workflow_def=wf.to_workflow_def(),
            input={"amount": 1000},
            task_ref_to_mock_output=mocks
        )

        execution = self.workflow_client.test_workflow(test_request)

        # Verify correct branch executed
        task_refs = [t.reference_task_name for t in execution.tasks]
        self.assertIn("high_ref", task_refs)
        self.assertNotIn("low_ref", task_refs)

    def _create_test_workflow(self):
        """Helper to create test workflow"""
        wf = ConductorWorkflow(name="test_workflow", version=1)

        validate = SimpleTask("validate_order", "validate")
        payment = SimpleTask("process_payment", "payment")
        shipping = SimpleTask("ship_order", "shipping")
        notify = SimpleTask("send_notification", "notify")

        wf >> validate >> payment >> shipping >> notify

        return wf

if __name__ == "__main__":
    unittest.main()
```

---

## See Also

- [Worker Documentation](./WORKER.md) - Implementing workers to test
- [Workflow Management](./WORKFLOW.md) - Creating workflows
- [Task Management](./TASK_MANAGEMENT.md) - Task execution details
- [Examples](../examples/) - Complete working examples
- [test_workflows.py](../examples/test_workflows.py) - Testing patterns