import asyncio
from requests.structures import CaseInsensitiveDict

from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.worker_interface import WorkerInterface


class UserInfo:
    def __init__(self, name: str = 'orkes', id: int = 0, address: str = None) -> None:
        self.name = name
        self.id = id
        self.address = address

    def __str__(self) -> str:
        return self.name + ':' + str(self.id)


class FaultyExecutionWorker(WorkerInterface):
    def execute(self, task: Task) -> TaskResult:
        raise Exception('faulty execution')


class SimplePythonWorker(WorkerInterface):
    def execute(self, task: Task) -> TaskResult:
        task_result = self.get_task_result_from_task(task)
        task_result.add_output_data('worker_style', 'class')
        task_result.add_output_data('secret_number', 1234)
        task_result.add_output_data('is_it_true', False)
        task_result.add_output_data('dictionary_ojb', {'name': 'sdk_worker', 'idx': 465})
        task_result.add_output_data('case_insensitive_dictionary_ojb',
                                    CaseInsensitiveDict(data={'NaMe': 'sdk_worker', 'iDX': 465}))
        task_result.status = TaskResultStatus.COMPLETED
        return task_result

    def get_polling_interval_in_seconds(self) -> float:
        # poll every 500ms
        return 0.5

    def get_domain(self) -> str:
        return 'simple_python_worker'


class ClassWorker(WorkerInterface):
    def __init__(self, task_definition_name: str):
        super().__init__(task_definition_name)
        self.poll_interval = 50.0

    def execute(self, task: Task) -> TaskResult:
        task_result = self.get_task_result_from_task(task)
        task_result.add_output_data('worker_style', 'class')
        task_result.add_output_data('secret_number', 1234)
        task_result.add_output_data('is_it_true', False)
        task_result.add_output_data('dictionary_ojb', {'name': 'sdk_worker', 'idx': 465})
        task_result.add_output_data('case_insensitive_dictionary_ojb',
                                    CaseInsensitiveDict(data={'NaMe': 'sdk_worker', 'iDX': 465}))
        task_result.status = TaskResultStatus.COMPLETED
        return task_result


# AsyncIO test workers

class AsyncWorker(WorkerInterface):
    """Async worker for testing asyncio task runner"""
    def __init__(self, task_definition_name: str):
        super().__init__(task_definition_name)
        self.poll_interval = 0.01  # Fast polling for tests

    async def execute(self, task: Task) -> TaskResult:
        """Async execute method"""
        # Simulate async work
        await asyncio.sleep(0.01)

        task_result = self.get_task_result_from_task(task)
        task_result.add_output_data('worker_style', 'async')
        task_result.add_output_data('secret_number', 5678)
        task_result.add_output_data('is_it_true', True)
        task_result.status = TaskResultStatus.COMPLETED
        return task_result


class AsyncFaultyExecutionWorker(WorkerInterface):
    """Async worker that raises exceptions for testing error handling"""
    async def execute(self, task: Task) -> TaskResult:
        await asyncio.sleep(0.01)
        raise Exception('async faulty execution')


class AsyncTimeoutWorker(WorkerInterface):
    """Async worker that hangs forever for testing timeout"""
    def __init__(self, task_definition_name: str, sleep_time: float = 999.0):
        super().__init__(task_definition_name)
        self.sleep_time = sleep_time

    async def execute(self, task: Task) -> TaskResult:
        # This will hang and should be killed by timeout
        await asyncio.sleep(self.sleep_time)
        task_result = self.get_task_result_from_task(task)
        task_result.status = TaskResultStatus.COMPLETED
        return task_result


class SyncWorkerForAsync(WorkerInterface):
    """Sync worker to test sync execution in asyncio runner (thread pool)"""
    def __init__(self, task_definition_name: str):
        super().__init__(task_definition_name)
        self.poll_interval = 0.01  # Fast polling for tests

    def execute(self, task: Task) -> TaskResult:
        """Sync execute method - should run in thread pool"""
        import time
        time.sleep(0.01)  # Simulate sync work

        task_result = self.get_task_result_from_task(task)
        task_result.add_output_data('worker_style', 'sync_in_async')
        task_result.add_output_data('ran_in_thread', True)
        task_result.status = TaskResultStatus.COMPLETED
        return task_result
