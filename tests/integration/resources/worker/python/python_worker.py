from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.shared.http.enums.task_result_status import TaskResultStatus
from conductor.client.worker.worker_interface import WorkerInterface
from conductor.client.worker.worker_task import WorkerTask


class FaultyExecutionWorker(WorkerInterface):
    def execute(self, task: Task) -> TaskResult:
        raise Exception('faulty execution')


class ClassWorker(WorkerInterface):
    def __init__(self, task_definition_name):
        super().__init__(task_definition_name)
        self.poll_interval = 375.0

    def execute(self, task: Task) -> TaskResult:
        task_result = self.get_task_result_from_task(task)
        task_result.add_output_data('worker_style', 'class')
        task_result.add_output_data('secret_number', 1234)
        task_result.add_output_data('is_it_true', False)
        task_result.status = TaskResultStatus.COMPLETED
        return task_result


class ClassWorkerWithDomain(WorkerInterface):
    def __init__(self, task_definition_name):
        super().__init__(task_definition_name)
        self.poll_interval = 850.0
        self.domain = 'simple_python_worker'

    def execute(self, task: Task) -> TaskResult:
        task_result = self.get_task_result_from_task(task)
        task_result.add_output_data('worker_style', 'class')
        task_result.add_output_data('secret_number', 1234)
        task_result.add_output_data('is_it_true', False)
        task_result.status = TaskResultStatus.COMPLETED
        return task_result


@WorkerTask(task_definition_name='test_python_decorated_worker')
def decorated_worker(obj: object) -> object:
    return {
        'worker_style': 'function',
        'worker_input': 'Task',
        'worker_output': 'object',
        'task_input': obj,
        'status': 'COMPLETED'
    }


@WorkerTask(task_definition_name='test_python_decorated_worker', domain='cool', poll_interval=500.0)
def decorated_worker_with_domain_and_poll_interval(obj: object) -> object:
    return {
        'worker_style': 'function',
        'worker_input': 'Task',
        'worker_output': 'object',
        'domain': 'cool',
        'task_input': obj,
        'status': 'COMPLETED'
    }


def worker_with_task_input_and_task_result_output(task: Task) -> TaskResult:
    task_result = TaskResult(
        task_id=task.task_id,
        workflow_instance_id=task.workflow_instance_id,
        worker_id='your_custom_id'
    )
    task_result.add_output_data('worker_style', 'function')
    task_result.add_output_data('worker_input', 'Task')
    task_result.add_output_data('worker_output', 'TaskResult')
    task_result.status = TaskResultStatus.COMPLETED
    return task_result


def worker_with_task_input_and_generic_output(task: Task) -> object:
    return {
        'worker_style': 'function',
        'worker_input': 'Task',
        'worker_output': 'object',
        'task_id': task.task_id,
        'task_input': task.input_data,
    }


def worker_with_generic_input_and_task_result_output(obj: object) -> TaskResult:
    task_result = TaskResult(
        task_id='',
        workflow_instance_id='',
        worker_id=''
    )
    task_result.add_output_data('worker_style', 'function')
    task_result.add_output_data('worker_input', 'object')
    task_result.add_output_data('worker_output', 'TaskResult')
    task_result.status = TaskResultStatus.COMPLETED
    return task_result


def worker_with_generic_input_and_generic_output(obj: object) -> object:
    return {
        'worker_style': 'function',
        'worker_input': 'object',
        'worker_output': 'object',
        'input': obj,
    }
