# Worker Discovery

Automatic worker discovery from packages, similar to Spring's component scanning in Java.

## Overview

The `WorkerLoader` class provides automatic discovery of workers decorated with `@worker_task` by scanning Python packages. This eliminates the need to manually register each worker.

**Important**: Worker discovery is **execution-model agnostic**. The same discovery process works for both:
- **TaskHandler** (sync, multiprocessing-based execution)
- **TaskHandlerAsyncIO** (async, asyncio-based execution)

Discovery just imports modules and registers workers - it doesn't care whether workers are sync or async functions. The execution model is determined by which TaskHandler you use, not by the discovery process.

## Quick Start

### Basic Usage

```python
from conductor.client.worker.worker_loader import auto_discover_workers
from conductor.client.automator.task_handler_asyncio import TaskHandlerAsyncIO
from conductor.client.configuration.configuration import Configuration

# Auto-discover workers from packages
loader = auto_discover_workers(packages=['my_app.workers'])

# Start task handler with discovered workers
async with TaskHandlerAsyncIO(configuration=Configuration()) as handler:
    await handler.wait()
```

### Directory Structure

```
my_app/
├── workers/
│   ├── __init__.py
│   ├── order_tasks.py      # Contains @worker_task decorated functions
│   ├── payment_tasks.py
│   └── notification_tasks.py
└── main.py
```

## Examples

### Example 1: Scan Single Package

```python
from conductor.client.worker.worker_loader import WorkerLoader

loader = WorkerLoader()
loader.scan_packages(['my_app.workers'])

# Print discovered workers
loader.print_summary()
```

### Example 2: Scan Multiple Packages

```python
loader = WorkerLoader()
loader.scan_packages([
    'my_app.workers',
    'my_app.tasks',
    'shared_lib.workers'
])
```

### Example 3: Convenience Function

```python
from conductor.client.worker.worker_loader import scan_for_workers

# Shorthand for scanning packages
loader = scan_for_workers('my_app.workers', 'my_app.tasks')
```

### Example 4: Scan Specific Modules

```python
loader = WorkerLoader()

# Scan individual modules instead of entire packages
loader.scan_module('my_app.workers.order_tasks')
loader.scan_module('my_app.workers.payment_tasks')
```

### Example 5: Non-Recursive Scanning

```python
# Scan only top-level package, not subpackages
loader.scan_packages(['my_app.workers'], recursive=False)
```

### Example 6: Production Use Case (AsyncIO)

```python
import asyncio
from conductor.client.worker.worker_loader import auto_discover_workers
from conductor.client.automator.task_handler_asyncio import TaskHandlerAsyncIO
from conductor.client.configuration.configuration import Configuration

async def main():
    # Auto-discover all workers
    loader = auto_discover_workers(
        packages=[
            'my_app.workers',
            'my_app.tasks'
        ],
        print_summary=True  # Print discovery summary
    )

    # Start async task handler
    config = Configuration()

    async with TaskHandlerAsyncIO(configuration=config) as handler:
        print(f"Started {loader.get_worker_count()} workers")
        await handler.wait()

if __name__ == '__main__':
    asyncio.run(main())
```

### Example 7: Production Use Case (Sync Multiprocessing)

```python
from conductor.client.worker.worker_loader import auto_discover_workers
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration

def main():
    # Auto-discover all workers (same discovery process)
    loader = auto_discover_workers(
        packages=[
            'my_app.workers',
            'my_app.tasks'
        ],
        print_summary=True
    )

    # Start sync task handler
    config = Configuration()

    handler = TaskHandler(
        configuration=config,
        scan_for_annotated_workers=True  # Uses discovered workers
    )

    print(f"Started {loader.get_worker_count()} workers")
    handler.start_processes()  # Blocks

if __name__ == '__main__':
    main()
```

## API Reference

### WorkerLoader

Main class for discovering workers from packages.

#### Methods

**`scan_packages(package_names: List[str], recursive: bool = True)`**
- Scan packages for workers
- `recursive=True`: Scan subpackages
- `recursive=False`: Scan only top-level

**`scan_module(module_name: str)`**
- Scan a specific module

**`scan_path(path: str, package_prefix: str = '')`**
- Scan a filesystem path

**`get_workers() -> List[WorkerInterface]`**
- Get all discovered workers

**`get_worker_count() -> int`**
- Get count of discovered workers

**`get_worker_names() -> List[str]`**
- Get list of task definition names

**`print_summary()`**
- Print discovery summary

### Convenience Functions

**`scan_for_workers(*package_names, recursive=True) -> WorkerLoader`**
```python
loader = scan_for_workers('my_app.workers', 'my_app.tasks')
```

**`auto_discover_workers(packages=None, paths=None, print_summary=True) -> WorkerLoader`**
```python
loader = auto_discover_workers(
    packages=['my_app.workers'],
    print_summary=True
)
```

## Sync vs Async Compatibility

Worker discovery is **completely independent** of execution model:

```python
# Same discovery for both execution models
loader = auto_discover_workers(packages=['my_app.workers'])

# Option 1: Use with AsyncIO (async execution)
async with TaskHandlerAsyncIO(configuration=config) as handler:
    await handler.wait()

# Option 2: Use with TaskHandler (sync multiprocessing)
handler = TaskHandler(configuration=config, scan_for_annotated_workers=True)
handler.start_processes()
```

### How Each Handler Executes Discovered Workers

| Worker Type | TaskHandler (Sync) | TaskHandlerAsyncIO (Async) |
|-------------|-------------------|---------------------------|
| **Sync functions** | Run directly in worker process | Run in thread pool executor |
| **Async functions** | Run in event loop in worker process | Run natively in event loop |

**Key Insight**: Discovery finds and registers workers. Execution model is determined by which TaskHandler you instantiate.

## How It Works

1. **Package Scanning**: The loader imports Python packages and modules
2. **Automatic Registration**: When modules are imported, `@worker_task` decorators automatically register workers
3. **Worker Retrieval**: The loader retrieves registered workers from the global registry
4. **Execution Model**: Determined by TaskHandler type, not by discovery

### Worker Registration Flow

```python
# In my_app/workers/order_tasks.py
from conductor.client.worker.worker_task import worker_task

@worker_task(task_definition_name='process_order', thread_count=10)
async def process_order(order_id: str) -> dict:
    return {'status': 'processed'}

# When this module is imported:
# 1. @worker_task decorator runs
# 2. Worker is registered in global registry
# 3. WorkerLoader can retrieve it
```

## Best Practices

### 1. Organize Workers by Domain

```
my_app/
├── workers/
│   ├── order/          # Order-related workers
│   │   ├── process.py
│   │   └── validate.py
│   ├── payment/        # Payment-related workers
│   │   ├── charge.py
│   │   └── refund.py
│   └── notification/   # Notification workers
│       ├── email.py
│       └── sms.py
```

### 2. Use Package Init Files

```python
# my_app/workers/__init__.py
"""
Workers package

All worker modules in this package will be discovered automatically
when using WorkerLoader.scan_packages(['my_app.workers'])
"""
```

### 3. Environment-Specific Loading

```python
import os

# Load different workers based on environment
env = os.getenv('ENV', 'production')

if env == 'production':
    packages = ['my_app.workers']
else:
    packages = ['my_app.workers', 'my_app.test_workers']

loader = auto_discover_workers(packages=packages)
```

### 4. Lazy Loading

```python
# Load workers on-demand
def get_worker_loader():
    if not hasattr(get_worker_loader, '_loader'):
        get_worker_loader._loader = auto_discover_workers(
            packages=['my_app.workers']
        )
    return get_worker_loader._loader
```

## Comparison with Java SDK

| Java SDK | Python SDK |
|----------|------------|
| `@WorkerTask` annotation | `@worker_task` decorator |
| Component scanning via Spring | `WorkerLoader.scan_packages()` |
| `@ComponentScan("com.example.workers")` | `scan_packages(['my_app.workers'])` |
| Classpath scanning | Module/package scanning |
| Automatic during Spring context startup | Manual via `WorkerLoader` |

## Troubleshooting

### Workers Not Discovered

**Problem**: Workers not appearing after scanning

**Solutions**:
1. Ensure package has `__init__.py` files
2. Check package name is correct
3. Verify worker functions are decorated with `@worker_task`
4. Check for import errors in worker modules

### Import Errors

**Problem**: Modules fail to import during scanning

**Solutions**:
1. Check module dependencies are installed
2. Verify `PYTHONPATH` includes necessary directories
3. Look for circular imports
4. Check syntax errors in worker files

### Duplicate Workers

**Problem**: Same worker discovered multiple times

**Cause**: Package scanned multiple times or circular imports

**Solution**: Track scanned modules (WorkerLoader does this automatically)

## Advanced Usage

### Custom Worker Registry

```python
from conductor.client.automator.task_handler import get_registered_workers

# Get workers directly from registry
workers = get_registered_workers()

# Filter workers
order_workers = [w for w in workers if 'order' in w.get_task_definition_name()]
```

### Dynamic Module Loading

```python
import importlib

# Dynamically load modules based on configuration
config = load_config()

for module_name in config['worker_modules']:
    importlib.import_module(module_name)

# Workers are now registered
workers = get_registered_workers()
```

### Integration with Flask/FastAPI

```python
from fastapi import FastAPI
from conductor.client.worker.worker_loader import auto_discover_workers

app = FastAPI()

@app.on_event("startup")
async def startup():
    # Discover workers on application startup
    loader = auto_discover_workers(packages=['my_app.workers'])
    print(f"Discovered {loader.get_worker_count()} workers")
```

## See Also

- [Worker Task Documentation](./docs/workers.md)
- [Task Handler Documentation](./docs/task_handler.md)
- [Examples](./examples/worker_discovery_example.py)
