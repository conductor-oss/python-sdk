# Secret Management API Reference

Complete API reference for secret management operations in Conductor Python SDK.

> 📚 **Security Note**: Secrets are encrypted at rest and in transit. Use appropriate access controls and never commit secret values to version control.

## Quick Start

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.orkes.orkes_secret_client import OrkesSecretClient
from conductor.client.orkes.models.metadata_tag import MetadataTag

# Initialize client
configuration = Configuration(
    server_api_url="http://localhost:8080/api",
    debug=False,
    authentication_settings=AuthenticationSettings(
        key_id="your_key_id",
        key_secret="your_key_secret"
    )
)

secret_client = OrkesSecretClient(configuration)

# Store a secret
secret_client.put_secret("API_KEY", "sk-1234567890abcdef")

# Retrieve a secret
api_key = secret_client.get_secret("API_KEY")

# Tag secrets for organization
tags = [
    MetadataTag("environment", "production"),
    MetadataTag("service", "payment-gateway")
]
secret_client.set_secret_tags(tags, "API_KEY")

# List all available secrets
secret_names = secret_client.list_all_secret_names()
print(f"Available secrets: {secret_names}")
```

## Quick Links

- [Secret Management APIs](#secret-management-apis)
- [Secret Access APIs](#secret-access-apis)
- [Secret Tag APIs](#secret-tag-apis)
- [API Details](#api-details)
- [Model Reference](#model-reference)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

## Secret Management APIs

Core CRUD operations for managing secrets.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `put_secret()` | `PUT /secrets/{key}` | Store or update a secret | [Example](#store-secret) |
| `get_secret()` | `GET /secrets/{key}` | Retrieve a secret value | [Example](#get-secret) |
| `delete_secret()` | `DELETE /secrets/{key}` | Delete a secret | [Example](#delete-secret) |
| `secret_exists()` | `GET /secrets/{key}/exists` | Check if secret exists | [Example](#check-secret-exists) |

## Secret Access APIs

Operations for managing secret access and permissions.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `list_all_secret_names()` | `GET /secrets` | List all secret names | [Example](#list-secrets) |
| `list_secrets_that_user_can_grant_access_to()` | `GET /secrets/grantable` | List secrets user can grant | [Example](#list-grantable-secrets) |

## Secret Tag APIs

Tag management for secret organization and discovery.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `set_secret_tags()` | `PUT /secrets/{key}/tags` | Set/overwrite tags | [Example](#set-tags) |
| `get_secret_tags()` | `GET /secrets/{key}/tags` | Get all tags for secret | [Example](#get-tags) |
| `delete_secret_tags()` | `DELETE /secrets/{key}/tags` | Delete specific tags | [Example](#delete-tags) |

---

## API Details

### Secret Management

#### Store Secret

Store or update a secret value.

```python
# Store API credentials
secret_client.put_secret("OPENAI_API_KEY", "sk-proj-abc123...")

# Store database password
secret_client.put_secret("DB_PASSWORD", "super_secure_password_123")

# Store JSON configuration as secret
import json
config = {
    "host": "db.example.com",
    "port": 5432,
    "ssl": True
}
secret_client.put_secret("DB_CONFIG", json.dumps(config))

# Update existing secret
secret_client.put_secret("API_KEY", "new-api-key-value")
```

**Parameters:**
- `key` (str, required): Unique secret identifier
- `value` (str, required): Secret value to store

**Notes:**
- Secret names must be unique
- Values are encrypted before storage
- Updating a secret overwrites the previous value
- No versioning is maintained (consider using different keys for versions)

#### Get Secret

Retrieve a secret value by key.

```python
# Get simple secret
api_key = secret_client.get_secret("OPENAI_API_KEY")
print(f"API Key: {api_key[:10]}...")  # Only show first 10 chars

# Get and parse JSON secret
import json
db_config_str = secret_client.get_secret("DB_CONFIG")
db_config = json.loads(db_config_str)
print(f"Database host: {db_config['host']}")

# Handle missing secrets
try:
    secret_value = secret_client.get_secret("NON_EXISTENT")
except Exception as e:
    print(f"Secret not found: {e}")
    # Use default value
    secret_value = "default_value"
```

**Parameters:**
- `key` (str, required): Secret identifier

**Returns:** String value of the secret

**Raises:** Exception if secret doesn't exist or access denied

#### Delete Secret

Permanently delete a secret.

```python
# Delete a single secret
secret_client.delete_secret("OLD_API_KEY")
print("Secret deleted successfully")

# Clean up test secrets
test_secrets = ["TEST_SECRET_1", "TEST_SECRET_2", "TEST_SECRET_3"]
for secret_name in test_secrets:
    try:
        secret_client.delete_secret(secret_name)
        print(f"Deleted: {secret_name}")
    except Exception:
        print(f"Secret {secret_name} not found or already deleted")
```

**Parameters:**
- `key` (str, required): Secret identifier to delete

**Notes:**
- Deletion is permanent and cannot be undone
- Deleting a non-existent secret may raise an exception

#### Check Secret Exists

Check if a secret exists without retrieving its value.

```python
# Check before accessing
if secret_client.secret_exists("API_KEY"):
    api_key = secret_client.get_secret("API_KEY")
    print("API key loaded")
else:
    print("API key not configured")

# Validate required secrets on startup
required_secrets = ["DB_PASSWORD", "API_KEY", "JWT_SECRET"]
missing_secrets = []

for secret_name in required_secrets:
    if not secret_client.secret_exists(secret_name):
        missing_secrets.append(secret_name)

if missing_secrets:
    print(f"Missing required secrets: {missing_secrets}")
    # Exit or use defaults
```

**Parameters:**
- `key` (str, required): Secret identifier

**Returns:** Boolean indicating existence

---

### Secret Access Management

#### List Secrets

List all secret names accessible to the current user.

```python
# Get all secret names
secret_names = secret_client.list_all_secret_names()

print(f"Total secrets: {len(secret_names)}")
for name in sorted(secret_names):
    print(f"  - {name}")

# Filter secrets by prefix
api_secrets = [s for s in secret_names if s.startswith("API_")]
db_secrets = [s for s in secret_names if s.startswith("DB_")]

print(f"API secrets: {api_secrets}")
print(f"Database secrets: {db_secrets}")

# Check for missing secrets
expected_secrets = {"API_KEY", "DB_PASSWORD", "JWT_SECRET"}
existing_secrets = secret_client.list_all_secret_names()
missing = expected_secrets - existing_secrets

if missing:
    print(f"Missing secrets: {missing}")
```

**Returns:** Set of secret name strings

#### List Grantable Secrets

List secrets that the current user can grant access to others.

```python
# Get secrets user can share
grantable = secret_client.list_secrets_that_user_can_grant_access_to()

print("Secrets you can grant access to:")
for secret_name in grantable:
    print(f"  - {secret_name}")

# Useful for admin tools
if "PRODUCTION_API_KEY" in grantable:
    print("You have admin access to production secrets")
    # Show grant UI or options
```

**Returns:** List of secret name strings

---

### Secret Tagging

#### Set Tags

Set or overwrite all tags on a secret.

```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

# Tag by environment
tags = [
    MetadataTag("environment", "production"),
    MetadataTag("region", "us-east-1")
]
secret_client.set_secret_tags(tags, "PROD_API_KEY")

# Tag by service
service_tags = [
    MetadataTag("service", "payment-gateway"),
    MetadataTag("team", "platform"),
    MetadataTag("criticality", "high")
]
secret_client.set_secret_tags(service_tags, "PAYMENT_SECRET")

# Tag with metadata
metadata_tags = [
    MetadataTag("created_by", "admin"),
    MetadataTag("created_date", "2024-01-15"),
    MetadataTag("expires", "2025-01-15"),
    MetadataTag("rotation_required", "true")
]
secret_client.set_secret_tags(metadata_tags, "TEMP_API_KEY")
```

**Parameters:**
- `tags` (List[MetadataTag], required): List of tags to set
- `key` (str, required): Secret identifier

**Note:** This overwrites all existing tags

#### Get Tags

Retrieve all tags for a secret.

```python
# Get tags for a secret
tags = secret_client.get_secret_tags("PROD_API_KEY")

for tag in tags:
    print(f"{tag.key}: {tag.value}")

# Check specific tag
tags = secret_client.get_secret_tags("API_KEY")
env_tag = next((t for t in tags if t.key == "environment"), None)

if env_tag and env_tag.value == "production":
    print("This is a production secret - handle with care!")

# Find secrets by tag (manual filtering)
all_secrets = secret_client.list_all_secret_names()
production_secrets = []

for secret_name in all_secrets:
    tags = secret_client.get_secret_tags(secret_name)
    if any(t.key == "environment" and t.value == "production" for t in tags):
        production_secrets.append(secret_name)

print(f"Production secrets: {production_secrets}")
```

**Parameters:**
- `key` (str, required): Secret identifier

**Returns:** List of MetadataTag objects

#### Delete Tags

Delete specific tags from a secret.

```python
# Remove specific tags
tags_to_remove = [
    MetadataTag("expires", "2025-01-15"),
    MetadataTag("rotation_required", "true")
]
secret_client.delete_secret_tags(tags_to_remove, "TEMP_API_KEY")

# Remove all temporary tags
temp_tags = [
    MetadataTag("temp", "true"),
    MetadataTag("test", "true")
]
secret_client.delete_secret_tags(temp_tags, "TEST_SECRET")

# Clean up deprecated tags
deprecated_tag = [MetadataTag("deprecated", "true")]
for secret_name in secret_client.list_all_secret_names():
    try:
        secret_client.delete_secret_tags(deprecated_tag, secret_name)
    except Exception:
        pass  # Tag might not exist on this secret
```

**Parameters:**
- `tags` (List[MetadataTag], required): Tags to delete
- `key` (str, required): Secret identifier

---

## Model Reference

### MetadataTag

Tag object for secret organization.

```python
class MetadataTag:
    key: str    # Tag key/name
    value: str  # Tag value

    def __init__(self, key: str, value: str)
```

### Usage in Workflows

Secrets can be referenced in workflow definitions:

```json
{
  "name": "secure_workflow",
  "tasks": [
    {
      "name": "api_call",
      "taskReferenceName": "call_external_api",
      "type": "HTTP",
      "inputParameters": {
        "http_request": {
          "uri": "https://api.example.com/data",
          "method": "GET",
          "headers": {
            "Authorization": "Bearer ${workflow.secrets.API_KEY}"
          }
        }
      }
    }
  ]
}
```

---

## Error Handling

### Common Errors

```python
# Handle missing secrets
def get_secret_safely(client, key, default=None):
    try:
        return client.get_secret(key)
    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            print(f"Secret {key} not found, using default")
            return default
        raise  # Re-raise other errors

# Handle permission errors
try:
    secret_client.put_secret("RESTRICTED_SECRET", "value")
except Exception as e:
    if "403" in str(e) or "forbidden" in str(e).lower():
        print("Permission denied - contact admin")
    else:
        print(f"Error storing secret: {e}")

# Validate secrets on startup
def validate_required_secrets(client, required_keys):
    errors = []
    for key in required_keys:
        if not client.secret_exists(key):
            errors.append(f"Missing required secret: {key}")

    if errors:
        raise ValueError("\n".join(errors))

# Use with:
validate_required_secrets(secret_client, ["API_KEY", "DB_PASSWORD"])
```

### Retry Logic

```python
import time
from typing import Optional

def get_secret_with_retry(
    client,
    key: str,
    max_retries: int = 3,
    delay: float = 1.0
) -> Optional[str]:
    """Get secret with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return client.get_secret(key)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = delay * (2 ** attempt)
            print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s")
            time.sleep(wait_time)
    return None
```

---

## Best Practices

### 1. Secret Naming Conventions

```python
# ✅ Good: Clear, hierarchical naming
secret_client.put_secret("PROD_DB_PASSWORD", "...")
secret_client.put_secret("STAGING_API_KEY_STRIPE", "...")
secret_client.put_secret("DEV_JWT_SECRET", "...")

# ❌ Bad: Ambiguous or unclear names
secret_client.put_secret("password", "...")
secret_client.put_secret("key1", "...")
secret_client.put_secret("secret", "...")
```

### 2. Secret Rotation

```python
import time
from datetime import datetime, timedelta

def rotate_secret(client, key: str, new_value: str):
    """Rotate a secret with backup"""
    # Backup old secret
    try:
        old_value = client.get_secret(key)
        backup_key = f"{key}_BACKUP_{int(time.time())}"
        client.put_secret(backup_key, old_value)

        # Tag the backup
        tags = [
            MetadataTag("type", "backup"),
            MetadataTag("original_key", key),
            MetadataTag("backed_up_at", datetime.now().isoformat())
        ]
        client.set_secret_tags(tags, backup_key)
    except Exception:
        pass  # First time setting secret

    # Set new secret
    client.put_secret(key, new_value)

    # Tag with rotation info
    tags = [
        MetadataTag("last_rotated", datetime.now().isoformat()),
        MetadataTag("next_rotation", (datetime.now() + timedelta(days=90)).isoformat())
    ]
    client.set_secret_tags(tags, key)
```

### 3. Environment-Specific Secrets

```python
import os

class EnvironmentSecrets:
    """Manage environment-specific secrets"""

    def __init__(self, client, environment: str = None):
        self.client = client
        self.env = environment or os.getenv("ENVIRONMENT", "dev")
        self.prefix = self.env.upper()

    def get(self, key: str) -> str:
        """Get environment-specific secret"""
        env_key = f"{self.prefix}_{key}"
        return self.client.get_secret(env_key)

    def put(self, key: str, value: str):
        """Store environment-specific secret"""
        env_key = f"{self.prefix}_{key}"
        self.client.put_secret(env_key, value)

        # Tag with environment
        tags = [
            MetadataTag("environment", self.env),
            MetadataTag("base_key", key)
        ]
        self.client.set_secret_tags(tags, env_key)

# Usage
env_secrets = EnvironmentSecrets(secret_client, "production")
db_password = env_secrets.get("DB_PASSWORD")  # Gets PRODUCTION_DB_PASSWORD
```

### 4. Secret Validation

```python
def validate_api_key(key: str) -> bool:
    """Validate API key format"""
    if not key:
        return False
    if not key.startswith("sk-"):
        return False
    if len(key) < 20:
        return False
    return True

# Store with validation
def store_validated_secret(client, key: str, value: str):
    # Validate based on key type
    if "API_KEY" in key and not validate_api_key(value):
        raise ValueError(f"Invalid API key format for {key}")

    if "PASSWORD" in key and len(value) < 8:
        raise ValueError(f"Password too short for {key}")

    client.put_secret(key, value)
```

### 5. Audit and Compliance

```python
from datetime import datetime

def audit_secret_access(client, key: str, action: str, user: str):
    """Log secret access for audit purposes"""
    audit_key = f"AUDIT_{key}_{int(time.time())}"
    audit_data = {
        "key": key,
        "action": action,
        "user": user,
        "timestamp": datetime.now().isoformat()
    }

    # Store audit log as secret (in production, use proper audit system)
    client.put_secret(audit_key, json.dumps(audit_data))

    # Tag for easy filtering
    tags = [
        MetadataTag("type", "audit"),
        MetadataTag("secret_key", key),
        MetadataTag("action", action)
    ]
    client.set_secret_tags(tags, audit_key)

# Usage with audit
def get_secret_with_audit(client, key: str, user: str):
    audit_secret_access(client, key, "read", user)
    return client.get_secret(key)
```

---

## Integration Examples

### Database Configuration

```python
import json
import psycopg2

def get_db_connection(secret_client):
    """Get database connection using secrets"""
    # Get database configuration from secrets
    db_config = json.loads(secret_client.get_secret("DB_CONFIG"))
    db_password = secret_client.get_secret("DB_PASSWORD")

    # Create connection
    conn = psycopg2.connect(
        host=db_config["host"],
        port=db_config["port"],
        database=db_config["database"],
        user=db_config["user"],
        password=db_password,
        sslmode="require" if db_config.get("ssl") else "prefer"
    )

    return conn
```

### API Client Configuration

```python
import httpx

class SecureAPIClient:
    """API client with secret management"""

    def __init__(self, secret_client, service_name: str):
        self.secret_client = secret_client
        self.service_name = service_name
        self._client = None

    def _get_client(self):
        if not self._client:
            # Get API credentials from secrets
            api_key = self.secret_client.get_secret(f"{self.service_name}_API_KEY")
            api_url = self.secret_client.get_secret(f"{self.service_name}_URL")

            self._client = httpx.Client(
                base_url=api_url,
                headers={"Authorization": f"Bearer {api_key}"}
            )

        return self._client

    def request(self, method: str, endpoint: str, **kwargs):
        client = self._get_client()
        return client.request(method, endpoint, **kwargs)

# Usage
api_client = SecureAPIClient(secret_client, "OPENAI")
response = api_client.request("POST", "/completions", json={...})
```

---

## Complete Working Example

```python
"""
Secret Management Example
========================

Demonstrates comprehensive secret management including:
- CRUD operations
- Tagging and organization
- Environment-specific secrets
- Rotation and backup
- Error handling
"""

from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.orkes.orkes_secret_client import OrkesSecretClient
from conductor.client.orkes.models.metadata_tag import MetadataTag
import json
import time
from datetime import datetime

def main():
    # Initialize client
    config = Configuration(
        server_api_url="http://localhost:8080/api",
        authentication_settings=AuthenticationSettings(
            key_id="your_key",
            key_secret="your_secret"
        )
    )

    secret_client = OrkesSecretClient(config)

    # 1. Store various types of secrets
    print("Storing secrets...")

    # API keys
    secret_client.put_secret("OPENAI_API_KEY", "sk-proj-abc123...")
    secret_client.put_secret("STRIPE_API_KEY", "sk_live_xyz789...")

    # Database credentials
    db_config = {
        "host": "db.example.com",
        "port": 5432,
        "database": "myapp",
        "user": "dbuser",
        "ssl": True
    }
    secret_client.put_secret("DB_CONFIG", json.dumps(db_config))
    secret_client.put_secret("DB_PASSWORD", "super_secure_pass_123")

    # 2. Tag secrets for organization
    print("\nTagging secrets...")

    # Tag API keys
    api_tags = [
        MetadataTag("type", "api_key"),
        MetadataTag("environment", "production"),
        MetadataTag("service", "openai")
    ]
    secret_client.set_secret_tags(api_tags, "OPENAI_API_KEY")

    # Tag database secrets
    db_tags = [
        MetadataTag("type", "database"),
        MetadataTag("environment", "production"),
        MetadataTag("region", "us-east-1")
    ]
    secret_client.set_secret_tags(db_tags, "DB_CONFIG")
    secret_client.set_secret_tags(db_tags, "DB_PASSWORD")

    # 3. List and filter secrets
    print("\nListing secrets...")
    all_secrets = secret_client.list_all_secret_names()
    print(f"Total secrets: {len(all_secrets)}")

    # Filter by prefix
    api_secrets = [s for s in all_secrets if "API" in s]
    db_secrets = [s for s in all_secrets if "DB" in s]

    print(f"API secrets: {api_secrets}")
    print(f"Database secrets: {db_secrets}")

    # 4. Retrieve and use secrets
    print("\nUsing secrets...")

    # Get API key
    api_key = secret_client.get_secret("OPENAI_API_KEY")
    print(f"API Key (first 10 chars): {api_key[:10]}...")

    # Get database config
    db_config_str = secret_client.get_secret("DB_CONFIG")
    db_config = json.loads(db_config_str)
    print(f"Database host: {db_config['host']}")

    # 5. Check secret existence
    print("\nChecking secrets...")
    required_secrets = ["OPENAI_API_KEY", "DB_PASSWORD", "JWT_SECRET"]

    for secret_name in required_secrets:
        exists = secret_client.secret_exists(secret_name)
        status = "✓" if exists else "✗"
        print(f"{status} {secret_name}")

    # 6. Update tags
    print("\nUpdating tags...")

    # Get current tags
    current_tags = secret_client.get_secret_tags("OPENAI_API_KEY")
    print(f"Current tags: {[(t.key, t.value) for t in current_tags]}")

    # Add rotation info
    new_tags = current_tags + [
        MetadataTag("last_rotated", datetime.now().isoformat()),
        MetadataTag("rotate_after", "90_days")
    ]
    secret_client.set_secret_tags(new_tags, "OPENAI_API_KEY")

    # 7. Clean up specific tags
    print("\nCleaning up tags...")
    tags_to_remove = [MetadataTag("rotate_after", "90_days")]
    secret_client.delete_secret_tags(tags_to_remove, "OPENAI_API_KEY")

    # 8. List grantable secrets
    print("\nChecking grantable secrets...")
    grantable = secret_client.list_secrets_that_user_can_grant_access_to()
    print(f"Can grant access to: {grantable}")

    # 9. Clean up (optional)
    if input("\nDelete test secrets? (y/n): ").lower() == 'y':
        for secret_name in ["OPENAI_API_KEY", "STRIPE_API_KEY", "DB_CONFIG", "DB_PASSWORD"]:
            try:
                secret_client.delete_secret(secret_name)
                print(f"Deleted: {secret_name}")
            except Exception as e:
                print(f"Could not delete {secret_name}: {e}")

if __name__ == "__main__":
    main()
```

---

## See Also

- [Workflow Management](./WORKFLOW.md) - Using secrets in workflows
- [Authorization](./AUTHORIZATION.md) - Managing secret access permissions
- [Task Management](./TASK_MANAGEMENT.md) - Using secrets in task execution
- [Examples](../examples/) - Complete working examples