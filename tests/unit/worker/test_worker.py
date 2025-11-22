import dataclasses
import unittest
from typing import Optional

from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.worker import Worker
from conductor.client.worker.base_worker import BaseWorker
from conductor.client.worker.exception import NonRetryableException


@dataclasses.dataclass
class UserInfo:
    name: str
    age: int
    email: Optional[str] = None


class TestWorkerInitialization(unittest.TestCase):
    def test_worker_init_minimal_params(self):
        def simple_func(task: Task) -> dict:
            return {"result": "ok"}

        worker = Worker("test_task", simple_func)
        self.assertEqual(worker.task_definition_name, "test_task")
        self.assertEqual(worker.poll_interval, 100)
        self.assertIsNone(worker.domain)
        self.assertIsNotNone(worker.worker_id)

    def test_worker_init_with_all_params(self):
        def simple_func(task: Task) -> dict:
            return {"result": "ok"}

        worker = Worker(
            task_definition_name="test_task",
            execute_function=simple_func,
            poll_interval=2.5,
            domain="staging",
            worker_id="worker-456",
        )
        self.assertEqual(worker.task_definition_name, "test_task")
        self.assertEqual(worker.poll_interval, 2.5)
        self.assertEqual(worker.domain, "staging")
        self.assertEqual(worker.worker_id, "worker-456")


class TestWorkerExecute(unittest.TestCase):
    def test_execute_with_task_parameter_returns_dict(self):
        def task_func(task: Task) -> dict:
            return {"result": "success", "value": 42}

        worker = Worker("test_task", task_func)
        task = Task(task_id="task-123", workflow_instance_id="workflow-456", task_def_name="test_task", input_data={})
        result = worker.execute(task)
        self.assertIsInstance(result, TaskResult)
        self.assertEqual(result.task_id, "task-123")
        self.assertEqual(result.workflow_instance_id, "workflow-456")
        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data, {"result": "success", "value": 42})

    def test_execute_with_simple_parameters(self):
        def task_func(name: str, age: int) -> dict:
            return {"greeting": f"Hello {name}, you are {age} years old"}

        worker = Worker("test_task", task_func)
        task = Task(task_id="task-123", workflow_instance_id="workflow-456", task_def_name="test_task",
                    input_data={"name": "Alice", "age": 30})
        result = worker.execute(task)
        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertEqual(result.output_data, {"greeting": "Hello Alice, you are 30 years old"})

    def test_execute_with_dataclass_parameter(self):
        def task_func(user: UserInfo) -> dict:
            return {"message": f"User {user.name} is {user.age} years old"}

        worker = Worker("test_task", task_func)
        task = Task(task_id="task-123", workflow_instance_id="workflow-456", task_def_name="test_task",
                    input_data={"user": {"name": "Bob", "age": 25, "email": "bob@example.com"}})
        result = worker.execute(task)
        self.assertEqual(result.status, TaskResultStatus.COMPLETED)
        self.assertIn("Bob", result.output_data["message"])

    def test_execute_with_non_retryable_exception(self):
        def task_func(task: Task) -> dict:
            raise NonRetryableException("This error should not be retried")

        worker = Worker("test_task", task_func)
        task = Task(task_id="task-123", workflow_instance_id="workflow-456", task_def_name="test_task", input_data={})
        result = worker.execute(task)
        self.assertEqual(result.status, TaskResultStatus.FAILED_WITH_TERMINAL_ERROR)
        self.assertEqual(result.reason_for_incompletion, "This error should not be retried")

    def test_execute_with_generic_exception(self):
        def task_func(task: Task) -> dict:
            raise ValueError("Something went wrong")

        worker = Worker("test_task", task_func)
        task = Task(task_id="task-123", workflow_instance_id="workflow-456", task_def_name="test_task", input_data={})
        result = worker.execute(task)
        self.assertEqual(result.status, TaskResultStatus.FAILED)
        self.assertEqual(result.reason_for_incompletion, "Something went wrong")
        self.assertEqual(len(result.logs), 1)
        self.assertIn("Traceback", result.logs[0].log)

    def test_execute_with_coroutine(self):
        async def async_task_func(task: Task) -> dict:
            return {"result": "async_success"}

        worker = Worker("test_task", async_task_func)
        task = Task(task_id="task-123", workflow_instance_id="workflow-456", task_def_name="test_task", input_data={})
        with self.assertRaisesRegex(Exception, 'Coroutines are not supported in SyncWorker, please use AsyncWorker'):
            worker.execute(task)


class TestBaseWorker(unittest.TestCase):
    def test_base_worker_creation(self):
        def simple_func(task: Task) -> dict:
            return {"result": "ok"}

        class ConcreteWorker(BaseWorker):
            def execute(self, task: Task) -> TaskResult:
                return super().execute(task)

        worker = ConcreteWorker("test_task", simple_func)
        self.assertEqual(worker.task_definition_name, "test_task")
        self.assertEqual(worker.poll_interval, 100)
        self.assertIsNone(worker.domain)
        self.assertIsNotNone(worker.worker_id)


if __name__ == '__main__':
    unittest.main()
