#!/usr/bin/env python3
"""
Simple example demonstrating sync client proxy configuration.

This example shows how to configure the Conductor Python SDK sync client
to work through a proxy server.
"""

import os
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients


def main():
    """
    Example of configuring sync client with proxy settings.
    """

    # Method 1: Configure proxy via Configuration constructor parameters

    # Basic proxy configuration
    config = Configuration(
        base_url="https://play.orkes.io",  # Or your Conductor server URL
        proxy="http://your-proxy.com:8080",  # Your proxy server
        proxy_headers={
            "Authorization": "Bearer your-proxy-token",  # Optional proxy auth
            "User-Agent": "Conductor-Python-SDK/1.0",
        },
    )

    # Create clients with proxy configuration
    clients = OrkesClients(configuration=config)
    workflow_client = clients.get_workflow_client()
    task_client = clients.get_task_client()

    # Method 2: Configure proxy via environment variables

    # Set environment variables (you would typically do this in your shell or .env file)
    os.environ["CONDUCTOR_SERVER_URL"] = "https://play.orkes.io/api"
    os.environ["CONDUCTOR_PROXY"] = "http://your-proxy.com:8080"
    os.environ["CONDUCTOR_PROXY_HEADERS"] = (
        '{"Authorization": "Bearer your-proxy-token"}'
    )

    # Configuration will automatically pick up environment variables
    config_env = Configuration()

    # Different proxy types

    # HTTP proxy
    http_config = Configuration(
        base_url="https://play.orkes.io", proxy="http://your-proxy.com:8080"
    )

    # HTTPS proxy
    https_config = Configuration(
        base_url="https://play.orkes.io", proxy="https://your-proxy.com:8080"
    )

    # SOCKS5 proxy
    socks5_config = Configuration(
        base_url="https://play.orkes.io", proxy="socks5://your-proxy.com:1080"
    )

    # SOCKS4 proxy
    socks4_config = Configuration(
        base_url="https://play.orkes.io", proxy="socks4://your-proxy.com:1080"
    )

    # Example: Get workflow definitions (this will go through the proxy)
    # Note: This will only work if you have valid credentials and the proxy is accessible

    workflows = workflow_client.search()
    print(f"Found {len(workflows)} workflows")


if __name__ == "__main__":
    main()
