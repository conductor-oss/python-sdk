import asyncio
import os
from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients


async def main():
    """
    Example of configuring async client with proxy settings.
    """
    
    # Method 1: Configure proxy via Configuration constructor parameters
    
    # Basic proxy configuration
    config = Configuration(
        server_url="https://play.orkes.io/api",  # Or your Conductor server URL
        proxy="http://proxy.company.com:8080",  # Your proxy server
        proxy_headers={
            "Authorization": "Bearer your-proxy-token",  # Optional proxy auth
            "User-Agent": "Conductor-Python-Async-SDK/1.0"
        }
    )

    # Method 2: Configure proxy via environment variables
    
    # Set environment variables (you would typically do this in your shell or .env file)
    os.environ["CONDUCTOR_SERVER_URL"] = "https://play.orkes.io/api"
    os.environ["CONDUCTOR_PROXY"] = "http://proxy.company.com:8080"
    os.environ["CONDUCTOR_PROXY_HEADERS"] = '{"Authorization": "Bearer your-proxy-token"}'
    
    # Configuration will automatically pick up environment variables
    config_env = Configuration()
    
    # Method 3: Different proxy types
    
    # HTTP proxy
    http_config = Configuration(
        server_url="https://play.orkes.io/api",
        proxy="http://proxy.company.com:8080"
    )
    
    # HTTPS proxy
    https_config = Configuration(
        server_url="https://play.orkes.io/api",
        proxy="https://proxy.company.com:8080"
    )
    
    # SOCKS5 proxy
    socks5_config = Configuration(
        server_url="https://play.orkes.io/api",
        proxy="socks5://proxy.company.com:1080"
    )
    
    # SOCKS4 proxy
    socks4_config = Configuration(
        server_url="https://play.orkes.io/api",
        proxy="socks4://proxy.company.com:1080"
    )
    
    # Usage:
    
    # Create API client with proxy configuration
    async with ApiClient(config) as api_client:
        # Create OrkesClients with the API client
        orkes_clients = OrkesClients(api_client, config)
        workflow_client = orkes_clients.get_workflow_client()
        
        # Example: Get workflow definitions (this will go through the proxy)
        # Note: This will only work if you have valid credentials and the proxy is accessible
        
        workflows = await workflow_client.search_workflows()
        print(f"Found {len(workflows)} workflows")


if __name__ == "__main__":
    asyncio.run(main())
