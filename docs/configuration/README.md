# Configuration

This section covers various configuration options for the Conductor Python SDK.

## Table of Contents

- [Basic Configuration](../../README.md#configuration) - Basic configuration setup
- [SSL/TLS Configuration](ssl-tls.md) - Secure connections and certificates
- [Proxy Configuration](proxy.md) - Network proxy setup

## Overview

The Conductor Python SDK provides flexible configuration options to work with different environments and security requirements. Configuration can be done through:

1. **Code Configuration** - Direct configuration in your application code
2. **Environment Variables** - Configuration through environment variables
3. **Configuration Files** - External configuration files (future enhancement)

## Quick Start

```python
from conductor.client.configuration.configuration import Configuration

# Basic configuration
config = Configuration()

# Custom server URL
config = Configuration(server_api_url="https://your-server.com/api")

# With authentication
from conductor.shared.configuration.settings.authentication_settings import AuthenticationSettings
config = Configuration(
    server_api_url="https://your-server.com/api",
    authentication_settings=AuthenticationSettings(
        key_id="your_key",
        key_secret="your_secret"
    )
)
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CONDUCTOR_SERVER_URL` | Conductor server API URL | `http://localhost:8080/api` |
| `CONDUCTOR_AUTH_KEY` | Authentication key | None |
| `CONDUCTOR_AUTH_SECRET` | Authentication secret | None |
| `CONDUCTOR_PROXY` | Proxy URL | None |
| `CONDUCTOR_PROXY_HEADERS` | Proxy headers (JSON) | None |
| `CONDUCTOR_SSL_CA_CERT` | CA certificate path | None |
| `CONDUCTOR_CERT_FILE` | Client certificate path | None |
| `CONDUCTOR_KEY_FILE` | Client private key path | None |

## Configuration Examples

### Local Development

```python
config = Configuration()  # Uses http://localhost:8080/api
```

### Production with Authentication

```python
config = Configuration(
    server_api_url="https://your-cluster.orkesconductor.io/api",
    authentication_settings=AuthenticationSettings(
        key_id="your_key",
        key_secret="your_secret"
    )
)
```

### With Proxy

```python
config = Configuration(
    server_api_url="https://your-server.com/api",
    proxy="http://proxy.company.com:8080"
)
```

### With SSL/TLS

```python
config = Configuration(
    server_api_url="https://your-server.com/api",
    ssl_ca_cert="/path/to/ca-cert.pem",
    cert_file="/path/to/client-cert.pem",
    key_file="/path/to/client-key.pem"
)
```

## Advanced Configuration

For more detailed configuration options, see:

- [SSL/TLS Configuration](ssl-tls.md) - Complete SSL/TLS setup guide
- [Proxy Configuration](proxy.md) - Network proxy configuration guide
