import pprint
import re  # noqa: F401
import six
from typing import Dict, Any, Optional, List
from enum import Enum


class WorkflowSignalReturnStrategy(Enum):
    """Enum for workflow signal return strategy"""
    TARGET_WORKFLOW = "TARGET_WORKFLOW"
    BLOCKING_WORKFLOW = "BLOCKING_WORKFLOW"
    BLOCKING_TASK = "BLOCKING_TASK"
    BLOCKING_TASK_INPUT = "BLOCKING_TASK_INPUT"


class TaskStatus(Enum):
    """Enum for task status"""
    IN_PROGRESS = "IN_PROGRESS"
    CANCELED = "CANCELED"
    FAILED = "FAILED"
    FAILED_WITH_TERMINAL_ERROR = "FAILED_WITH_TERMINAL_ERROR"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    SCHEDULED = "SCHEDULED"
    TIMED_OUT = "TIMED_OUT"
    READY_FOR_RERUN = "READY_FOR_RERUN"
    SKIPPED = "SKIPPED"


class SignalResponse:
    swagger_types = {
        'response_type': 'str',
        'target_workflow_id': 'str',
        'target_workflow_status': 'str',
        'request_id': 'str',
        'workflow_id': 'str',
        'correlation_id': 'str',
        'input': 'dict(str, object)',
        'output': 'dict(str, object)',
        'task_type': 'str',
        'task_id': 'str',
        'reference_task_name': 'str',
        'retry_count': 'int',
        'task_def_name': 'str',
        'retried_task_id': 'str',
        'workflow_type': 'str',
        'reason_for_incompletion': 'str',
        'priority': 'int',
        'variables': 'dict(str, object)',
        'tasks': 'list[object]',
        'created_by': 'str',
        'create_time': 'int',
        'update_time': 'int',
        'status': 'str'
    }

    attribute_map = {
        'response_type': 'responseType',
        'target_workflow_id': 'targetWorkflowId',
        'target_workflow_status': 'targetWorkflowStatus',
        'request_id': 'requestId',
        'workflow_id': 'workflowId',
        'correlation_id': 'correlationId',
        'input': 'input',
        'output': 'output',
        'task_type': 'taskType',
        'task_id': 'taskId',
        'reference_task_name': 'referenceTaskName',
        'retry_count': 'retryCount',
        'task_def_name': 'taskDefName',
        'retried_task_id': 'retriedTaskId',
        'workflow_type': 'workflowType',
        'reason_for_incompletion': 'reasonForIncompletion',
        'priority': 'priority',
        'variables': 'variables',
        'tasks': 'tasks',
        'created_by': 'createdBy',
        'create_time': 'createTime',
        'update_time': 'updateTime',
        'status': 'status'
    }

    def __init__(self, **kwargs):
        """Initialize with API response data, handling both camelCase and snake_case"""

        # Initialize all attributes with default values
        self.response_type = None
        self.target_workflow_id = None
        self.target_workflow_status = None
        self.request_id = None
        self.workflow_id = None
        self.correlation_id = None
        self.input = {}
        self.output = {}
        self.task_type = None
        self.task_id = None
        self.reference_task_name = None
        self.retry_count = 0
        self.task_def_name = None
        self.retried_task_id = None
        self.workflow_type = None
        self.reason_for_incompletion = None
        self.priority = 0
        self.variables = {}
        self.tasks = []
        self.created_by = None
        self.create_time = 0
        self.update_time = 0
        self.status = None
        self.discriminator = None

        # Handle both camelCase (from API) and snake_case keys
        reverse_mapping = {v: k for k, v in self.attribute_map.items()}

        for key, value in kwargs.items():
            if key in reverse_mapping:
                # Convert camelCase to snake_case
                snake_key = reverse_mapping[key]
                if snake_key == 'status' and isinstance(value, str):
                    try:
                        setattr(self, snake_key, TaskStatus(value))
                    except ValueError:
                        setattr(self, snake_key, value)
                else:
                    setattr(self, snake_key, value)
            elif hasattr(self, key):
                # Direct snake_case assignment
                if key == 'status' and isinstance(value, str):
                    try:
                        setattr(self, key, TaskStatus(value))
                    except ValueError:
                        setattr(self, key, value)
                else:
                    setattr(self, key, value)

        # Extract task information from the first IN_PROGRESS task if available
        if self.response_type == "TARGET_WORKFLOW" and self.tasks:
            in_progress_task = None
            for task in self.tasks:
                if isinstance(task, dict) and task.get('status') == 'IN_PROGRESS':
                    in_progress_task = task
                    break

            # If no IN_PROGRESS task, get the last task
            if not in_progress_task and self.tasks:
                in_progress_task = self.tasks[-1] if isinstance(self.tasks[-1], dict) else None

            if in_progress_task:
                # Map task fields if they weren't already set
                if self.task_id is None:
                    self.task_id = in_progress_task.get('taskId')
                if self.task_type is None:
                    self.task_type = in_progress_task.get('taskType')
                if self.reference_task_name is None:
                    self.reference_task_name = in_progress_task.get('referenceTaskName')
                if self.task_def_name is None:
                    self.task_def_name = in_progress_task.get('taskDefName')
                if self.retry_count == 0:
                    self.retry_count = in_progress_task.get('retryCount', 0)

    def __str__(self):
        """Returns a detailed string representation similar to Swagger response"""

        def format_dict(d, indent=12):
            if not d:
                return "{}"
            items = []
            for k, v in d.items():
                if isinstance(v, dict):
                    formatted_v = format_dict(v, indent + 4)
                    items.append(f"{' ' * indent}'{k}': {formatted_v}")
                elif isinstance(v, list):
                    formatted_v = format_list(v, indent + 4)
                    items.append(f"{' ' * indent}'{k}': {formatted_v}")
                elif isinstance(v, str):
                    items.append(f"{' ' * indent}'{k}': '{v}'")
                else:
                    items.append(f"{' ' * indent}'{k}': {v}")
            return "{\n" + ",\n".join(items) + f"\n{' ' * (indent - 4)}}}"

        def format_list(lst, indent=12):
            if not lst:
                return "[]"
            items = []
            for item in lst:
                if isinstance(item, dict):
                    formatted_item = format_dict(item, indent + 4)
                    items.append(f"{' ' * indent}{formatted_item}")
                elif isinstance(item, str):
                    items.append(f"{' ' * indent}'{item}'")
                else:
                    items.append(f"{' ' * indent}{item}")
            return "[\n" + ",\n".join(items) + f"\n{' ' * (indent - 4)}]"

        # Format input and output
        input_str = format_dict(self.input) if self.input else "{}"
        output_str = format_dict(self.output) if self.output else "{}"
        variables_str = format_dict(self.variables) if self.variables else "{}"

        # Handle different response types
        if self.response_type == "TARGET_WORKFLOW":
            # Workflow response - show tasks array
            tasks_str = format_list(self.tasks, 12) if self.tasks else "[]"
            return f"""SignalResponse(
    responseType='{self.response_type}',
    targetWorkflowId='{self.target_workflow_id}',
    targetWorkflowStatus='{self.target_workflow_status}',
    workflowId='{self.workflow_id}',
    input={input_str},
    output={output_str},
    priority={self.priority},
    variables={variables_str},
    tasks={tasks_str},
    createdBy='{self.created_by}',
    createTime={self.create_time},
    updateTime={self.update_time},
    status='{self.status}'
)"""

        elif self.response_type == "BLOCKING_TASK":
            # Task response - show task-specific fields
            status_str = self.status.value if hasattr(self.status, 'value') else str(self.status)
            return f"""SignalResponse(
    responseType='{self.response_type}',
    targetWorkflowId='{self.target_workflow_id}',
    targetWorkflowStatus='{self.target_workflow_status}',
    workflowId='{self.workflow_id}',
    input={input_str},
    output={output_str},
    taskType='{self.task_type}',
    taskId='{self.task_id}',
    referenceTaskName='{self.reference_task_name}',
    retryCount={self.retry_count},
    taskDefName='{self.task_def_name}',
    workflowType='{self.workflow_type}',
    priority={self.priority},
    createTime={self.create_time},
    updateTime={self.update_time},
    status='{status_str}'
)"""

        else:
            # Generic response - show all available fields
            status_str = self.status.value if hasattr(self.status, 'value') else str(self.status)
            result = f"""SignalResponse(
    responseType='{self.response_type}',
    targetWorkflowId='{self.target_workflow_id}',
    targetWorkflowStatus='{self.target_workflow_status}',
    workflowId='{self.workflow_id}',
    input={input_str},
    output={output_str},
    priority={self.priority}"""

            # Add task fields if they exist
            if self.task_type:
                result += f",\n    taskType='{self.task_type}'"
            if self.task_id:
                result += f",\n    taskId='{self.task_id}'"
            if self.reference_task_name:
                result += f",\n    referenceTaskName='{self.reference_task_name}'"
            if self.retry_count > 0:
                result += f",\n    retryCount={self.retry_count}"
            if self.task_def_name:
                result += f",\n    taskDefName='{self.task_def_name}'"
            if self.workflow_type:
                result += f",\n    workflowType='{self.workflow_type}'"

            # Add workflow fields if they exist
            if self.variables:
                result += f",\n    variables={variables_str}"
            if self.tasks:
                tasks_str = format_list(self.tasks, 12)
                result += f",\n    tasks={tasks_str}"
            if self.created_by:
                result += f",\n    createdBy='{self.created_by}'"

            result += f",\n    createTime={self.create_time}"
            result += f",\n    updateTime={self.update_time}"
            result += f",\n    status='{status_str}'"
            result += "\n)"

            return result

    def get_task_by_reference_name(self, ref_name: str) -> Optional[Dict]:
        """Get a specific task by its reference name"""
        if not self.tasks:
            return None

        for task in self.tasks:
            if isinstance(task, dict) and task.get('referenceTaskName') == ref_name:
                return task
        return None

    def get_tasks_by_status(self, status: str) -> List[Dict]:
        """Get all tasks with a specific status"""
        if not self.tasks:
            return []

        return [task for task in self.tasks
                if isinstance(task, dict) and task.get('status') == status]

    def get_in_progress_task(self) -> Optional[Dict]:
        """Get the current IN_PROGRESS task"""
        in_progress_tasks = self.get_tasks_by_status('IN_PROGRESS')
        return in_progress_tasks[0] if in_progress_tasks else None

    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks in the workflow"""
        return self.tasks if self.tasks else []

    def get_completed_tasks(self) -> List[Dict]:
        """Get all completed tasks"""
        return self.get_tasks_by_status('COMPLETED')

    def get_failed_tasks(self) -> List[Dict]:
        """Get all failed tasks"""
        return self.get_tasks_by_status('FAILED')

    def get_task_chain(self) -> List[str]:
        """Get the sequence of task reference names in execution order"""
        if not self.tasks:
            return []

        # Sort by seq number if available, otherwise by the order in the list
        sorted_tasks = sorted(self.tasks, key=lambda t: t.get('seq', 0) if isinstance(t, dict) else 0)
        return [task.get('referenceTaskName', f'task_{i}')
                for i, task in enumerate(sorted_tasks) if isinstance(task, dict)]

    # ===== HELPER METHODS (Following Go SDK Pattern) =====

    def is_target_workflow(self) -> bool:
        """Returns True if the response contains target workflow details"""
        return self.response_type == "TARGET_WORKFLOW"

    def is_blocking_workflow(self) -> bool:
        """Returns True if the response contains blocking workflow details"""
        return self.response_type == "BLOCKING_WORKFLOW"

    def is_blocking_task(self) -> bool:
        """Returns True if the response contains blocking task details"""
        return self.response_type == "BLOCKING_TASK"

    def is_blocking_task_input(self) -> bool:
        """Returns True if the response contains blocking task input"""
        return self.response_type == "BLOCKING_TASK_INPUT"

    def get_workflow(self) -> Optional[Dict]:
        """
        Extract workflow details from a SignalResponse.
        Returns None if the response type doesn't contain workflow details.
        """
        if not (self.is_target_workflow() or self.is_blocking_workflow()):
            return None

        return {
            'workflowId': self.workflow_id,
            'status': self.status.value if hasattr(self.status, 'value') else str(self.status),
            'tasks': self.tasks or [],
            'createdBy': self.created_by,
            'createTime': self.create_time,
            'updateTime': self.update_time,
            'input': self.input or {},
            'output': self.output or {},
            'variables': self.variables or {},
            'priority': self.priority,
            'targetWorkflowId': self.target_workflow_id,
            'targetWorkflowStatus': self.target_workflow_status
        }

    def get_blocking_task(self) -> Optional[Dict]:
        """
        Extract task details from a SignalResponse.
        Returns None if the response type doesn't contain task details.
        """
        if not (self.is_blocking_task() or self.is_blocking_task_input()):
            return None

        return {
            'taskId': self.task_id,
            'taskType': self.task_type,
            'taskDefName': self.task_def_name,
            'workflowType': self.workflow_type,
            'referenceTaskName': self.reference_task_name,
            'retryCount': self.retry_count,
            'status': self.status.value if hasattr(self.status, 'value') else str(self.status),
            'workflowId': self.workflow_id,
            'input': self.input or {},
            'output': self.output or {},
            'priority': self.priority,
            'createTime': self.create_time,
            'updateTime': self.update_time
        }

    def get_task_input(self) -> Optional[Dict]:
        """
        Extract task input from a SignalResponse.
        Only valid for BLOCKING_TASK_INPUT responses.
        """
        if not self.is_blocking_task_input():
            return None

        return self.input or {}

    def print_summary(self):
        """Print a concise summary for quick overview"""
        status_str = self.status.value if hasattr(self.status, 'value') else str(self.status)

        print(f"""
=== Signal Response Summary ===
Response Type: {self.response_type}
Workflow ID: {self.workflow_id}
Workflow Status: {self.target_workflow_status}
""")

        if self.is_target_workflow() or self.is_blocking_workflow():
            print(f"Total Tasks: {len(self.tasks) if self.tasks else 0}")
            print(f"Workflow Status: {status_str}")
            if self.created_by:
                print(f"Created By: {self.created_by}")

        if self.is_blocking_task() or self.is_blocking_task_input():
            print(f"Task Info:")
            print(f"  Task ID: {self.task_id}")
            print(f"  Task Type: {self.task_type}")
            print(f"  Reference Name: {self.reference_task_name}")
            print(f"  Status: {status_str}")
            print(f"  Retry Count: {self.retry_count}")
            if self.workflow_type:
                print(f"  Workflow Type: {self.workflow_type}")

    def get_response_summary(self) -> str:
        """Get a quick text summary of the response type and key info"""
        status_str = self.status.value if hasattr(self.status, 'value') else str(self.status)

        if self.is_target_workflow():
            return f"TARGET_WORKFLOW: {self.workflow_id} ({self.target_workflow_status}) - {len(self.tasks) if self.tasks else 0} tasks"
        elif self.is_blocking_workflow():
            return f"BLOCKING_WORKFLOW: {self.workflow_id} ({status_str}) - {len(self.tasks) if self.tasks else 0} tasks"
        elif self.is_blocking_task():
            return f"BLOCKING_TASK: {self.task_type} ({self.reference_task_name}) - {status_str}"
        elif self.is_blocking_task_input():
            return f"BLOCKING_TASK_INPUT: {self.task_type} ({self.reference_task_name}) - Input data available"
        else:
            return f"UNKNOWN_RESPONSE_TYPE: {self.response_type}"

    def print_tasks_summary(self):
        """Print a detailed summary of all tasks"""
        if not self.tasks:
            print("No tasks found in the response.")
            return

        print(f"\n=== Tasks Summary ({len(self.tasks)} tasks) ===")
        for i, task in enumerate(self.tasks, 1):
            if isinstance(task, dict):
                print(f"\nTask {i}:")
                print(f"  Type: {task.get('taskType', 'UNKNOWN')}")
                print(f"  Reference Name: {task.get('referenceTaskName', 'UNKNOWN')}")
                print(f"  Status: {task.get('status', 'UNKNOWN')}")
                print(f"  Task ID: {task.get('taskId', 'UNKNOWN')}")
                print(f"  Sequence: {task.get('seq', 'N/A')}")
                if task.get('startTime'):
                    print(f"  Start Time: {task.get('startTime')}")
                if task.get('endTime'):
                    print(f"  End Time: {task.get('endTime')}")
                if task.get('inputData'):
                    print(f"  Input Data: {task.get('inputData')}")
                if task.get('outputData'):
                    print(f"  Output Data: {task.get('outputData')}")
                if task.get('workerId'):
                    print(f"  Worker ID: {task.get('workerId')}")

    def get_full_json(self) -> str:
        """Get the complete response as JSON string (like Swagger)"""
        import json
        return json.dumps(self.to_dict(), indent=2)

    def save_to_file(self, filename: str):
        """Save the complete response to a JSON file"""
        import json
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"Response saved to {filename}")

    def to_dict(self):
        """Returns the model properties as a dict with camelCase keys"""
        result = {}

        for snake_key, value in self.__dict__.items():
            if value is None or snake_key == 'discriminator':
                continue

            # Convert to camelCase using attribute_map
            camel_key = self.attribute_map.get(snake_key, snake_key)

            if isinstance(value, TaskStatus):
                result[camel_key] = value.value
            elif snake_key == 'tasks' and not value:
                # For BLOCKING_TASK responses, don't include empty tasks array
                if self.response_type != "BLOCKING_TASK":
                    result[camel_key] = value
            elif snake_key in ['task_type', 'task_id', 'reference_task_name', 'task_def_name',
                               'workflow_type'] and not value:
                # For TARGET_WORKFLOW responses, don't include empty task fields
                if self.response_type == "BLOCKING_TASK":
                    continue
                else:
                    result[camel_key] = value
            elif snake_key in ['variables', 'created_by'] and not value:
                # Don't include empty variables or None created_by
                continue
            else:
                result[camel_key] = value

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SignalResponse':
        """Create instance from dictionary with camelCase keys"""
        snake_case_data = {}

        # Reverse mapping from camelCase to snake_case
        reverse_mapping = {v: k for k, v in cls.attribute_map.items()}

        for camel_key, value in data.items():
            if camel_key in reverse_mapping:
                snake_key = reverse_mapping[camel_key]
                if snake_key == 'status' and value:
                    snake_case_data[snake_key] = TaskStatus(value)
                else:
                    snake_case_data[snake_key] = value

        return cls(**snake_case_data)

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'SignalResponse':
        """Create instance from API response dictionary with proper field mapping"""
        if not isinstance(data, dict):
            return cls()

        kwargs = {}

        # Reverse mapping from camelCase to snake_case
        reverse_mapping = {v: k for k, v in cls.attribute_map.items()}

        for camel_key, value in data.items():
            if camel_key in reverse_mapping:
                snake_key = reverse_mapping[camel_key]
                if snake_key == 'status' and value and isinstance(value, str):
                    try:
                        kwargs[snake_key] = TaskStatus(value)
                    except ValueError:
                        kwargs[snake_key] = value
                else:
                    kwargs[snake_key] = value

        return cls(**kwargs)

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, SignalResponse):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other