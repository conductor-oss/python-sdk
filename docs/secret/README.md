# Secret Management

## Secret Client

### Initialization

```python
from conductor.client.configuration.configuration import Configuration
from conductor.shared.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.orkes.orkes_secret_client import OrkesSecretClient

configuration = Configuration(
    server_api_url=SERVER_API_URL,
    debug=False,
    authentication_settings=AuthenticationSettings(key_id=KEY_ID, key_secret=KEY_SECRET)
)

secret_client = OrkesSecretClient(configuration)
```

### Saving Secret

```python
secret_client.put_secret("SECRET_NAME", "SECRET_VALUE")
```

### Get Secret

#### Get a specific secret value

```python
value = secret_client.get_secret("SECRET_NAME")
```

#### List all secret names

```python
secret_names = secret_client.list_all_secret_names()
```

#### List all secret names that user can grant access to

```python
secret_names = secret_client.list_secrets_that_user_can_grant_access_to()
```

### Delete Secret

```python
secret_client.delete_secret("SECRET_NAME")
```

### Secret Tag Management

#### Set secret tags

```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

tags = [
    MetadataTag("sec_tag", "val"), MetadataTag("sec_tag_2", "val2")
]
secret_client.set_secret_tags(tags, "SECRET_NAME")
```

#### Get secret tags

```python
tags = secret_client.get_secret_tags("SECRET_NAME")
```

#### Delete secret tags

```python
tags = [
    MetadataTag("sec_tag", "val"), MetadataTag("sec_tag_2", "val2")
]
secret_client.delete_secret_tags(tags, "SECRET_NAME")
```
