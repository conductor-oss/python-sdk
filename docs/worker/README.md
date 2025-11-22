# Worker

Considering real use cases, the goal is to run multiple workers in parallel. Due to some limitations with Python, a multiprocessing architecture was chosen in order to enable real parallelization.

You can write your workers independently and append them to a list. The `TaskHandler` class will spawn a unique and independent process for each worker, making sure it will behave as expected, by running an infinite loop like this:
* Poll for a `Task` at Conductor Server
* Generate `TaskResult` from given `Task`
* Update given `Task` with `TaskResult` at Conductor Server

## Write workers

Currently, there are three ways of writing a Python worker:
1. [Worker as a function](#worker-as-a-function)
2. [Worker as a class](#worker-as-a-class)
3. [Worker as an annotation](#worker-as-an-annotation)
4. [Async workers](#async-workers) - Workers using async/await for I/O-bound operations


### Worker as a function

The function should follow this signature:

```python
ExecuteTaskFunction = Callable[
    [
        Union[Task, object]
    ],
    Union[TaskResult, object]
]
```

In other words:
* Input must be either a `Task` or an `object`
    * If it isn't a `Task`, the assumption is - you're expecting to receive the `Task.input_data` as the object
* Output must be either a `TaskResult` or an `object`
    * If it isn't a `TaskResult`, the assumption is - you're expecting to use the object as the `TaskResult.output_data`

Quick example below:

```python
from conductor.client.http.models import Task, TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus

def execute(task: Task) -> TaskResult:
    task_result = TaskResult(
        task_id=task.task_id,
        workflow_instance_id=task.workflow_instance_id,
        worker_id='your_custom_id'
    )
    task_result.add_output_data('worker_style', 'function')
    task_result.status = TaskResultStatus.COMPLETED
    return task_result
```

In the case you like more details, you can take a look at all possible combinations of workers [here](../../tests/integration/resources/worker/python/python_worker.py)

### Worker as a class

The class must implement `WorkerInterface` class, which requires an `execute` method. The remaining ones are inherited, but can be easily overridden. Example with a custom polling interval:

```python
from conductor.client.http.models import Task, TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.worker_interface import WorkerInterface

class SimplePythonWorker(WorkerInterface):
    def execute(self, task: Task) -> TaskResult:
        task_result = self.get_task_result_from_task(task)
        task_result.add_output_data('worker_style', 'class')
        task_result.add_output_data('secret_number', 1234)
        task_result.add_output_data('is_it_true', False)
        task_result.status = TaskResultStatus.COMPLETED
        return task_result

    def get_polling_interval_in_seconds(self) -> float:
        # poll every 500ms
        return 0.5
```

### Worker as an annotation
A worker can also be invoked by adding a WorkerTask decorator as shown in the below example.
As long as the annotated worker is in any file inside the root folder of your worker application, it will be picked up by the TaskHandler, see [Run Workers](#run-workers)

The arguments that can be passed when defining the decorated worker are:
1. task_definition_name: The task definition name of the condcutor task that needs to be polled for.
2. domain: Optional routing domain of the worker to execute tasks with a specific domain
3. worker_id: An optional worker id used to identify the polling worker
4. poll_interval: Polling interval in seconds. Defaulted to 1 second if not passed.

```python
from conductor.client.worker.worker_task import WorkerTask

@WorkerTask(task_definition_name='python_annotated_task', worker_id='decorated', poll_interval=200.0)
def python_annotated_task(input) -> object:
    return {'message': 'python is so cool :)'}
```

### Async Workers

For I/O-bound operations (like HTTP requests, database queries, or file operations), you can write async workers using Python's `async`/`await` syntax. Async workers are executed efficiently using a persistent background event loop, avoiding the overhead of creating a new event loop for each task.

#### Async Worker as a Function

```python
import asyncio
import httpx
from conductor.client.http.models import Task, TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus

async def async_http_worker(task: Task) -> TaskResult:
    """Async worker that makes HTTP requests."""
    task_result = TaskResult(
        task_id=task.task_id,
        workflow_instance_id=task.workflow_instance_id,
    )

    url = task.input_data.get('url', 'https://api.example.com/data')

    # Use async HTTP client for non-blocking I/O
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        task_result.add_output_data('status_code', response.status_code)
        task_result.add_output_data('data', response.json())

    task_result.status = TaskResultStatus.COMPLETED
    return task_result
```

#### Async Worker as an Annotation

```python
import asyncio
from conductor.client.worker.worker_task import WorkerTask

@WorkerTask(task_definition_name='async_task', poll_interval=1.0)
async def async_worker(url: str, timeout: int = 30) -> dict:
    """Simple async worker with automatic input/output mapping."""
    await asyncio.sleep(0.1)  # Simulate async I/O

    # Your async logic here
    result = await fetch_data_async(url, timeout)

    return {
        'result': result,
        'processed_at': datetime.now().isoformat()
    }
```

#### Performance Benefits

Async workers use a **persistent background event loop** that provides significant performance improvements over traditional synchronous workers:

- **1.5-2x faster** for I/O-bound tasks compared to blocking operations
- **No event loop overhead** - single loop shared across all async workers
- **Better resource utilization** - workers don't block while waiting for I/O
- **Scalability** - handle more concurrent operations with fewer threads

**Note (v1.2.5+)**: With the ultra-low latency polling optimizations, both sync and async workers now benefit from:
- **2-5ms average polling delay** (down from 15-90ms)
- **Batch polling** (60-70% fewer API calls)
- **Adaptive backoff** (prevents API hammering when queue is empty)
- **Concurrent execution** (via ThreadPoolExecutor, controlled by `thread_count` parameter)

#### Best Practices for Async Workers

1. **Use for I/O-bound tasks**: Database queries, HTTP requests, file I/O
2. **Don't use for CPU-bound tasks**: Use regular sync workers for heavy computation
3. **Use async libraries**: `httpx`, `aiohttp`, `asyncpg`, etc.
4. **Keep timeouts reasonable**: Default timeout is 300 seconds (5 minutes)
5. **Handle exceptions**: Async exceptions are properly propagated to task results

#### Example: Async Database Worker

```python
import asyncpg
from conductor.client.worker.worker_task import WorkerTask

@WorkerTask(task_definition_name='async_db_query')
async def query_database(user_id: int) -> dict:
    """Async worker that queries PostgreSQL database."""
    # Create async database connection pool
    pool = await asyncpg.create_pool(
        host='localhost',
        database='mydb',
        user='user',
        password='password'
    )

    try:
        async with pool.acquire() as conn:
            # Execute async query
            result = await conn.fetch(
                'SELECT * FROM users WHERE id = $1',
                user_id
            )
            return {'user': dict(result[0]) if result else None}
    finally:
        await pool.close()
```

#### Mixed Sync and Async Workers

You can mix sync and async workers in the same application. The SDK automatically detects async functions and handles them appropriately:

```python
from conductor.client.worker.worker import Worker

workers = [
    # Sync worker
    Worker(
        task_definition_name='sync_task',
        execute_function=sync_worker_function
    ),
    # Async worker
    Worker(
        task_definition_name='async_task',
        execute_function=async_worker_function
    ),
]
```

## Run Workers

Now you can run your workers by calling a `TaskHandler`, example:

```python
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.configuration.configuration import Configuration
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.worker.worker import Worker

#### Add these lines if running on a mac####
from multiprocessing import set_start_method
set_start_method('fork')
############################################

SERVER_API_URL = 'http://localhost:8080/api'
KEY_ID = '<KEY_ID>'
KEY_SECRET = '<KEY_SECRET>'

configuration = Configuration(
    server_api_url=SERVER_API_URL,
    debug=True,
    authentication_settings=AuthenticationSettings(
        key_id=KEY_ID,
        key_secret=KEY_SECRET
    ),
)

workers = [
    SimplePythonWorker(
        task_definition_name='python_task_example'
    ),
    Worker(
        task_definition_name='python_execute_function_task',
        execute_function=execute,
        poll_interval=250,
        domain='test'
    )
]

# If there are decorated workers in your application, scan_for_annotated_workers should be set
# default value of scan_for_annotated_workers is False
with TaskHandler(workers, configuration, scan_for_annotated_workers=True) as task_handler:
    task_handler.start_processes()
```

If you paste the above code in a file called main.py, you can launch the workers by running:
```shell
python3 main.py
```

## Task Domains
Workers can be configured to start polling for work that is tagged by a task domain. See more on domains [here](https://orkes.io/content/developer-guides/task-to-domain).


```python
from conductor.client.worker.worker_task import WorkerTask

@WorkerTask(task_definition_name='python_annotated_task', domain='cool')
def python_annotated_task(input) -> object:
    return {'message': 'python is so cool :)'}
```

The above code would run a worker polling for task of type, *python_annotated_task*, but only for workflows that have a task to domain mapping specified with domain for this task as _cool_.

```json
"taskToDomain": {
   "python_annotated_task": "cool"
}
```

## Worker Configuration

### Using Config File

You can choose to pass an _worker.ini_ file for specifying worker arguments like domain and polling_interval. This allows for configuring your workers dynamically and hence provides the flexbility along with cleaner worker code. This file has to be in the same directory as the main.py of your worker application.

#### Format
```
[task_definition_name]
domain = <domain>
polling_interval = <polling-interval-in-ms>
```

#### Generic Properties
There is an option for specifying common set of properties which apply to all workers by putting them in the _DEFAULT_ section. All workers who don't have a domain or/and polling_interval specified will default to these values.

```
[DEFAULT]
domain = <domain>
polling_interval = <polling-interval-in-ms>
```

#### Example File
```
[DEFAULT]
domain = nice
polling_interval = 2000

[python_annotated_task_1]
domain = cool
polling_interval = 500

[python_annotated_task_2]
domain = hot
polling_interval = 300
```

With the presence of the above config file, you don't need to specify domain and poll_interval for any of the worker task types.

##### Without config
```python
from conductor.client.worker.worker_task import WorkerTask

@WorkerTask(task_definition_name='python_annotated_task_1', domain='cool', poll_interval=500.0)
def python_annotated_task(input) -> object:
    return {'message': 'python is so cool :)'}

@WorkerTask(task_definition_name='python_annotated_task_2', domain='hot', poll_interval=300.0)
def python_annotated_task_2(input) -> object:
    return {'message': 'python is so hot :)'}

@WorkerTask(task_definition_name='python_annotated_task_3', domain='nice', poll_interval=2000.0)
def python_annotated_task_3(input) -> object:
    return {'message': 'python is so nice :)'}

@WorkerTask(task_definition_name='python_annotated_task_4', domain='nice', poll_interval=2000.0)
def python_annotated_task_4(input) -> object:
    return {'message': 'python is very nice :)'}
```

##### With config
```python
from conductor.client.worker.worker_task import WorkerTask

@WorkerTask(task_definition_name='python_annotated_task_1')
def python_annotated_task(input) -> object:
    return {'message': 'python is so cool :)'}

@WorkerTask(task_definition_name='python_annotated_task_2')
def python_annotated_task_2(input) -> object:
    return {'message': 'python is so hot :)'}

@WorkerTask(task_definition_name='python_annotated_task_3')
def python_annotated_task_3(input) -> object:
    return {'message': 'python is so nice :)'}

@WorkerTask(task_definition_name='python_annotated_task_4')
def python_annotated_task_4(input) -> object:
    return {'message': 'python is very nice :)'}

```

### Using Environment Variables

Workers can also be configured at run time by using environment variables which override configuration files as well.

#### Format
```
conductor_worker_polling_interval=<polling-interval-in-ms>
conductor_worker_domain=<domain>
conductor_worker_<task_definition_name>_polling_interval=<polling-interval-in-ms>
conductor_worker_<task_definition_name>_domain=<domain>
```

#### Example
```
conductor_worker_polling_interval=2000
conductor_worker_domain=nice
conductor_worker_python_annotated_task_1_polling_interval=500
conductor_worker_python_annotated_task_1_domain=cool
conductor_worker_python_annotated_task_2_polling_interval=300
conductor_worker_python_annotated_task_2_domain=hot
```

### Order of Precedence
If the worker configuration is initialized using multiple mechanisms mentioned above then the following order of priority
will be considered from highest to lowest:
1. Environment Variables
2. Config File
3. Worker Constructor Arguments

See [Using Conductor Playground](https://orkes.io/content/docs/getting-started/playground/using-conductor-playground) for more details on how to use Playground environment for testing.

## Performance

### Concurrent Execution within a Worker (v1.2.5+)

The SDK now supports concurrent execution within a single worker using the `thread_count` parameter. This is **recommended** over creating multiple worker instances:

```python
from conductor.client.worker.worker_task import WorkerTask

@WorkerTask(
    task_definition_name='high_throughput_task',
    thread_count=10,      # Execute up to 10 tasks concurrently
    poll_interval=100     # Poll every 100ms
)
async def process_task(data: dict) -> dict:
    # Your worker logic here
    result = await process_data_async(data)
    return {'result': result}
```

**Benefits:**
- **Ultra-low latency**: 2-5ms average polling delay (down from 15-90ms)
- **Batch polling**: Fetches multiple tasks per API call (60-70% fewer API calls)
- **Adaptive backoff**: Prevents API hammering when queue is empty
- **Concurrent execution**: Tasks execute in background while polling continues
- **Single process**: Lower memory footprint vs multiple worker instances

**Performance metrics (thread_count=10):**
- Throughput: 250+ tasks/sec (continuous load)
- Efficiency: 80-85% of perfect parallelism
- P95 latency: <15ms
- P99 latency: <20ms

### Configuration Recommendations

**For maximum throughput:**
```python
@WorkerTask(
    task_definition_name='api_calls',
    thread_count=20,      # High concurrency for I/O-bound tasks
    poll_interval=10      # Aggressive polling (10ms)
)
```

**For balanced performance:**
```python
@WorkerTask(
    task_definition_name='data_processing',
    thread_count=10,      # Moderate concurrency
    poll_interval=100     # Standard polling (100ms)
)
```

**For CPU-bound tasks:**
```python
@WorkerTask(
    task_definition_name='image_processing',
    thread_count=4,       # Limited by CPU cores
    poll_interval=100
)
```

### Legacy: Multiple Worker Instances

For backward compatibility, you can still create multiple worker instances, but **thread_count is now preferred**:

```python
# Legacy approach (still works, but uses more memory)
workers = [
    SimplePythonWorker(task_definition_name='python_task_example'),
    SimplePythonWorker(task_definition_name='python_task_example'),
    SimplePythonWorker(task_definition_name='python_task_example'),
]

# Recommended approach (single worker with concurrency)
@WorkerTask(task_definition_name='python_task_example', thread_count=3)
def process_task(data):
    # Same functionality, less memory
    return process(data)
```

## C/C++ Support
Python is great, but at times you need to call into native C/C++ code. 
Here is an example how you can do that with Conductor SDK.

### 1. Export your C++ functions as `extern "C"`:
   * C++ function example (sum two integers)
        ```cpp
        #include <iostream>

        extern "C" int32_t get_sum(const int32_t A, const int32_t B) {
            return A + B;
        }
        ```
### 2. Compile and share its library:
   * C++ file name: `simple_cpp_lib.cpp`
   * Library output name goal: `lib.so`
        ```shell
        g++ -c -fPIC simple_cpp_lib.cpp -o simple_cpp_lib.o
        g++ -shared -Wl,-install_name,lib.so -o lib.so simple_cpp_lib.o
        ```
     
### 3. Use the C++ library in your python worker
You can use the Python library to call native code written in C++.  Here is an example that calls native C++ library
from the Python worker.
See [simple_cpp_lib.cpp](src/example/worker/cpp/simple_cpp_lib.cpp) 
and [simple_cpp_worker.py](src/example/worker/cpp/simple_cpp_worker.py) for complete working example.

```python
from conductor.client.http.models.task import Task
from conductor.client.http.models.task_result import TaskResult
from conductor.client.http.models.task_result_status import TaskResultStatus
from conductor.client.worker.worker_interface import WorkerInterface
from ctypes import cdll

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
```

## Long-Running Tasks and Lease Extension

For tasks that take longer than the configured `responseTimeoutSeconds`, the SDK provides automatic lease extension to prevent timeouts. See the comprehensive [Lease Extension Guide](../../LEASE_EXTENSION.md) for:

- How lease extension works
- Automatic vs manual control
- Usage patterns and best practices
- Troubleshooting common issues

**Quick example:**

```python
from conductor.client.context.task_context import TaskInProgress
from typing import Union

@worker_task(
    task_definition_name='long_task',
    lease_extend_enabled=True  # Default: automatic lease extension
)
def process_large_dataset(dataset_id: str) -> Union[dict, TaskInProgress]:
    ctx = get_task_context()
    poll_count = ctx.get_poll_count()

    # Process in chunks
    processed = process_chunk(dataset_id, chunk=poll_count)

    if processed < TOTAL_CHUNKS:
        # More work to do - extend lease
        return TaskInProgress(
            callback_after_seconds=60,
            output={'progress': processed}
        )
    else:
        # All done
        return {'status': 'completed', 'total_processed': processed}
```

### Next: [Create workflows using Code](../workflow/README.md)
