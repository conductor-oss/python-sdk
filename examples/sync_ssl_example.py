#!/usr/bin/env python3
"""
Simple example demonstrating sync client SSL configuration.

This example shows how to configure the Conductor Python SDK sync client
with various SSL/TLS settings for secure connections.
"""

import os
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients


def main():
    """
    Example of configuring sync client with SSL settings.
    """

    # Method 1: Configure SSL via Configuration constructor parameters

    # Basic SSL configuration with custom CA certificate
    config = Configuration(
        base_url="https://play.orkes.io",
        ssl_ca_cert="/path/to/ca-certificate.pem",
    )

    # Create clients with SSL configuration
    clients = OrkesClients(configuration=config)
    workflow_client = clients.get_workflow_client()
    task_client = clients.get_task_client()

    # Method 2: Configure SSL via environment variables

    # Set environment variables (you would typically do this in your shell or .env file)
    os.environ["CONDUCTOR_SERVER_URL"] = "https://play.orkes.io/api"
    os.environ["CONDUCTOR_SSL_CA_CERT"] = "/path/to/ca-certificate.pem"
    os.environ["CONDUCTOR_VERIFY_SSL"] = "true"

    # Configuration will automatically pick up environment variables
    config_env = Configuration()

    # Different SSL configurations

    # SSL with custom CA certificate file
    ssl_ca_file_config = Configuration(
        base_url="https://play.orkes.io",
        ssl_ca_cert="/path/to/ca-certificate.pem",
    )

    # SSL with custom CA certificate data (PEM string)
    ssl_ca_data_config = Configuration(
        base_url="https://play.orkes.io",
        ca_cert_data="""-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKoK/Ovj8EUMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMTYwMjEyMTQ0NDQ2WhcNMjYwMjEwMTQ0NDQ2WjBF
-----END CERTIFICATE-----""",
    )

    # SSL with client certificate authentication
    client_cert_config = Configuration(
        base_url="https://play.orkes.io",
        ssl_ca_cert="/path/to/ca-certificate.pem",
    )

    # SSL with disabled hostname verification
    no_hostname_verify_config = Configuration(
        base_url="https://play.orkes.io",
        ssl_ca_cert="/path/to/ca-certificate.pem",
    )

    # SSL with completely disabled verification (NOT RECOMMENDED for production)
    no_ssl_verify_config = Configuration(
        base_url="https://play.orkes.io",
    )
    # Disable SSL verification entirely
    no_ssl_verify_config.verify_ssl = False

    # SSL with httpx-specific configurations
    import httpx
    import ssl

    # httpx client with custom SSL settings
    httpx_ssl_client = httpx.Client(
        verify="/path/to/ca-certificate.pem",  # CA certificate file
        cert=(
            "/path/to/client-certificate.pem",
            "/path/to/client-key.pem",
        ),  # Client cert
        timeout=httpx.Timeout(120.0),
        follow_redirects=True,
    )

    httpx_ssl_config = Configuration(
        base_url="https://play.orkes.io",
    )
    httpx_ssl_config.http_connection = httpx_ssl_client

    # httpx client with disabled SSL verification
    httpx_no_ssl_client = httpx.Client(
        verify=False,  # Disable SSL verification
        timeout=httpx.Timeout(120.0),
        follow_redirects=True,
    )

    httpx_no_ssl_config = Configuration(
        base_url="https://play.orkes.io",
    )
    httpx_no_ssl_config.http_connection = httpx_no_ssl_client

    # SSL with custom SSL context (advanced usage)

    # Create custom SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.load_verify_locations("/path/to/ca-certificate.pem")
    ssl_context.load_cert_chain(
        certfile="/path/to/client-certificate.pem", keyfile="/path/to/client-key.pem"
    )

    # Create custom httpx client with SSL context
    custom_client = httpx.Client(
        verify=ssl_context,
        timeout=httpx.Timeout(120.0),
        follow_redirects=True,
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    )

    custom_ssl_config = Configuration(
        base_url="https://play.orkes.io",
        ssl_ca_cert="/path/to/ca-certificate.pem",
    )
    custom_ssl_config.http_connection = custom_client

    # Note: The sync client uses httpx instead of requests
    # All SSL configurations are handled through the Configuration class
    # or by providing a custom httpx.Client instance via http_connection

    # Example: Get workflow definitions (this will use SSL configuration)
    # Note: This will only work if you have valid credentials and SSL certificates

    try:
        workflows = workflow_client.search()
        print(f"Found {len(workflows)} workflows")
    except Exception as e:
        print(f"SSL connection failed: {e}")
        print("Make sure your SSL certificates are valid and accessible")

    # Example usage with different SSL configurations:
    # You can use any of the configurations above by passing them to OrkesClients

    # Example with client certificate authentication:
    # clients_with_cert = OrkesClients(configuration=client_cert_config)
    # workflow_client_cert = clients_with_cert.get_workflow_client()

    # Example with custom httpx client:
    # clients_with_httpx = OrkesClients(configuration=httpx_ssl_config)
    # workflow_client_httpx = clients_with_httpx.get_workflow_client()


if __name__ == "__main__":
    main()
