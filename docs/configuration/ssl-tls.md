# SSL/TLS Configuration

The Conductor Python SDK supports comprehensive SSL/TLS configuration for both synchronous and asynchronous clients. This allows you to configure secure connections with custom certificates, client authentication, and various SSL verification options.

## Table of Contents

- [Synchronous Client SSL Configuration](#synchronous-client-ssl-configuration)
- [Asynchronous Client SSL Configuration](#asynchronous-client-ssl-configuration)
- [Environment Variable Configuration](#environment-variable-configuration)
- [Configuration Parameters](#configuration-parameters)
- [Example Files](#example-files)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting SSL Issues](#troubleshooting-ssl-issues)

## Synchronous Client SSL Configuration

### Basic SSL Configuration

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes_clients import OrkesClients

# Basic SSL configuration with custom CA certificate
config = Configuration(
    base_url="https://play.orkes.io",
    ssl_ca_cert="/path/to/ca-certificate.pem",
)

# Create clients with SSL configuration
clients = OrkesClients(configuration=config)
workflow_client = clients.get_workflow_client()
```

### SSL with Certificate Data

```python
# SSL with custom CA certificate data (PEM string)
config = Configuration(
    base_url="https://play.orkes.io",
    ca_cert_data="""-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKoK/Ovj8EUMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMTYwMjEyMTQ0NDQ2WhcNMjYwMjEwMTQ0NDQ2WjBF
-----END CERTIFICATE-----""",
)
```

### SSL with Client Certificate Authentication

```python
# SSL with client certificate authentication
config = Configuration(
    base_url="https://play.orkes.io",
    ssl_ca_cert="/path/to/ca-certificate.pem",
    cert_file="/path/to/client-certificate.pem",
    key_file="/path/to/client-key.pem",
)
```

### SSL with Disabled Verification (Not Recommended for Production)

```python
# SSL with completely disabled verification (NOT RECOMMENDED for production)
config = Configuration(
    base_url="https://play.orkes.io",
)
config.verify_ssl = False
```

### Advanced SSL Configuration with httpx

```python
import httpx
import ssl

# Create custom SSL context
ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations("/path/to/ca-certificate.pem")
ssl_context.load_cert_chain(
    certfile="/path/to/client-certificate.pem",
    keyfile="/path/to/client-key.pem"
)

# Create custom httpx client with SSL context
custom_client = httpx.Client(
    verify=ssl_context,
    timeout=httpx.Timeout(120.0),
    follow_redirects=True,
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
)

config = Configuration(base_url="https://play.orkes.io")
config.http_connection = custom_client
```

## Asynchronous Client SSL Configuration

### Basic Async SSL Configuration

```python
import asyncio
from conductor.asyncio_client.configuration import Configuration
from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients

# Basic SSL configuration with custom CA certificate
config = Configuration(
    server_url="https://play.orkes.io/api",
    ssl_ca_cert="/path/to/ca-certificate.pem",
)

async def main():
    async with ApiClient(config) as api_client:
        orkes_clients = OrkesClients(api_client, config)
        workflow_client = orkes_clients.get_workflow_client()

        # Use the client with SSL configuration
        workflows = await workflow_client.search_workflows()
        print(f"Found {len(workflows)} workflows")

asyncio.run(main())
```

### Async SSL with Certificate Data

```python
# SSL with custom CA certificate data (PEM string)
config = Configuration(
    server_url="https://play.orkes.io/api",
    ca_cert_data="""-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKoK/Ovj8EUMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMTYwMjEyMTQ0NDQ2WhcNMjYwMjEwMTQ0NDQ2WjBF
-----END CERTIFICATE-----""",
)
```

### Async SSL with Custom SSL Context

```python
import ssl

# Create custom SSL context
ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations("/path/to/ca-certificate.pem")
ssl_context.load_cert_chain(
    certfile="/path/to/client-certificate.pem",
    keyfile="/path/to/client-key.pem"
)
ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED

# Use with async client
config = Configuration(
    server_url="https://play.orkes.io/api",
    ssl_ca_cert="/path/to/ca-certificate.pem",
)
```

## Environment Variable Configuration

You can configure SSL settings using environment variables:

```bash
# Basic SSL configuration
export CONDUCTOR_SERVER_URL="https://play.orkes.io/api"
export CONDUCTOR_SSL_CA_CERT="/path/to/ca-certificate.pem"

# Client certificate authentication
export CONDUCTOR_CERT_FILE="/path/to/client-certificate.pem"
export CONDUCTOR_KEY_FILE="/path/to/client-key.pem"
```

```python
# Configuration will automatically pick up environment variables
from conductor.client.configuration.configuration import Configuration

config = Configuration()  # SSL settings loaded from environment
```

## Configuration Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ssl_ca_cert` | str | Path to CA certificate file |
| `ca_cert_data` | str/bytes | CA certificate data as PEM string or DER bytes |
| `cert_file` | str | Path to client certificate file |
| `key_file` | str | Path to client private key file |
| `verify_ssl` | bool | Enable/disable SSL verification (default: True) |
| `assert_hostname` | str | Custom hostname for SSL verification |

## Example Files

For complete working examples, see:
- [Sync SSL Example](../../examples/sync_ssl_example.py) - Comprehensive sync client SSL configuration
- [Async SSL Example](../../examples/async/async_ssl_example.py) - Comprehensive async client SSL configuration

## Security Best Practices

1. **Always use HTTPS in production** - Never use HTTP for production environments
2. **Verify SSL certificates** - Keep `verify_ssl=True` in production
3. **Use strong cipher suites** - Ensure your server supports modern TLS versions
4. **Rotate certificates regularly** - Implement certificate rotation policies
5. **Use certificate pinning** - For high-security environments, consider certificate pinning
6. **Monitor certificate expiration** - Set up alerts for certificate expiration
7. **Use proper key management** - Store private keys securely

## Troubleshooting SSL Issues

### Common SSL Issues

1. **Certificate verification failed**
   - Check if the CA certificate is correct
   - Verify the certificate chain is complete
   - Ensure the certificate hasn't expired

2. **Hostname verification failed**
   - Check if the hostname matches the certificate
   - Use `assert_hostname` parameter if needed

3. **Connection timeout**
   - Check network connectivity
   - Verify firewall settings
   - Check if the server is accessible

### Debug SSL Connections

```python
import ssl
import logging

# Enable SSL debugging
logging.basicConfig(level=logging.DEBUG)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False  # Only for debugging
ssl_context.verify_mode = ssl.CERT_NONE  # Only for debugging

# Use with configuration
config = Configuration(
    base_url="https://your-server.com",
    ssl_ca_cert="/path/to/ca-cert.pem"
)
```

### Testing SSL Configuration

```python
import ssl
import socket

def test_ssl_connection(hostname, port, ca_cert_path):
    context = ssl.create_default_context()
    context.load_verify_locations(ca_cert_path)

    with socket.create_connection((hostname, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            print(f"SSL connection successful: {ssock.version()}")
            print(f"Certificate: {ssock.getpeercert()}")

# Test your SSL configuration
test_ssl_connection("your-server.com", 443, "/path/to/ca-cert.pem")
```
