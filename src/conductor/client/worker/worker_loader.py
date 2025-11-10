"""
Worker Loader - Dynamic worker discovery from packages

Provides package scanning to automatically discover workers decorated with @worker_task,
similar to Spring's component scanning in Java.

Usage:
    from conductor.client.worker.worker_loader import WorkerLoader
    from conductor.client.automator.task_handler_asyncio import TaskHandlerAsyncIO

    # Scan packages for workers
    loader = WorkerLoader()
    loader.scan_packages(['my_app.workers', 'my_app.tasks'])

    # Or scan specific modules
    loader.scan_module('my_app.workers.order_tasks')

    # Get discovered workers
    workers = loader.get_workers()

    # Start task handler with discovered workers
    task_handler = TaskHandlerAsyncIO(configuration=config)
    await task_handler.start()
"""

from __future__ import annotations
import importlib
import inspect
import logging
import pkgutil
import sys
from pathlib import Path
from typing import List, Set, Optional, Dict
from conductor.client.worker.worker_interface import WorkerInterface


logger = logging.getLogger(__name__)


class WorkerLoader:
    """
    Discovers and loads workers from Python packages.

    Workers are discovered by scanning packages for functions decorated
    with @worker_task or @WorkerTask.

    Example:
        # In my_app/workers/order_workers.py:
        from conductor.client.worker.worker_task import worker_task

        @worker_task(task_definition_name='process_order')
        def process_order(order_id: str) -> dict:
            return {'status': 'processed'}

        # In main.py:
        loader = WorkerLoader()
        loader.scan_packages(['my_app.workers'])
        workers = loader.get_workers()

        # All @worker_task decorated functions are now registered
    """

    def __init__(self):
        self._scanned_modules: Set[str] = set()
        self._discovered_workers: List[WorkerInterface] = []

    def scan_packages(self, package_names: List[str], recursive: bool = True) -> None:
        """
        Scan packages for workers decorated with @worker_task.

        Args:
            package_names: List of package names to scan (e.g., ['my_app.workers', 'my_app.tasks'])
            recursive: If True, scan subpackages recursively (default: True)

        Example:
            loader = WorkerLoader()

            # Scan single package
            loader.scan_packages(['my_app.workers'])

            # Scan multiple packages
            loader.scan_packages(['my_app.workers', 'my_app.tasks', 'shared.workers'])

            # Scan only top-level (no subpackages)
            loader.scan_packages(['my_app.workers'], recursive=False)
        """
        for package_name in package_names:
            try:
                logger.info(f"Scanning package: {package_name}")
                self._scan_package(package_name, recursive=recursive)
            except Exception as e:
                logger.error(f"Failed to scan package {package_name}: {e}")
                raise

    def scan_module(self, module_name: str) -> None:
        """
        Scan a specific module for workers.

        Args:
            module_name: Full module name (e.g., 'my_app.workers.order_tasks')

        Example:
            loader = WorkerLoader()
            loader.scan_module('my_app.workers.order_tasks')
            loader.scan_module('my_app.workers.payment_tasks')
        """
        if module_name in self._scanned_modules:
            logger.debug(f"Module {module_name} already scanned, skipping")
            return

        try:
            logger.debug(f"Scanning module: {module_name}")
            module = importlib.import_module(module_name)
            self._scanned_modules.add(module_name)

            # Import the module to trigger @worker_task registration
            # The decorator automatically registers workers when the module loads

            logger.debug(f"Successfully scanned module: {module_name}")

        except Exception as e:
            logger.error(f"Failed to scan module {module_name}: {e}")
            raise

    def scan_path(self, path: str, package_prefix: str = '') -> None:
        """
        Scan a filesystem path for Python modules.

        Args:
            path: Filesystem path to scan
            package_prefix: Package prefix to prepend to discovered modules

        Example:
            loader = WorkerLoader()
            loader.scan_path('/app/workers', package_prefix='my_app.workers')
        """
        path_obj = Path(path)

        if not path_obj.exists():
            raise ValueError(f"Path does not exist: {path}")

        if not path_obj.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        logger.info(f"Scanning path: {path}")

        # Add path to sys.path if not already there
        if str(path_obj.parent) not in sys.path:
            sys.path.insert(0, str(path_obj.parent))

        # Scan all Python files in directory
        for py_file in path_obj.rglob('*.py'):
            if py_file.name.startswith('_'):
                continue  # Skip __init__.py and private modules

            # Convert path to module name
            relative_path = py_file.relative_to(path_obj)
            module_parts = list(relative_path.parts[:-1]) + [relative_path.stem]

            if package_prefix:
                module_name = f"{package_prefix}.{'.'.join(module_parts)}"
            else:
                module_name = path_obj.name + '.' + '.'.join(module_parts)

            try:
                self.scan_module(module_name)
            except Exception as e:
                logger.warning(f"Failed to import module {module_name}: {e}")

    def get_workers(self) -> List[WorkerInterface]:
        """
        Get all discovered workers.

        Returns:
            List of WorkerInterface instances

        Note:
            Workers are automatically registered when modules are imported.
            This method retrieves them from the global worker registry.
        """
        from conductor.client.automator.task_handler import get_registered_workers
        return get_registered_workers()

    def get_worker_count(self) -> int:
        """
        Get the number of discovered workers.

        Returns:
            Count of registered workers
        """
        return len(self.get_workers())

    def get_worker_names(self) -> List[str]:
        """
        Get the names of all discovered workers.

        Returns:
            List of task definition names
        """
        return [worker.get_task_definition_name() for worker in self.get_workers()]

    def print_summary(self) -> None:
        """
        Print a summary of discovered workers.

        Example output:
            Discovered 5 workers from 3 modules:
              • process_order (from my_app.workers.order_tasks)
              • process_payment (from my_app.workers.payment_tasks)
              • send_email (from my_app.workers.notification_tasks)
        """
        workers = self.get_workers()

        print(f"\nDiscovered {len(workers)} workers from {len(self._scanned_modules)} modules:")

        for worker in workers:
            task_name = worker.get_task_definition_name()
            print(f"  • {task_name}")

        print()

    def _scan_package(self, package_name: str, recursive: bool = True) -> None:
        """
        Internal method to scan a package and its subpackages.

        Args:
            package_name: Package name to scan
            recursive: Whether to scan subpackages
        """
        try:
            # Import the package
            package = importlib.import_module(package_name)

            # If package has __path__, it's a package (not a module)
            if hasattr(package, '__path__'):
                # Scan all modules in package
                for importer, modname, ispkg in pkgutil.walk_packages(
                    path=package.__path__,
                    prefix=package.__name__ + '.',
                    onerror=lambda x: logger.warning(f"Error importing module: {x}")
                ):
                    if recursive or not ispkg:
                        self.scan_module(modname)
            else:
                # It's a module, just scan it
                self.scan_module(package_name)

        except ImportError as e:
            logger.error(f"Failed to import package {package_name}: {e}")
            raise


def scan_for_workers(*package_names: str, recursive: bool = True) -> WorkerLoader:
    """
    Convenience function to scan packages for workers.

    Args:
        *package_names: Package names to scan
        recursive: Whether to scan subpackages recursively (default: True)

    Returns:
        WorkerLoader instance with discovered workers

    Example:
        # Scan packages
        loader = scan_for_workers('my_app.workers', 'my_app.tasks')

        # Print summary
        loader.print_summary()

        # Start task handler
        async with TaskHandlerAsyncIO(configuration=config) as handler:
            await handler.wait()
    """
    loader = WorkerLoader()
    loader.scan_packages(list(package_names), recursive=recursive)
    return loader


# Convenience function for common use case
def auto_discover_workers(
    packages: Optional[List[str]] = None,
    paths: Optional[List[str]] = None,
    print_summary: bool = True
) -> WorkerLoader:
    """
    Auto-discover workers from packages and/or filesystem paths.

    Args:
        packages: List of package names to scan (e.g., ['my_app.workers'])
        paths: List of filesystem paths to scan (e.g., ['/app/workers'])
        print_summary: Whether to print discovery summary (default: True)

    Returns:
        WorkerLoader instance

    Example:
        # Discover from packages
        loader = auto_discover_workers(packages=['my_app.workers'])

        # Discover from filesystem
        loader = auto_discover_workers(paths=['/app/workers'])

        # Discover from both
        loader = auto_discover_workers(
            packages=['my_app.workers'],
            paths=['/app/additional_workers']
        )

        # Start task handler with discovered workers
        async with TaskHandlerAsyncIO(configuration=config) as handler:
            await handler.wait()
    """
    loader = WorkerLoader()

    if packages:
        loader.scan_packages(packages)

    if paths:
        for path in paths:
            loader.scan_path(path)

    if print_summary:
        loader.print_summary()

    return loader
