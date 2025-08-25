from ctypes import cdll

from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.shared.http.enums import TaskResultStatus
from conductor.client.worker.worker_interface import WorkerInterface


class CppWrapper:
    def __init__(self, file_path='./lib.so'):
        self.cpp_lib = cdll.LoadLibrary(file_path)

    def get_sum(self, X: int, Y: int) -> int:
        return self.cpp_lib.get_sum(X, Y)


class SimpleCppWorker(WorkerInterface):
    cpp_wrapper = CppWrapper()

    def execute(self, task: Task) -> TaskResult:
        execution_result = self.cpp_wrapper.get_sum(1, 2)
        task_result = self.get_task_result_from_task(task)
        task_result.add_output_data(
            'sum', execution_result
        )
        task_result.status = TaskResultStatus.COMPLETED
        return task_result
