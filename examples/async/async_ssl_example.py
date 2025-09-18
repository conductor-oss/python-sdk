import asyncio
import os
from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients


async def main():
    """
    Example of configuring async client with SSL settings.
    """

    # Method 1: Configure SSL via Configuration constructor parameters

    # Basic SSL configuration with custom CA certificate
    config = Configuration(
        server_url="https://play.orkes.io/api",  # Or your Conductor server URL
        ssl_ca_cert="/path/to/ca-certificate.pem",  # Path to CA certificate file
    )

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
        server_url="https://play.orkes.io/api",
        ssl_ca_cert="/path/to/ca-certificate.pem",
    )

    # SSL with custom CA certificate data (PEM string)
    ssl_ca_data_config = Configuration(
        server_url="https://play.orkes.io/api",
        ca_cert_data="""-----BEGIN CERTIFICATE-----
            MIIDXTCCAkWgAwIBAgIJAKoK/Ovj8EUMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV
            BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
            aWRnaXRzIFB0eSBMdGQwHhcNMTYwMjEyMTQ0NDQ2WhcNMjYwMjEwMTQ0NDQ2WjBF
            -----END CERTIFICATE-----""",
    )

    # SSL with client certificate authentication
    client_cert_config = Configuration(
        server_url="https://play.orkes.io/api",
        ssl_ca_cert="/path/to/ca-certificate.pem",
    )

    # SSL with disabled hostname verification
    no_hostname_verify_config = Configuration(
        server_url="https://play.orkes.io/api",
        ssl_ca_cert="/path/to/ca-certificate.pem",
    )

    # SSL with Server Name Indication (SNI)
    sni_config = Configuration(
        server_url="https://play.orkes.io/api",
        ssl_ca_cert="/path/to/ca-certificate.pem",
    )

    # SSL with completely disabled verification (NOT RECOMMENDED for production)
    no_ssl_verify_config = Configuration(
        server_url="https://play.orkes.io/api",
    )

    # SSL with custom SSL context (advanced usage)
    import ssl

    # Create custom SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.load_verify_locations("/path/to/ca-certificate.pem")
    ssl_context.load_cert_chain(
        certfile="/path/to/client-certificate.pem", keyfile="/path/to/client-key.pem"
    )
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    # Usage

    # Create API client with SSL configuration
    async with ApiClient(config) as api_client:
        # Create OrkesClients with the API client
        orkes_clients = OrkesClients(api_client, config)
        workflow_client = orkes_clients.get_workflow_client()

        # Example: Get workflow definitions (this will use SSL configuration)
        # Note: This will only work if you have valid credentials and SSL certificates

        try:
            workflows = await workflow_client.search_workflows()
            print(f"Found {len(workflows)} workflows")
        except Exception as e:
            print(f"SSL connection failed: {e}")
            print("Make sure your SSL certificates are valid and accessible")


if __name__ == "__main__":
    asyncio.run(main())
