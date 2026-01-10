# Integration API Reference

This document provides a comprehensive reference for all Integration APIs available in the Conductor Python SDK, focusing on AI/LLM integrations, Vector DBs, Kafka, and other external systems.

> 📚 **Complete Working Example**: See [prompt_journey.py](../../examples/prompt_journey.py) for integration with prompts.

## Quick Start

```python
from conductor.client.orkes.orkes_integration_client import OrkesIntegrationClient
from conductor.client.orkes.orkes_prompt_client import OrkesPromptClient
from conductor.client.http.models.integration_update import IntegrationUpdate
from conductor.client.http.models.integration_api_update import IntegrationApiUpdate

# 1. Create Integration (if not exists)
integration = IntegrationUpdate(
    type='openai',
    category='AI_MODEL',
    description='OpenAI models',
    enabled=True,
    configuration={
        'api_key': 'sk-your-key',  # ✅ Use 'api_key' not 'apiKey'
        'endpoint': 'https://api.openai.com/v1'
    }
)
integration_client.save_integration('openai', integration)

# 2. Add Models (ALWAYS do this, even if integration exists)
model = IntegrationApiUpdate(
    description='GPT-4 Optimized',
    enabled=True,
    max_tokens=128000
    # NO 'model' in configuration - it's the API name parameter!
)
integration_client.save_integration_api('openai', 'gpt-4o', model)
#                                                  ^^^^^^^^
#                                                  Model name here, NOT in config!

# 3. Create Prompt with Models
prompt_client.save_prompt(
    prompt_name='greeting',
    description='Greeting prompt',
    prompt_template='Hello ${name}!',
    models=['gpt-4o', 'gpt-4']  # ✅ Just model names, NO 'openai:' prefix
)

# 4. Test Prompt
result = prompt_client.test_prompt(
    prompt_text='Hello ${name}!',
    variables={'name': 'World'},
    ai_integration='openai',      # ✅ Integration name
    text_complete_model='gpt-4o'  # ✅ Just model name, NO prefix
)
```

## Table of Contents
- [Integrations](#integrations)
- [Integration APIs](#integration-apis)
- [Tags](#tags)
- [Prompt Associations](#prompt-associations)
- [Token Usage](#token-usage)
- [Available APIs](#available-apis)
- [Provider Definitions](#provider-definitions)

---

## Integrations

Manage integration providers (e.g., OpenAI, Pinecone, Kafka clusters).

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `save_integration()` | `PUT /api/integrations/{name}` | Create or update an integration | [Example](#save-integration) |
| `get_integration()` | `GET /api/integrations/{name}` | Get integration by name | [Example](#get-integration) |
| `get_integrations()` | `GET /api/integrations` | List all integrations | [Example](#get-integrations) |
| `delete_integration()` | `DELETE /api/integrations/{name}` | Delete an integration | [Example](#delete-integration) |

### Save Integration

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_integration_client import OrkesIntegrationClient
from conductor.client.http.models.integration_update import IntegrationUpdate

configuration = Configuration()
integration_client = OrkesIntegrationClient(configuration)

# Create OpenAI integration
integration = IntegrationUpdate(
    type='openai',
    category='AI_MODEL',
    description='OpenAI GPT models',
    enabled=True,
    configuration={
        'api_key': 'sk-your-key',  # Use 'api_key' not 'apiKey'
        'endpoint': 'https://api.openai.com/v1'
    }
)

integration_client.save_integration('openai', integration)
print("✅ Integration created")
```

### Get Integration

```python
# Get integration by name
integration = integration_client.get_integration('openai')
if integration:
    print(f"Integration: {integration.name}")
    print(f"Type: {integration.type}")
    print(f"Enabled: {integration.enabled}")
```

### Get Integrations

```python
# List all integrations
integrations = integration_client.get_integrations()
for integration in integrations:
    print(f"Integration: {integration.name} ({integration.type})")
```

### Delete Integration

```python
# Delete integration
integration_client.delete_integration('openai')
print("✅ Integration deleted")
```

---

## Integration APIs

Manage APIs/models within integrations (e.g., specific models for AI integrations).

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `save_integration_api()` | `PUT /api/integrations/{integration}/apis/{api}` | Add/update model or API | [Example](#save-integration-api) |
| `get_integration_api()` | `GET /api/integrations/{integration}/apis/{api}` | Get specific API/model | [Example](#get-integration-api) |
| `get_integration_apis()` | `GET /api/integrations/{integration}/apis` | List all APIs/models | [Example](#get-integration-apis) |
| `delete_integration_api()` | `DELETE /api/integrations/{integration}/apis/{api}` | Delete API/model | [Example](#delete-integration-api) |

### Save Integration API

```python
from conductor.client.http.models.integration_api_update import IntegrationApiUpdate

# Add GPT-4 model to OpenAI integration
model = IntegrationApiUpdate(
    description='GPT-4 Optimized',
    enabled=True,
    max_tokens=128000
    # Model name goes in the API parameter, NOT in configuration
)

integration_client.save_integration_api('openai', 'gpt-4o', model)
print("✅ Model added")
```

### Get Integration API

```python
# Get specific model
model = integration_client.get_integration_api('gpt-4o', 'openai')
if model:
    print(f"Model: {model.name}")
    print(f"Enabled: {model.enabled}")
```

### Get Integration APIs

```python
# List all models for an integration
models = integration_client.get_integration_apis('openai')
for model in models:
    print(f"Model: {model.name} - {model.description}")
```

### Delete Integration API

```python
# Delete a model
integration_client.delete_integration_api('gpt-3.5-turbo', 'openai')
print("✅ Model deleted")
```

---

## Tags

Manage tags for integrations and models for organization and tracking.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `put_tag_for_integration_provider()` | `PUT /api/integrations/{name}/tags` | Add tags to integration | [Example](#put-tag-for-integration-provider) |
| `get_tags_for_integration_provider()` | `GET /api/integrations/{name}/tags` | Get integration tags | [Example](#get-tags-for-integration-provider) |
| `delete_tag_for_integration_provider()` | `DELETE /api/integrations/{name}/tags` | Delete integration tags | [Example](#delete-tag-for-integration-provider) |
| `put_tag_for_integration()` | `PUT /api/integrations/{integration}/apis/{api}/tags` | Add tags to model | [Example](#put-tag-for-integration) |
| `get_tags_for_integration()` | `GET /api/integrations/{integration}/apis/{api}/tags` | Get model tags | [Example](#get-tags-for-integration) |
| `delete_tag_for_integration()` | `DELETE /api/integrations/{integration}/apis/{api}/tags` | Delete model tags | [Example](#delete-tag-for-integration) |

### Put Tag For Integration Provider

```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

# Tag the integration provider
tags = [
    MetadataTag("environment", "production"),
    MetadataTag("team", "ai_platform"),
    MetadataTag("cost_center", "engineering")
]

integration_client.put_tag_for_integration_provider(tags, 'openai')
print("✅ Integration tagged")
```

### Get Tags For Integration Provider

```python
# Get integration tags
tags = integration_client.get_tags_for_integration_provider('openai')
for tag in tags:
    print(f"Tag: {tag.key} = {tag.value}")
```

### Delete Tag For Integration Provider

```python
# Delete specific tags
tags_to_delete = [
    MetadataTag("environment", "production")
]
integration_client.delete_tag_for_integration_provider(tags_to_delete, 'openai')
print("✅ Tags deleted")
```

### Put Tag For Integration

```python
# Tag a specific model
model_tags = [
    MetadataTag("model_type", "optimized"),
    MetadataTag("context_window", "128k"),
    MetadataTag("cost_tier", "premium")
]

integration_client.put_tag_for_integration(model_tags, 'gpt-4o', 'openai')
print("✅ Model tagged")
```

### Get Tags For Integration

```python
# Get model tags
tags = integration_client.get_tags_for_integration('gpt-4o', 'openai')
for tag in tags:
    print(f"Tag: {tag.key} = {tag.value}")
```

### Delete Tag For Integration

```python
# Delete model tags
tags_to_delete = [
    MetadataTag("cost_tier", "premium")
]
# Note: Parameter order is (tags, model_name, integration_name)
integration_client.delete_tag_for_integration(tags_to_delete, 'gpt-4o', 'openai')
print("✅ Model tags deleted")
```

---

## Prompt Associations

Associate prompts with specific models for optimization.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `associate_prompt_with_integration()` | `POST /api/integrations/{integration}/models/{model}/prompts/{prompt}` | Associate prompt with model | [Example](#associate-prompt-with-integration) |
| `get_prompts_with_integration()` | `GET /api/integrations/{integration}/models/{model}/prompts` | Get prompts for model | [Example](#get-prompts-with-integration) |

### Associate Prompt With Integration

```python
# Associate a prompt with a specific model
integration_client.associate_prompt_with_integration(
    ai_integration='openai',
    model_name='gpt-4o',
    prompt_name='customer_greeting'
)
print("✅ Prompt associated with model")
```

### Get Prompts With Integration

```python
# Get all prompts associated with a model
prompts = integration_client.get_prompts_with_integration('openai', 'gpt-4o')
for prompt in prompts:
    print(f"Prompt: {prompt.name} - {prompt.description}")
```

---

## Token Usage

Track token usage for cost monitoring and optimization.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `get_token_usage_for_integration_provider()` | `GET /api/integrations/{name}/usage` | Get provider usage | [Example](#get-token-usage-for-integration-provider) |
| `get_token_usage_for_integration()` | `GET /api/integrations/{integration}/apis/{api}/usage` | Get model usage | [Example](#get-token-usage-for-integration) |

### Get Token Usage For Integration Provider

```python
# Get total token usage for integration
usage = integration_client.get_token_usage_for_integration_provider('openai')
if usage:
    print(f"Total tokens: {usage.get('total_tokens', 0):,}")
    print(f"Input tokens: {usage.get('input_tokens', 0):,}")
    print(f"Output tokens: {usage.get('output_tokens', 0):,}")
```

### Get Token Usage For Integration

```python
# Get token usage for specific model
usage = integration_client.get_token_usage_for_integration('gpt-4o', 'openai')
if usage:
    print(f"Model gpt-4o used: {usage:,} tokens")
```

---

## Available APIs

Get available APIs and configurations for integration providers.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `get_integration_available_apis()` | `GET /api/integrations/{name}/available` | Get available APIs | [Example](#get-integration-available-apis) |
| `get_integration_provider_defs()` | `GET /api/integrations/providers` | Get provider definitions | [Example](#get-integration-provider-defs) |
| `get_providers_and_integrations()` | `GET /api/integrations/all` | Get all providers and integrations | [Example](#get-providers-and-integrations) |

### Get Integration Available APIs

```python
# Get available APIs for a provider
available = integration_client.get_integration_available_apis('openai')
for api in available:
    print(f"Available: {api.name} - {api.description}")
```

### Get Integration Provider Defs

```python
# Get all provider definitions
providers = integration_client.get_integration_provider_defs()
for provider in providers:
    print(f"Provider: {provider.name}")
    print(f"  Type: {provider.type}")
    print(f"  Category: {provider.category}")
```

### Get Providers And Integrations

```python
# Get comprehensive view of all providers and their integrations
all_data = integration_client.get_providers_and_integrations()
for provider_name, integrations in all_data.items():
    print(f"Provider: {provider_name}")
    for integration in integrations:
        print(f"  - {integration.name}: {integration.enabled}")
```

---

## Models Reference

### Core Models

#### IntegrationUpdate

Request model for creating or updating an integration.

**Module:** `conductor.client.http.models.integration_update`

**Properties:**
- `type` (str, required): Integration type (e.g., 'openai', 'pinecone', 'kafka')
- `category` (str, required): Category (e.g., 'AI_MODEL', 'VECTOR_DB', 'MESSAGE_BROKER')
- `description` (str): Description of the integration
- `enabled` (bool): Whether integration is active
- `configuration` (dict): Configuration with valid ConfigKey values

**Valid ConfigKey values:**
- `api_key` - API key for authentication
- `endpoint` - API endpoint URL
- `environment` - Environment setting
- Other provider-specific keys (NOT 'model')

**Example:**
```python
from conductor.client.http.models.integration_update import IntegrationUpdate

integration = IntegrationUpdate(
    type='openai',
    category='AI_MODEL',
    description='OpenAI GPT models',
    enabled=True,
    configuration={
        'api_key': 'sk-your-key',  # ✅ Valid ConfigKey
        'endpoint': 'https://api.openai.com/v1'  # ✅ Valid ConfigKey
        # 'model': 'gpt-4'  # ❌ INVALID - model goes in API name
    }
)
```

#### IntegrationApiUpdate

Request model for adding/updating models or APIs within an integration.

**Module:** `conductor.client.http.models.integration_api_update`

**Properties:**
- `description` (str): Description of the model/API
- `enabled` (bool): Whether model is active
- `max_tokens` (int): Maximum token limit (for AI models)
- `configuration` (dict, optional): Additional valid configurations

**Example:**
```python
from conductor.client.http.models.integration_api_update import IntegrationApiUpdate

model = IntegrationApiUpdate(
    description='GPT-4 Optimized - Latest model',
    enabled=True,
    max_tokens=128000
    # Model name is passed as API parameter, not in configuration
)

# Use like this:
integration_client.save_integration_api('openai', 'gpt-4o', model)
#                                                  ^^^^^^^^ Model name here
```

#### Integration

Represents an integration provider.

**Module:** `conductor.client.http.models.integration`

**Properties:**
- `name` (str): Integration name
- `type` (str): Integration type
- `category` (str): Category
- `description` (str): Description
- `enabled` (bool): Active status
- `configuration` (dict): Current configuration

#### IntegrationApi

Represents a model or API within an integration.

**Module:** `conductor.client.http.models.integration_api`

**Properties:**
- `name` (str): Model/API name
- `description` (str): Description
- `enabled` (bool): Active status
- `max_tokens` (int): Token limit (for AI models)

#### MetadataTag

Tag for organizing integrations and models.

**Module:** `conductor.client.orkes.models.metadata_tag`

**Properties:**
- `key` (str, required): Tag key
- `value` (str, required): Tag value

**Example:**
```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

tags = [
    MetadataTag("environment", "production"),
    MetadataTag("team", "ai_platform"),
    MetadataTag("cost_tier", "premium")
]
```

---

## Integration Types

### AI/LLM Providers

**Type:** `openai`, `anthropic`, `cohere`, `huggingface`
**Category:** `AI_MODEL`

```python
# OpenAI Integration
integration = IntegrationUpdate(
    type='openai',
    category='AI_MODEL',
    description='OpenAI GPT models',
    enabled=True,
    configuration={
        'api_key': 'sk-your-key',
        'endpoint': 'https://api.openai.com/v1'
    }
)

# Add models
models = ['gpt-4o', 'gpt-4', 'gpt-3.5-turbo']
for model_name in models:
    model = IntegrationApiUpdate(
        description=f'{model_name} model',
        enabled=True,
        max_tokens=128000
    )
    integration_client.save_integration_api('openai', model_name, model)
```

### Vector Databases

**Type:** `pinecone`, `weaviate`, `qdrant`
**Category:** `VECTOR_DB`

```python
# Pinecone Integration
integration = IntegrationUpdate(
    type='pinecone',
    category='VECTOR_DB',
    description='Pinecone vector database',
    enabled=True,
    configuration={
        'api_key': 'your-pinecone-key',
        'environment': 'us-west1-gcp'
    }
)

# Add indexes
index = IntegrationApiUpdate(
    description='Product embeddings index',
    enabled=True
)
integration_client.save_integration_api('pinecone', 'product-index', index)
```

### Message Brokers

**Type:** `kafka`
**Category:** `MESSAGE_BROKER`

```python
# Kafka Integration
integration = IntegrationUpdate(
    type='kafka',
    category='MESSAGE_BROKER',
    description='Kafka cluster',
    enabled=True,
    configuration={
        'bootstrap_servers': 'localhost:9092',
        'security_protocol': 'SASL_SSL'
    }
)

# Add topics
topic = IntegrationApiUpdate(
    description='Events topic',
    enabled=True
)
integration_client.save_integration_api('kafka', 'events-topic', topic)
```

---

## Complete Setup Example

Here's a complete example setting up an AI integration with models and tags:

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_integration_client import OrkesIntegrationClient
from conductor.client.http.models.integration_update import IntegrationUpdate
from conductor.client.http.models.integration_api_update import IntegrationApiUpdate
from conductor.client.orkes.models.metadata_tag import MetadataTag

# Initialize
configuration = Configuration()
client = OrkesIntegrationClient(configuration)

# 1. Create Integration
integration = IntegrationUpdate(
    type='openai',
    category='AI_MODEL',
    description='OpenAI GPT models for production',
    enabled=True,
    configuration={
        'api_key': 'sk-your-openai-key',
        'endpoint': 'https://api.openai.com/v1'
    }
)
client.save_integration('openai', integration)

# 2. Add Models
models = [
    {'name': 'gpt-4o', 'tokens': 128000, 'desc': 'Optimized GPT-4'},
    {'name': 'gpt-4', 'tokens': 8192, 'desc': 'Standard GPT-4'},
    {'name': 'gpt-3.5-turbo', 'tokens': 16384, 'desc': 'Fast GPT-3.5'}
]

for model_info in models:
    model = IntegrationApiUpdate(
        description=model_info['desc'],
        enabled=True,
        max_tokens=model_info['tokens']
    )
    client.save_integration_api('openai', model_info['name'], model)

# 3. Tag Integration
integration_tags = [
    MetadataTag("environment", "production"),
    MetadataTag("team", "ai_platform"),
    MetadataTag("cost_center", "engineering")
]
client.put_tag_for_integration_provider(integration_tags, 'openai')

# 4. Tag Models
model_tags = [
    MetadataTag("performance", "optimized"),
    MetadataTag("cost_tier", "premium")
]
client.put_tag_for_integration(model_tags, 'gpt-4o', 'openai')

# 5. Verify Setup
integration = client.get_integration('openai')
print(f"Integration: {integration.name} - {integration.enabled}")

models = client.get_integration_apis('openai')
for model in models:
    print(f"  Model: {model.name} - {model.enabled}")

# 6. Check Token Usage
usage = client.get_token_usage_for_integration_provider('openai')
print(f"Total usage: {usage}")
```

---

## Best Practices

### 1. Always Configure Models

Even if an integration exists, always configure the required models:

```python
# WRONG - Integration alone is not enough
client.save_integration('openai', integration)
# Missing: Model configuration

# RIGHT - Integration + Models
client.save_integration('openai', integration)
for model_name in ['gpt-4o', 'gpt-4']:
    model = IntegrationApiUpdate(...)
    client.save_integration_api('openai', model_name, model)
```

### 2. Use Correct Model Format

```python
# WRONG in API calls
text_complete_model='openai:gpt-4o'  # ❌

# RIGHT in API calls
text_complete_model='gpt-4o'  # ✅
ai_integration='openai'  # ✅ Separate parameter
```

### 3. Use Valid Configuration Keys

```python
# WRONG
configuration={
    'apiKey': 'key',  # ❌ Invalid ConfigKey
    'model': 'gpt-4'  # ❌ Model goes in API name
}

# RIGHT
configuration={
    'api_key': 'key',  # ✅ Valid ConfigKey
    'endpoint': 'url'  # ✅ Valid ConfigKey
}
```

### 4. Tag for Organization

Use consistent tagging strategy:

```python
# Integration-level tags
integration_tags = [
    MetadataTag("provider", "openai"),
    MetadataTag("environment", "production"),
    MetadataTag("team", "ai_platform")
]

# Model-level tags
model_tags = [
    MetadataTag("model_type", "optimized"),
    MetadataTag("context_window", "128k"),
    MetadataTag("cost_tier", "premium")
]
```

### 5. Monitor Token Usage

Regularly check token usage for cost optimization:

```python
# Provider level
provider_usage = client.get_token_usage_for_integration_provider('openai')

# Model level
for model in ['gpt-4o', 'gpt-4', 'gpt-3.5-turbo']:
    usage = client.get_token_usage_for_integration(model, 'openai')
    print(f"{model}: {usage:,} tokens")
```

---

## Error Handling

```python
from conductor.client.http.rest import ApiException

try:
    integration = client.get_integration('openai')
    if not integration:
        # Integration doesn't exist, create it
        integration = IntegrationUpdate(...)
        client.save_integration('openai', integration)

except ApiException as e:
    if e.status == 404:
        print("Integration not found")
    elif e.status == 400:
        print("Invalid configuration")
    else:
        print(f"Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")

# Always verify models are configured
try:
    models = client.get_integration_apis('openai')
    if not models:
        print("No models configured, adding default models...")
        # Add models
except Exception as e:
    print(f"Error checking models: {e}")
```

---

## See Also

- [Prompt Management](./PROMPT.md) - Using prompts with integrations
- [Working Example](../examples/prompt_journey.py) - Complete implementation
- [Authorization](./AUTHORIZATION.md) - Access control for integrations