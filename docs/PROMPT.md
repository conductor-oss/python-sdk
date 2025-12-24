# Prompt Management API Reference

This document provides a comprehensive reference for all Prompt Management APIs available in the Conductor Python SDK.

> 📚 **Complete Working Example**: See [prompt_journey.py](../../examples/prompt_journey.py) for a comprehensive example covering all 8 APIs.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Prompt Templates](#prompt-templates)
- [Version Management](#version-management)
- [Prompt Tags](#prompt-tags)
- [Testing Prompts](#testing-prompts)
- [Models Reference](#models-reference)
- [Integration with Workflows](#integration-with-workflows)
- [API Coverage Summary](#api-coverage-summary)
- [Best Practices](#best-practices)
- [Error Handling](#error-handling)

## Prerequisites

### Required: Integration Setup

⚠️ **IMPORTANT**: Before using prompts with AI models, you MUST set up integrations:

```python
from conductor.client.orkes.orkes_integration_client import OrkesIntegrationClient
from conductor.client.http.models.integration_update import IntegrationUpdate
from conductor.client.http.models.integration_api_update import IntegrationApiUpdate

# Step 1: Create Integration
integration = IntegrationUpdate(
    type='openai',
    category='AI_MODEL',
    description='OpenAI models',
    enabled=True,
    configuration={
        'api_key': 'sk-your-key',
        'endpoint': 'https://api.openai.com/v1'
    }
)
integration_client.save_integration('openai', integration)

# Step 2: Add Models (REQUIRED even if integration exists!)
model = IntegrationApiUpdate(
    description='GPT-4 Optimized',
    enabled=True,
    max_tokens=128000
)
integration_client.save_integration_api('openai', 'gpt-4o', model)
```

See [Integration Documentation](./INTEGRATION.md) for complete setup.

---

## Quick Start

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_prompt_client import OrkesPromptClient

# Initialize client
configuration = Configuration()
prompt_client = OrkesPromptClient(configuration)

# Create a prompt
prompt_client.save_prompt(
    prompt_name="greeting",
    description="Customer greeting",
    prompt_template="Hello ${customer_name}, how can I help you?"
)

# Test the prompt
response = prompt_client.test_prompt(
    prompt_text="Hello ${customer_name}, how can I help you?",
    variables={"customer_name": "Alice"},
    ai_integration="openai",
    text_complete_model="gpt-4o",
    temperature=0.7
)
```

---

## Prompt Templates

Manage prompt templates for AI/LLM interactions.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `save_prompt()` | `PUT /api/prompts/{name}` | Create or update prompt | [Example](#save-prompt) |
| `get_prompt()` | `GET /api/prompts/{name}` | Get prompt by name | [Example](#get-prompt) |
| `get_prompts()` | `GET /api/prompts` | List all prompts | [Example](#get-prompts) |
| `delete_prompt()` | `DELETE /api/prompts/{name}` | Delete a prompt | [Example](#delete-prompt) |

### Save Prompt

Creates or updates a prompt template with optional version management.

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_prompt_client import OrkesPromptClient

configuration = Configuration()
prompt_client = OrkesPromptClient(configuration)

# Basic prompt creation
prompt_client.save_prompt(
    prompt_name="customer_greeting",
    description="Personalized customer greeting",
    prompt_template="Hello ${customer_name}, how can I help you today?"
)

# With explicit version (default is 1)
prompt_client.save_prompt(
    prompt_name="order_inquiry",
    description="Order status inquiry handler",
    prompt_template="Order ${order_id}: Status is ${status}",
    version=1  # Explicit version
)

# With model associations
prompt_client.save_prompt(
    prompt_name="complex_analysis",
    description="Complex analysis requiring GPT-4",
    prompt_template="${analysis_prompt}",
    models=['gpt-4o', 'gpt-4']  # Just model names, no prefix
)

# With auto-increment for updates
prompt_client.save_prompt(
    prompt_name="existing_prompt",
    description="Updated description",
    prompt_template="Updated template",
    auto_increment=True  # Auto-increment version
)
```

### Get Prompt

```python
# Get prompt by name
prompt = prompt_client.get_prompt("customer_greeting")
if prompt:
    print(f"Name: {prompt.name}")
    print(f"Description: {prompt.description}")
    print(f"Template: {prompt.template}")
    print(f"Variables: {prompt.variables}")
    print(f"Version: {prompt.version}")
```

### Get Prompts

```python
# List all prompts
prompts = prompt_client.get_prompts()
for prompt in prompts:
    print(f"Prompt: {prompt.name} v{prompt.version}")
    print(f"  Description: {prompt.description}")
    print(f"  Variables: {prompt.variables}")
```

### Delete Prompt

```python
# Delete a prompt
prompt_client.delete_prompt("old_prompt")
print("✅ Prompt deleted")
```

---

## Version Management

Conductor supports versioning for prompt templates to track changes and enable rollbacks.

| Feature | Description | Example |
|---------|-------------|---------|
| Explicit Version | Set specific version number | `version=2` |
| Auto-Increment | Automatically increment version | `auto_increment=True` |
| Default Version | New prompts default to version 1 | Default behavior |

### Creating Versions

```python
# Version 1 - Initial prompt
prompt_client.save_prompt(
    prompt_name="faq_response",
    description="FAQ response generator - v1",
    prompt_template="Answer: ${question}",
    version=1
)

# Version 2 - Enhanced version
prompt_client.save_prompt(
    prompt_name="faq_response",
    description="FAQ response generator - v2 with category",
    prompt_template="Category: ${category}\nQuestion: ${question}\nAnswer:",
    version=2
)

# Version 3 - Auto-incremented
prompt_client.save_prompt(
    prompt_name="faq_response",
    description="FAQ response generator - v3 with urgency",
    prompt_template="Urgency: ${urgency}\nCategory: ${category}\nQuestion: ${question}",
    auto_increment=True  # Will become version 3
)
```

### Version Best Practices

1. **Major Changes**: Use explicit version numbers
2. **Minor Updates**: Use auto-increment
3. **Testing**: Create separate versions for A/B testing
4. **Rollback**: Keep previous versions for quick rollback

---

## Prompt Tags

Organize and categorize prompts with metadata tags.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `update_tag_for_prompt_template()` | `PUT /api/prompts/{name}/tags` | Add/update tags | [Example](#update-tag-for-prompt-template) |
| `get_tags_for_prompt_template()` | `GET /api/prompts/{name}/tags` | Get prompt tags | [Example](#get-tags-for-prompt-template) |
| `delete_tag_for_prompt_template()` | `DELETE /api/prompts/{name}/tags` | Delete tags | [Example](#delete-tag-for-prompt-template) |

### Update Tag For Prompt Template

```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

# Add tags for organization
tags = [
    MetadataTag("category", "customer_service"),
    MetadataTag("type", "greeting"),
    MetadataTag("language", "english"),
    MetadataTag("status", "production"),
    MetadataTag("model_tested", "gpt-4o"),
    MetadataTag("version_status", "active")
]

# Note: prompt_name is first parameter, then tags
prompt_client.update_tag_for_prompt_template("customer_greeting", tags)
print("✅ Tags added to prompt")
```

### Get Tags For Prompt Template

```python
# Get all tags for a prompt
tags = prompt_client.get_tags_for_prompt_template("customer_greeting")
for tag in tags:
    print(f"Tag: {tag.key} = {tag.value}")
```

### Delete Tag For Prompt Template

```python
# Delete specific tags
tags_to_remove = [
    MetadataTag("status", "testing"),
    MetadataTag("version_status", "deprecated")
]

# Note: prompt_name is first parameter, then tags
prompt_client.delete_tag_for_prompt_template("customer_greeting", tags_to_remove)
print("✅ Tags removed")
```

---

## Testing Prompts

Test prompts with actual AI models before deployment.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `test_prompt()` | `POST /api/prompts/test` | Test prompt with AI model | [Example](#test-prompt) |

### Test Prompt

```python
# Test with variables and AI model
response = prompt_client.test_prompt(
    prompt_text="Greet ${customer_name} who is a ${customer_tier} member",
    variables={
        "customer_name": "John Smith",
        "customer_tier": "Premium"
    },
    ai_integration="openai",  # Integration name
    text_complete_model="gpt-4o",  # Model name (no prefix!)
    temperature=0.7,
    top_p=0.9,
    stop_words=None  # Optional list of stop words
)

print(f"AI Response: {response}")

# Test with different parameters
test_configs = [
    {"temp": 0.3, "desc": "Conservative"},
    {"temp": 0.7, "desc": "Balanced"},
    {"temp": 0.9, "desc": "Creative"}
]

for config in test_configs:
    response = prompt_client.test_prompt(
        prompt_text=template,
        variables=variables,
        ai_integration="openai",
        text_complete_model="gpt-4o",
        temperature=config["temp"],
        top_p=0.9
    )
    print(f"{config['desc']}: {response[:100]}...")
```

---

## Models Reference

### Core Models

#### PromptTemplate

Represents a prompt template with metadata.

**Module:** `conductor.client.http.models.prompt_template`

**Properties:**
- `name` (str): Unique prompt name
- `description` (str): Prompt description
- `template` (str): Prompt template with variables
- `variables` (List[str]): List of variable names
- `version` (int): Version number (default: 1)
- `tags` (List[MetadataTag]): Associated tags
- `created_by` (str): Creator username
- `created_on` (int): Creation timestamp
- `updated_on` (int): Last update timestamp

**Example:**
```python
prompt = prompt_client.get_prompt("customer_greeting")
print(f"Name: {prompt.name}")
print(f"Version: {prompt.version}")
print(f"Variables: {prompt.variables}")  # ['customer_name', 'customer_tier']
```

#### MetadataTag

Tag for organizing prompts.

**Module:** `conductor.client.orkes.models.metadata_tag`

**Properties:**
- `key` (str): Tag key
- `value` (str): Tag value

**Example:**
```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

tags = [
    MetadataTag("environment", "production"),
    MetadataTag("team", "customer_service"),
    MetadataTag("compliance", "pii_safe")
]
```

---


## Integration with Workflows

Use prompts in workflows via AI tasks for automated processing.

```python
from conductor.client.workflow.task.llm_text_complete_task import LlmTextCompleteTask

# Use saved prompt in workflow
llm_task = LlmTextCompleteTask(
    task_ref_name="generate_response",
    llm_provider="openai",
    model="gpt-4o",  # Just model name, no prefix
    prompt_name="customer_greeting",
    prompt_variables={
        "customer_name": "${workflow.input.customer_name}",
        "customer_tier": "${workflow.input.tier}",
        "time_of_day": "${workflow.input.time}"
    },
    temperature=0.7,
    top_p=0.9
)

# Add to workflow definition
workflow.add(llm_task)
```

---

## Complete Example

Here's a complete example demonstrating prompt management with integrations:

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_prompt_client import OrkesPromptClient
from conductor.client.orkes.orkes_integration_client import OrkesIntegrationClient
from conductor.client.http.models.integration_update import IntegrationUpdate
from conductor.client.http.models.integration_api_update import IntegrationApiUpdate
from conductor.client.orkes.models.metadata_tag import MetadataTag

# Initialize clients
configuration = Configuration()
prompt_client = OrkesPromptClient(configuration)
integration_client = OrkesIntegrationClient(configuration)

# 1. Setup Integration
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
integration_client.save_integration('openai', integration)

# 2. Add Models
model = IntegrationApiUpdate(
    description='GPT-4 Optimized',
    enabled=True,
    max_tokens=128000
)
integration_client.save_integration_api('openai', 'gpt-4o', model)

# 3. Create Prompt with Version
prompt_client.save_prompt(
    prompt_name="customer_greeting",
    description="Personalized greeting",
    prompt_template="""Hello ${customer_name}!

As a ${customer_tier} member, you have access to priority support.
How can I help you today?""",
    version=1,
    models=['gpt-4o', 'gpt-4']
)

# 4. Tag Prompt
tags = [
    MetadataTag("category", "customer_service"),
    MetadataTag("status", "production"),
    MetadataTag("language", "english")
]
prompt_client.update_tag_for_prompt_template("customer_greeting", tags)

# 5. Test Prompt
prompt = prompt_client.get_prompt("customer_greeting")
response = prompt_client.test_prompt(
    prompt_text=prompt.template,
    variables={
        "customer_name": "John Smith",
        "customer_tier": "Premium"
    },
    ai_integration="openai",
    text_complete_model="gpt-4o",
    temperature=0.7,
    top_p=0.9
)
print(f"Response: {response}")

# 6. Create Updated Version
prompt_client.save_prompt(
    prompt_name="customer_greeting",
    description="Enhanced greeting with time awareness",
    prompt_template="""Good ${time_of_day}, ${customer_name}!

As a valued ${customer_tier} member, you have priority access.
How may I assist you today?""",
    auto_increment=True  # Version 2
)
```

---

## API Coverage Summary

### Prompt Management APIs (8 total)

| API | Method | Status | Description |
|-----|--------|--------|-------------|
| `save_prompt()` | `PUT` | ✅ Implemented | Create/update prompts with versioning |
| `get_prompt()` | `GET` | ✅ Implemented | Retrieve specific prompt |
| `get_prompts()` | `GET` | ✅ Implemented | List all prompts |
| `delete_prompt()` | `DELETE` | ✅ Implemented | Delete prompt |
| `update_tag_for_prompt_template()` | `PUT` | ✅ Implemented | Add/update tags |
| `get_tags_for_prompt_template()` | `GET` | ✅ Implemented | Get prompt tags |
| `delete_tag_for_prompt_template()` | `DELETE` | ✅ Implemented | Remove tags |
| `test_prompt()` | `POST` | ✅ Implemented | Test with AI model |

**Coverage: 8/8 APIs (100%)**

---

## Best Practices

### 1. Integration Setup

**Always set up integrations before using prompts:**
```python
# ✅ RIGHT: Integration → Models → Prompts
integration_client.save_integration('openai', integration)
integration_client.save_integration_api('openai', 'gpt-4o', model)
prompt_client.save_prompt(...)

# ❌ WRONG: Prompts without integration
prompt_client.save_prompt(...)  # Will fail when testing
```

### 2. Model Format

**Use correct model naming in API calls:**
```python
# ✅ RIGHT
ai_integration="openai"
text_complete_model="gpt-4o"  # Just model name

# ❌ WRONG
text_complete_model="openai:gpt-4o"  # Don't use prefix
```

### 3. Version Management

```python
# Major changes: Explicit version
version=2

# Minor updates: Auto-increment
auto_increment=True

# Default for new prompts: Version 1
# (no version parameter needed)
```

### 4. Tag Strategy

```python
# Consistent tagging for organization
standard_tags = [
    MetadataTag("category", "customer_service"),
    MetadataTag("environment", "production"),
    MetadataTag("status", "active"),
    MetadataTag("compliance", "pii_safe"),
    MetadataTag("model_tested", "gpt-4o")
]
```

### 5. Testing Strategy

```python
# Test with different parameters
for temp in [0.3, 0.7, 0.9]:
    response = prompt_client.test_prompt(
        prompt_text=template,
        variables=variables,
        ai_integration="openai",
        text_complete_model="gpt-4o",
        temperature=temp
    )
    # Analyze response...
```

---

## Error Handling

```python
from conductor.client.http.rest import ApiException

try:
    # Check if prompt exists
    prompt = prompt_client.get_prompt("customer_greeting")
    if not prompt:
        print("Prompt not found, creating...")
        prompt_client.save_prompt(...)

except ApiException as e:
    if e.status == 404:
        print("Resource not found")
    elif e.status == 400:
        print("Invalid request")
    else:
        print(f"API Error: {e}")

except Exception as e:
    print(f"Unexpected error: {e}")

# Safe prompt testing
def safe_test(prompt_name, variables):
    try:
        prompt = prompt_client.get_prompt(prompt_name)
        if not prompt:
            return None

        return prompt_client.test_prompt(
            prompt_text=prompt.template,
            variables=variables,
            ai_integration="openai",
            text_complete_model="gpt-4o",
            temperature=0.7
        )
    except Exception as e:
        print(f"Test failed: {e}")
        return None
```

---

## Complete Working Example

For a comprehensive implementation demonstrating all prompt management features:

📚 **[examples/prompt_journey.py](../../examples/prompt_journey.py)**

This example includes:
- ✅ All 8 Prompt Management APIs
- ✅ Integration setup and model configuration
- ✅ Version management (explicit and auto-increment)
- ✅ Tag-based organization
- ✅ Testing with multiple models and parameters
- ✅ Real-world customer service scenarios
- ✅ Best practices and error handling

---

## See Also

- [Integration Management](./INTEGRATION.md) - Setting up AI providers
- [Workflow Management](./WORKFLOW.md) - Using prompts in workflows
- [Authorization](./AUTHORIZATION.md) - Access control for prompts