# Proxy Configuration

The Conductor Python SDK supports proxy configuration for both synchronous and asynchronous clients. This is useful when your application needs to route traffic through corporate firewalls, load balancers, or other network intermediaries.

## Table of Contents

- [Supported Proxy Types](#supported-proxy-types)
- [Client Proxy Configuration](#client-proxy-configuration)
- [Environment Variable Configuration](#environment-variable-configuration)
- [Advanced Proxy Configuration](#advanced-proxy-configuration)
- [Troubleshooting](#troubleshooting)

## Supported Proxy Types

- **HTTP Proxy**: `http://proxy.example.com:8080`
- **HTTPS Proxy**: `https://proxy.example.com:8443`
- **SOCKS4 Proxy**: `socks4://proxy.example.com:1080`
- **SOCKS5 Proxy**: `socks5://proxy.example.com:1080`
- **Proxy with Authentication**: `http://username:password@proxy.example.com:8080`

> [!NOTE]
> For SOCKS proxy support, install the additional dependency: `pip install httpx[socks]`

## Client Proxy Configuration

### Basic HTTP Proxy Configuration

```python
from conductor.client.configuration.configuration import Configuration
from conductor.shared.configuration.settings.authentication_settings import AuthenticationSettings

# Basic HTTP proxy configuration
config = Configuration(
    server_api_url="https://api.orkes.io/api",
    authentication_settings=AuthenticationSettings(
        key_id="your_key_id",
        key_secret="your_key_secret"
    ),
    proxy="http://proxy.company.com:8080"
)
```

### HTTPS Proxy with Authentication Headers

```python
# HTTPS proxy with authentication headers
config = Configuration(
    server_api_url="https://api.orkes.io/api",
    authentication_settings=AuthenticationSettings(
        key_id="your_key_id",
        key_secret="your_key_secret"
    ),
    proxy="https://secure-proxy.company.com:8443",
    proxy_headers={
        "Proxy-Authorization": "Basic dXNlcm5hbWU6cGFzc3dvcmQ=",
        "X-Proxy-Client": "conductor-python-sdk"
    }
)
```

### SOCKS Proxy Configuration

```python
# SOCKS5 proxy configuration
config = Configuration(
    server_api_url="https://api.orkes.io/api",
    proxy="socks5://proxy.company.com:1080"
)

# SOCKS5 proxy with authentication
config = Configuration(
    server_api_url="https://api.orkes.io/api",
    proxy="socks5://username:password@proxy.company.com:1080"
)
```

## Environment Variable Configuration

You can configure proxy settings using Conductor-specific environment variables:

```shell
# Basic proxy configuration
export CONDUCTOR_PROXY=http://proxy.company.com:8080

# Proxy with authentication headers (JSON format)
export CONDUCTOR_PROXY_HEADERS='{"Proxy-Authorization": "Basic dXNlcm5hbWU6cGFzc3dvcmQ=", "X-Proxy-Client": "conductor-python-sdk"}'

# Or single header value
export CONDUCTOR_PROXY_HEADERS="Basic dXNlcm5hbWU6cGFzc3dvcmQ="
```

**Priority Order:**
1. Explicit proxy parameters in Configuration constructor
2. `CONDUCTOR_PROXY` and `CONDUCTOR_PROXY_HEADERS` environment variables

### Example Usage with Environment Variables

```python
# Set environment variables
import os
os.environ['CONDUCTOR_PROXY'] = 'http://proxy.company.com:8080'
os.environ['CONDUCTOR_PROXY_HEADERS'] = '{"Proxy-Authorization": "Basic dXNlcm5hbWU6cGFzc3dvcmQ="}'

# Configuration will automatically use proxy from environment
from conductor.client.configuration.configuration import Configuration
config = Configuration(server_api_url="https://api.orkes.io/api")
# Proxy is automatically configured from CONDUCTOR_PROXY environment variable
```

## Advanced Proxy Configuration

### Custom HTTP Client with Proxy

```python
import httpx
from conductor.client.configuration.configuration import Configuration

# Create custom HTTP client with proxy
custom_client = httpx.Client(
    proxies={
        "http://": "http://proxy.company.com:8080",
        "https://": "http://proxy.company.com:8080"
    },
    timeout=httpx.Timeout(120.0),
    follow_redirects=True,
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
)

config = Configuration(
    server_api_url="https://api.orkes.io/api",
    http_connection=custom_client
)
```

### Proxy with Custom Headers

```python
import httpx
from conductor.client.configuration.configuration import Configuration

# Create custom HTTP client with proxy and headers
custom_client = httpx.Client(
    proxies={
        "http://": "http://proxy.company.com:8080",
        "https://": "http://proxy.company.com:8080"
    },
    headers={
        "Proxy-Authorization": "Basic dXNlcm5hbWU6cGFzc3dvcmQ=",
        "X-Proxy-Client": "conductor-python-sdk",
        "User-Agent": "Conductor-Python-SDK/1.0"
    }
)

config = Configuration(
    server_api_url="https://api.orkes.io/api",
    http_connection=custom_client
)
```

### SOCKS Proxy with Authentication

```python
import httpx
from conductor.client.configuration.configuration import Configuration

# SOCKS5 proxy with authentication
custom_client = httpx.Client(
    proxies={
        "http://": "socks5://username:password@proxy.company.com:1080",
        "https://": "socks5://username:password@proxy.company.com:1080"
    }
)

config = Configuration(
    server_api_url="https://api.orkes.io/api",
    http_connection=custom_client
)
```

### Async Client Proxy Configuration

```python
import asyncio
import httpx
from conductor.asyncio_client.configuration import Configuration
from conductor.asyncio_client.adapters import ApiClient

async def main():
    # Create async HTTP client with proxy
    async_client = httpx.AsyncClient(
        proxies={
            "http://": "http://proxy.company.com:8080",
            "https://": "http://proxy.company.com:8080"
        }
    )
    
    config = Configuration(
        server_url="https://api.orkes.io/api",
        http_connection=async_client
    )
    
    async with ApiClient(config) as api_client:
        # Use the client with proxy configuration
        pass

asyncio.run(main())
```

## Troubleshooting

### Common Proxy Issues

1. **Connection refused**
   - Check if the proxy server is running
   - Verify the proxy URL and port
   - Check firewall settings

2. **Authentication failed**
   - Verify username and password
   - Check if the proxy requires specific authentication method
   - Ensure credentials are properly encoded

3. **SOCKS proxy not working**
   - Install httpx with SOCKS support: `pip install httpx[socks]`
   - Check if the SOCKS proxy server is accessible
   - Verify SOCKS version (4 or 5)

4. **SSL/TLS issues through proxy**
   - Some proxies don't support HTTPS properly
   - Try using HTTP proxy for HTTPS traffic
   - Check proxy server SSL configuration

### Debug Proxy Configuration

```python
import httpx
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Test proxy connection
def test_proxy_connection(proxy_url):
    try:
        with httpx.Client(proxies={"http://": proxy_url, "https://": proxy_url}) as client:
            response = client.get("http://httpbin.org/ip")
            print(f"Proxy test successful: {response.json()}")
    except Exception as e:
        print(f"Proxy test failed: {e}")

# Test your proxy
test_proxy_connection("http://proxy.company.com:8080")
```

### Proxy Environment Variables

```bash
# Set proxy environment variables for testing
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1

# Test with curl
curl -I https://api.orkes.io/api
```

### Proxy Authentication

```python
import base64
from urllib.parse import quote

# Create proxy authentication header
username = "your_username"
password = "your_password"
credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

proxy_headers = {
    "Proxy-Authorization": f"Basic {encoded_credentials}"
}

config = Configuration(
    server_api_url="https://api.orkes.io/api",
    proxy="http://proxy.company.com:8080",
    proxy_headers=proxy_headers
)
```
