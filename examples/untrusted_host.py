"""
Example demonstrating how to connect to a Conductor server with untrusted/self-signed SSL certificates.

This is useful for:
- Development environments with self-signed certificates
- Internal servers with custom CA certificates
- Testing environments

WARNING: Disabling SSL verification should only be used in development/testing.
Never use this in production as it makes you vulnerable to man-in-the-middle attacks.
"""

import httpx
import warnings

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.worker.worker_task import worker_task


@worker_task(task_definition_name='hello')
def hello(name: str) -> str:
    print(f'executing.... {name}')
    return f'Hello {name}'


def main():
    # Suppress SSL verification warnings
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

    # Create httpx client with SSL verification disabled
    # verify=False disables SSL certificate verification
    http_client = httpx.Client(
        verify=False,  # Disable SSL verification
        timeout=httpx.Timeout(120.0, connect=10.0),
        follow_redirects=True,
        http2=True
    )

    # Configure Conductor to use the custom HTTP client
    api_config = Configuration()
    api_config.http_connection = http_client

    print("=" * 80)
    print("Untrusted Host Example")
    print("=" * 80)
    print("")
    print("WARNING: SSL verification is DISABLED!")
    print("This should only be used in development/testing environments.")
    print("")
    print("Worker available:")
    print("  - hello: Simple greeting worker")
    print("")
    print("Press Ctrl+C to stop...")
    print("=" * 80)
    print("")

    try:
        # Start workers with the custom configuration
        with TaskHandler(
            configuration=api_config,
            scan_for_annotated_workers=True
        ) as task_handler:
            task_handler.start_processes()
            task_handler.join_processes()

    except KeyboardInterrupt:
        print("\nShutting down gracefully...")

    finally:
        # Close the HTTP client
        http_client.close()

    print("\nWorkers stopped. Goodbye!")


if __name__ == '__main__':
    main()
