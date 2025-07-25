from requests.structures import CaseInsensitiveDict

from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.worker_interface import WorkerInterface


class UserInfo:
    def __init__(self, name: str = "orkes", id: int = 0, address: str = None) -> None:
        self.name = name
        self.id = id
        self.address = address

    def __str__(self) -> str:
        return self.name + ":" + str(self.id)


class FaultyExecutionWorker(WorkerInterface):
    def execute(self, task: Task) -> TaskResult:
        raise Exception("faulty execution")


class SimplePythonWorker(WorkerInterface):
    def execute(self, task: Task) -> TaskResult:
        task_result = self.get_task_result_from_task(task)
        task_result.add_output_data("worker_style", "class")
        task_result.add_output_data("secret_number", 1234)
        task_result.add_output_data("is_it_true", False)
        task_result.add_output_data("dictionary_ojb", {"name": "sdk_worker", "idx": 465})
        task_result.add_output_data("case_insensitive_dictionary_ojb",
                                    CaseInsensitiveDict(data={"NaMe": "sdk_worker", "iDX": 465}))
        task_result.status = TaskResultStatus.COMPLETED
        return task_result

    def get_polling_interval_in_seconds(self) -> float:
        # poll every 500ms
        return 0.5

    def get_domain(self) -> str:
        return "simple_python_worker"


class ClassWorker(WorkerInterface):
    def __init__(self, task_definition_name: str):
        super().__init__(task_definition_name)
        self.poll_interval = 50.0

    def execute(self, task: Task) -> TaskResult:
        task_result = self.get_task_result_from_task(task)
        task_result.add_output_data("worker_style", "class")
        task_result.add_output_data("secret_number", 1234)
        task_result.add_output_data("is_it_true", False)
        task_result.add_output_data("dictionary_ojb", {"name": "sdk_worker", "idx": 465})
        task_result.add_output_data("case_insensitive_dictionary_ojb",
                                    CaseInsensitiveDict(data={"NaMe": "sdk_worker", "iDX": 465}))
        task_result.status = TaskResultStatus.COMPLETED
        return task_result
