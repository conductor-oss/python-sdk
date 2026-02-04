"""
Multi-Homed Workers Example

This example demonstrates how to configure workers to poll tasks from 
multiple Conductor servers simultaneously for high availability.

Multi-homed workers provide:
- Disaster recovery: If one server goes down, workers continue polling others
- Active-active deployments: Workers poll all servers in parallel
- Geographic distribution: Poll from servers in different regions
- Built-in resilience: Circuit breaker (skip down servers), timeouts, and rapid recovery

Usage:
------
Option 1: Environment Variables (recommended for production)
    export CONDUCTOR_SERVER_URL=https://east.example.com/api,https://west.example.com/api
    export CONDUCTOR_AUTH_KEY=key1,key2
    export CONDUCTOR_AUTH_SECRET=secret1,secret2
    python multi_homed_workers.py

Option 2: Programmatic Configuration
    python multi_homed_workers.py --programmatic

Option 3: Mixed (single server, backward compatible)
    export CONDUCTOR_SERVER_URL=https://conductor.example.com/api
    python multi_homed_workers.py
"""

import argparse
import logging
import os
import sys
import time

from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.worker.worker_task import worker_task

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# Worker Definitions
# =============================================================================

@worker_task(task_definition_name='multi_homed_example_task')
def example_worker(name: str) -> dict:
    """
    Simple worker that processes tasks from any configured server.
    
    The SDK automatically:
    - Polls all configured servers in parallel
    - Tracks which server each task came from
    - Routes updates back to the originating server
    """
    logger.info(f"Processing task for: {name}")
    return {
        'message': f'Hello {name}!',
        'processed_by': os.getpid(),
        'timestamp': time.time()
    }


@worker_task(task_definition_name='multi_homed_async_task', thread_count=10)
async def async_example_worker(data: dict) -> dict:
    """
    Async worker with high concurrency - also works with multi-homed servers.
    """
    import asyncio
    await asyncio.sleep(0.1)  # Simulate async I/O
    return {
        'processed': True,
        'input_keys': list(data.keys()) if data else []
    }


# =============================================================================
# Configuration Examples
# =============================================================================

def get_env_var_configuration():
    """
    Uses comma-separated environment variables for multi-homed configuration.
    
    Environment Variables:
        CONDUCTOR_SERVER_URL: comma-separated server URLs
        CONDUCTOR_AUTH_KEY: comma-separated auth keys (must match server count)
        CONDUCTOR_AUTH_SECRET: comma-separated auth secrets (must match server count)
    
    Returns:
        List of Configuration objects (auto-parsed from env vars)
    """
    # Configuration.from_env_multi() automatically parses comma-separated env vars
    configs = Configuration.from_env_multi()
    
    logger.info(f"Loaded {len(configs)} server configuration(s) from environment")
    for i, cfg in enumerate(configs):
        has_auth = "Yes" if cfg.authentication_settings else "No"
        logger.info(f"  Server {i+1}: {cfg.host} (Auth: {has_auth})")
    
    return configs


def get_programmatic_configuration():
    """
    Creates multi-homed configuration programmatically.
    
    This approach is useful when:
    - Servers are discovered dynamically
    - Different servers need different SSL/proxy settings
    - Configuration comes from a secrets manager
    
    Returns:
        List of Configuration objects
    """
    # Example: Configure two servers
    configs = [
        Configuration(
            server_api_url="http://localhost:8080/api",
            # Optional: Add authentication
            # authentication_settings=AuthenticationSettings(
            #     key_id="your-key-1",
            #     key_secret="your-secret-1"
            # ),
            debug=False
        ),
        Configuration(
            server_api_url="http://localhost:8081/api",
            # authentication_settings=AuthenticationSettings(
            #     key_id="your-key-2",
            #     key_secret="your-secret-2"
            # ),
            debug=False
        ),
    ]
    
    logger.info(f"Created {len(configs)} server configuration(s) programmatically")
    for i, cfg in enumerate(configs):
        logger.info(f"  Server {i+1}: {cfg.host}")
    
    return configs


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Multi-Homed Workers Example')
    parser.add_argument(
        '--programmatic',
        action='store_true',
        help='Use programmatic configuration instead of environment variables'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='Duration to run workers in seconds (default: 60)'
    )
    args = parser.parse_args()
    
    # Get configuration
    if args.programmatic:
        logger.info("Using programmatic configuration...")
        configs = get_programmatic_configuration()
    else:
        logger.info("Using environment variable configuration...")
        configs = get_env_var_configuration()
    
    # Display multi-homed status
    if len(configs) > 1:
        logger.info(f"🌐 MULTI-HOMED MODE: Workers will poll {len(configs)} servers in parallel")
    else:
        logger.info(f"📡 SINGLE SERVER MODE: Workers will poll 1 server")
    
    # Create TaskHandler with multi-homed configuration
    task_handler = TaskHandler(
        configuration=configs,  # Pass list of configurations
        scan_for_annotated_workers=True
    )
    
    try:
        # Start workers
        logger.info("Starting worker processes...")
        task_handler.start_processes()
        
        logger.info(f"Workers running. Will stop after {args.duration} seconds.")
        logger.info("Create workflows with tasks 'multi_homed_example_task' or 'multi_homed_async_task' to test.")
        
        # Run for specified duration
        time.sleep(args.duration)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        logger.info("Stopping workers...")
        task_handler.stop_processes()
        logger.info("Workers stopped")


if __name__ == '__main__':
    main()
