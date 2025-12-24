# Authorization API Reference

This document provides a comprehensive reference for all authorization and RBAC (Role-Based Access Control) APIs available in the Conductor Python SDK.

> 📚 **Complete Working Example**: See [authorization_journey.py](../../examples/authorization_journey.py) for a comprehensive example.

## Table of Contents
- [Applications](#applications)
- [Application Roles](#application-roles)
- [Application Tags](#application-tags)
- [Access Keys](#access-keys)
- [Users](#users)
- [Groups](#groups)
- [Group Users](#group-users)
- [Permissions](#permissions)
- [Roles](#roles)
- [Token & Authentication](#token--authentication)
- [API Gateway Authentication](#api-gateway-authentication)

---

## Applications

Manage applications in your Conductor instance.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `create_application()` | `POST /api/applications` | Create a new application | [Example](#create-application) |
| `get_application()` | `GET /api/applications/{id}` | Get application by ID | [Example](#get-application) |
| `list_applications()` | `GET /api/applications` | List all applications | [Example](#list-applications) |
| `update_application()` | `PUT /api/applications/{id}` | Update an existing application | [Example](#update-application) |
| `delete_application()` | `DELETE /api/applications/{id}` | Delete an application | [Example](#delete-application) |
| `get_app_by_access_key_id()` | `GET /api/applications/key/{accessKeyId}` | Get application ID by access key | [Example](#get-app-by-access-key-id) |

### Create Application

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_authorization_client import OrkesAuthorizationClient
from conductor.client.http.models.create_or_update_application_request import CreateOrUpdateApplicationRequest

configuration = Configuration()
auth_client = OrkesAuthorizationClient(configuration)

# Create application
request = CreateOrUpdateApplicationRequest(name="my-application")
app = auth_client.create_application(request)

print(f"Created application with ID: {app.id}")
```

### Get Application

```python
# Get application by ID
app = auth_client.get_application("app-id-123")
print(f"Application name: {app.name}")
```

### List Applications

```python
# List all applications
apps = auth_client.list_applications()
for app in apps:
    print(f"App ID: {app.id}, Name: {app.name}")
```

### Update Application

```python
# Update application
request = CreateOrUpdateApplicationRequest(name="my-updated-application")
updated_app = auth_client.update_application(request, "app-id-123")
```

### Delete Application

```python
# Delete application
auth_client.delete_application("app-id-123")
```

### Get App By Access Key ID

```python
# Get application ID by access key
app_id = auth_client.get_app_by_access_key_id("access-key-123")
print(f"Application ID: {app_id}")
```

---

## Application Roles

Manage roles for application users.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `add_role_to_application_user()` | `POST /api/applications/{applicationId}/roles/{role}` | Add a role to application user | [Example](#add-role-to-application-user) |
| `remove_role_from_application_user()` | `DELETE /api/applications/{applicationId}/roles/{role}` | Remove a role from application user | [Example](#remove-role-from-application-user) |

**Available Roles:**
- `USER` - Basic user access
- `ADMIN` - Administrative access
- `METADATA_MANAGER` - Manage workflow/task definitions
- `WORKFLOW_MANAGER` - Manage workflow executions
- `WORKER` - Worker task execution access

### Add Role To Application User

```python
# Add role to application user
auth_client.add_role_to_application_user("app-id-123", "ADMIN")
```

### Remove Role From Application User

```python
# Remove role from application user
auth_client.remove_role_from_application_user("app-id-123", "ADMIN")
```

---

## Application Tags

Manage tags for applications.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `set_application_tags()` | `PUT /api/applications/{id}/tags` | Set/add tags to application | [Example](#set-application-tags) |
| `get_application_tags()` | `GET /api/applications/{id}/tags` | Get all tags for application | [Example](#get-application-tags) |
| `delete_application_tags()` | `DELETE /api/applications/{id}/tags` | Delete tags from application | [Example](#delete-application-tags) |

### Set Application Tags

```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

# Set application tags
tags = [
    MetadataTag("environment", "production"),
    MetadataTag("team", "platform")
]
auth_client.set_application_tags(tags, "app-id-123")
```

### Get Application Tags

```python
# Get application tags
tags = auth_client.get_application_tags("app-id-123")
for tag in tags:
    print(f"Tag: {tag.key} = {tag.value}")
```

### Delete Application Tags

```python
# Delete specific tags
tags = [
    MetadataTag("environment", "production")
]
auth_client.delete_application_tags(tags, "app-id-123")
```

---

## Access Keys

Manage access keys for applications.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `create_access_key()` | `POST /api/applications/{id}/accessKeys` | Create a new access key | [Example](#create-access-key) |
| `get_access_keys()` | `GET /api/applications/{id}/accessKeys` | Get all access keys for application | [Example](#get-access-keys) |
| `toggle_access_key_status()` | `POST /api/applications/{applicationId}/accessKeys/{keyId}/status` | Toggle access key active/inactive | [Example](#toggle-access-key-status) |
| `delete_access_key()` | `DELETE /api/applications/{applicationId}/accessKeys/{keyId}` | Delete an access key | [Example](#delete-access-key) |

### Create Access Key

```python
# Create access key
access_key = auth_client.create_access_key("app-id-123")

# IMPORTANT: Save the secret immediately - it's only shown once!
print(f"Key ID: {access_key.id}")
print(f"Secret: {access_key.secret}")  # Only available at creation time
```

### Get Access Keys

```python
# Get all access keys for an application
keys = auth_client.get_access_keys("app-id-123")
for key in keys:
    print(f"Key ID: {key.id}, Status: {key.status}")
```

### Toggle Access Key Status

```python
# Toggle access key between ACTIVE and INACTIVE
key = auth_client.toggle_access_key_status("app-id-123", "key-id-456")
print(f"New status: {key.status}")
```

### Delete Access Key

```python
# Delete access key
auth_client.delete_access_key("app-id-123", "key-id-456")
```

---

## Users

Manage users in your Conductor instance.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `upsert_user()` | `PUT /api/users/{id}` | Create or update a user | [Example](#upsert-user) |
| `get_user()` | `GET /api/users/{id}` | Get user by ID | [Example](#get-user) |
| `list_users()` | `GET /api/users` | List all users | [Example](#list-users) |
| `delete_user()` | `DELETE /api/users/{id}` | Delete a user | [Example](#delete-user) |
| `get_granted_permissions_for_user()` | `GET /api/users/{userId}/permissions` | Get all permissions granted to user | [Example](#get-granted-permissions-for-user) |
| `check_permissions()` | `GET /api/users/{userId}/checkPermissions` | Check if user has specific permissions | [Example](#check-permissions) |

### Upsert User

```python
from conductor.client.http.models.upsert_user_request import UpsertUserRequest

# Create or update user
user_id = "user@example.com"
request = UpsertUserRequest(
    name="John Doe",
    roles=["USER", "METADATA_MANAGER"]
)
user = auth_client.upsert_user(request, user_id)
print(f"User created: {user.id}")
```

### Get User

```python
# Get user by ID
user = auth_client.get_user("user@example.com")
print(f"User name: {user.name}")
print(f"Roles: {user.roles}")
```

### List Users

```python
# List all users
users = auth_client.list_users()
for user in users:
    print(f"User: {user.id}, Name: {user.name}")

# List users including applications
users_with_apps = auth_client.list_users(apps=True)
```

### Delete User

```python
# Delete user
auth_client.delete_user("user@example.com")
```

### Get Granted Permissions For User

```python
# Get all permissions granted to user
permissions = auth_client.get_granted_permissions_for_user("user@example.com")
for perm in permissions:
    print(f"Target: {perm.target.type}:{perm.target.id}")
    print(f"Access: {perm.access}")
```

### Check Permissions

```python
# Check if user has specific permissions on a target
result = auth_client.check_permissions(
    user_id="user@example.com",
    target_type="WORKFLOW_DEF",
    target_id="my-workflow"
)
print(f"Has access: {result}")
```

---

## Groups

Manage user groups in your Conductor instance.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `upsert_group()` | `PUT /api/groups/{id}` | Create or update a group | [Example](#upsert-group) |
| `get_group()` | `GET /api/groups/{id}` | Get group by ID | [Example](#get-group) |
| `list_groups()` | `GET /api/groups` | List all groups | [Example](#list-groups) |
| `delete_group()` | `DELETE /api/groups/{id}` | Delete a group | [Example](#delete-group) |
| `get_granted_permissions_for_group()` | `GET /api/groups/{groupId}/permissions` | Get all permissions granted to group | [Example](#get-granted-permissions-for-group) |

### Upsert Group

```python
from conductor.client.http.models.upsert_group_request import UpsertGroupRequest

# Create or update group
group_id = "engineering-team"
request = UpsertGroupRequest(
    description="Engineering Team",
    roles=["USER", "WORKFLOW_MANAGER"]
)
group = auth_client.upsert_group(request, group_id)
print(f"Group created: {group.id}")
```

### Get Group

```python
# Get group by ID
group = auth_client.get_group("engineering-team")
print(f"Group description: {group.description}")
print(f"Roles: {group.roles}")
```

### List Groups

```python
# List all groups
groups = auth_client.list_groups()
for group in groups:
    print(f"Group: {group.id}, Description: {group.description}")
```

### Delete Group

```python
# Delete group
auth_client.delete_group("engineering-team")
```

### Get Granted Permissions For Group

```python
# Get all permissions granted to group
permissions = auth_client.get_granted_permissions_for_group("engineering-team")
for perm in permissions:
    print(f"Target: {perm.target.type}:{perm.target.id}")
    print(f"Access: {perm.access}")
```

---

## Group Users

Manage users within groups.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `add_user_to_group()` | `POST /api/groups/{groupId}/users/{userId}` | Add a single user to group | [Example](#add-user-to-group) |
| `add_users_to_group()` | `POST /api/groups/{groupId}/users` | Add multiple users to group | [Example](#add-users-to-group) |
| `get_users_in_group()` | `GET /api/groups/{id}/users` | Get all users in group | [Example](#get-users-in-group) |
| `remove_user_from_group()` | `DELETE /api/groups/{groupId}/users/{userId}` | Remove a single user from group | [Example](#remove-user-from-group) |
| `remove_users_from_group()` | `DELETE /api/groups/{groupId}/users` | Remove multiple users from group | [Example](#remove-users-from-group) |

### Add User To Group

```python
# Add single user to group
auth_client.add_user_to_group("engineering-team", "user@example.com")
```

### Add Users To Group

```python
# Add multiple users to group (bulk operation)
user_ids = [
    "user1@example.com",
    "user2@example.com",
    "user3@example.com"
]
auth_client.add_users_to_group("engineering-team", user_ids)
```

### Get Users In Group

```python
# Get all users in a group
users = auth_client.get_users_in_group("engineering-team")
for user in users:
    print(f"User: {user.id}, Name: {user.name}")
```

### Remove User From Group

```python
# Remove single user from group
auth_client.remove_user_from_group("engineering-team", "user@example.com")
```

### Remove Users From Group

```python
# Remove multiple users from group (bulk operation)
user_ids = [
    "user1@example.com",
    "user2@example.com"
]
auth_client.remove_users_from_group("engineering-team", user_ids)
```

---

## Permissions

Manage permissions and access control.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `grant_permissions()` | `POST /api/auth/authorization` | Grant permissions to subject on target | [Example](#grant-permissions) |
| `get_permissions()` | `GET /api/auth/authorization/{type}/{id}` | Get all permissions for a target | [Example](#get-permissions) |
| `remove_permissions()` | `DELETE /api/auth/authorization` | Remove permissions from subject on target | [Example](#remove-permissions) |

**Target Types:**
- `WORKFLOW_DEF` - Workflow definition
- `TASK_DEF` - Task definition
- `APPLICATION` - Application
- `USER` - User
- `DOMAIN` - Domain

**Subject Types:**
- `USER` - Individual user
- `GROUP` - User group
- `ROLE` - Role

**Access Types:**
- `READ` - Read access
- `CREATE` - Create access
- `UPDATE` - Update access
- `EXECUTE` - Execute access
- `DELETE` - Delete access

### Grant Permissions

```python
from conductor.client.http.models.target_ref import TargetRef, TargetType
from conductor.client.http.models.subject_ref import SubjectRef, SubjectType
from conductor.client.orkes.models.access_type import AccessType

# Grant permissions to a group on a workflow
target = TargetRef(TargetType.WORKFLOW_DEF, "order-processing-workflow")
subject = SubjectRef(SubjectType.GROUP, "engineering-team")
access = [AccessType.READ, AccessType.EXECUTE]

auth_client.grant_permissions(subject, target, access)

# Grant permissions to a user on a task
target = TargetRef(TargetType.TASK_DEF, "send-email-task")
subject = SubjectRef(SubjectType.USER, "user@example.com")
access = [AccessType.READ, AccessType.UPDATE]

auth_client.grant_permissions(subject, target, access)
```

### Get Permissions

```python
from conductor.client.http.models.target_ref import TargetRef, TargetType

# Get all permissions for a workflow
target = TargetRef(TargetType.WORKFLOW_DEF, "order-processing-workflow")
permissions = auth_client.get_permissions(target)

# permissions is a Dict[str, List[SubjectRef]]
# Key is AccessType, value is list of subjects with that access
for access_type, subjects in permissions.items():
    print(f"Access Type: {access_type}")
    for subject in subjects:
        print(f"  Subject: {subject.type}:{subject.id}")
```

### Remove Permissions

```python
from conductor.client.http.models.target_ref import TargetRef, TargetType
from conductor.client.http.models.subject_ref import SubjectRef, SubjectType
from conductor.client.orkes.models.access_type import AccessType

# Remove permissions from a group
target = TargetRef(TargetType.WORKFLOW_DEF, "order-processing-workflow")
subject = SubjectRef(SubjectType.GROUP, "engineering-team")
access = [AccessType.EXECUTE]

auth_client.remove_permissions(subject, target, access)
```

---

## Roles

Manage custom roles and role-based access control.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `list_all_roles()` | `GET /api/roles` | List all roles (system + custom) | [Example](#list-all-roles) |
| `list_system_roles()` | `GET /api/roles/system` | List system-defined roles | [Example](#list-system-roles) |
| `list_custom_roles()` | `GET /api/roles/custom` | List custom roles only | [Example](#list-custom-roles) |
| `list_available_permissions()` | `GET /api/roles/permissions` | List all available permissions | [Example](#list-available-permissions) |
| `create_role()` | `POST /api/roles` | Create a new custom role | [Example](#create-role) |
| `get_role()` | `GET /api/roles/{name}` | Get role by name | [Example](#get-role) |
| `update_role()` | `PUT /api/roles/{name}` | Update an existing custom role | [Example](#update-role) |
| `delete_role()` | `DELETE /api/roles/{name}` | Delete a custom role | [Example](#delete-role) |

### List All Roles

```python
# List all roles (system + custom)
roles = auth_client.list_all_roles()
for role in roles:
    print(f"Role: {role['name']}")
    print(f"  Description: {role.get('description', 'N/A')}")
    print(f"  Type: {role.get('type', 'custom')}")
```

### List System Roles

```python
# List system-defined roles
system_roles = auth_client.list_system_roles()
for role_name, role_data in system_roles.items():
    print(f"System Role: {role_name}")
    print(f"  Permissions: {role_data.get('permissions', [])}")
```

### List Custom Roles

```python
# List custom roles only
custom_roles = auth_client.list_custom_roles()
for role in custom_roles:
    print(f"Custom Role: {role['name']}")
```

### List Available Permissions

```python
# List all available permissions that can be assigned to roles
permissions = auth_client.list_available_permissions()
for resource_type, perms in permissions.items():
    print(f"Resource: {resource_type}")
    print(f"  Permissions: {perms}")
```

### Create Role

```python
# Create a custom role
role_request = {
    "name": "workflow-operator",
    "description": "Can execute and monitor workflows",
    "permissions": [
        {
            "resource": "WORKFLOW_DEF",
            "actions": ["READ", "EXECUTE"]
        },
        {
            "resource": "WORKFLOW",
            "actions": ["READ", "EXECUTE"]
        }
    ]
}
role = auth_client.create_role(role_request)
print(f"Created role: {role['name']}")
```

### Get Role

```python
# Get role by name
role = auth_client.get_role("workflow-operator")
print(f"Role: {role['name']}")
print(f"Permissions: {role['permissions']}")
```

### Update Role

```python
# Update an existing custom role
role_update = {
    "description": "Updated description",
    "permissions": [
        {
            "resource": "WORKFLOW_DEF",
            "actions": ["READ", "EXECUTE", "UPDATE"]
        }
    ]
}
updated_role = auth_client.update_role("workflow-operator", role_update)
```

### Delete Role

```python
# Delete a custom role
auth_client.delete_role("workflow-operator")
```

---

## Token & Authentication

Manage authentication tokens and retrieve user information.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `get_user_info_from_token()` | `GET /api/token/userInfo` | Get user info from current auth token | [Example](#get-user-info-from-token) |
| `generate_token()` | `POST /api/token` | Generate JWT with access key credentials | [Example](#generate-token) |

### Get User Info From Token

```python
# Get user information from the current authentication token
user_info = auth_client.get_user_info_from_token()

print(f"User ID: {user_info.get('id')}")
print(f"User Name: {user_info.get('name')}")
print(f"Roles: {user_info.get('roles')}")
print(f"Application: {user_info.get('application')}")
```

### Generate Token

```python
# Generate JWT token using access key credentials
token_response = auth_client.generate_token(
    key_id="your-access-key-id",
    key_secret="your-access-key-secret"
)

jwt_token = token_response.get('token')
expires_in = token_response.get('expiresIn')

print(f"JWT Token: {jwt_token}")
print(f"Expires in: {expires_in} seconds")

# Use this token for API authentication
configuration = Configuration()
configuration.set_authentication_settings(jwt_token)
```

---

## API Gateway Authentication

Manage authentication configurations for the API Gateway.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `create_gateway_auth_config()` | `POST /api/gateway/config/auth` | Create gateway auth configuration | [Example](#create-gateway-auth-config) |
| `get_gateway_auth_config()` | `GET /api/gateway/config/auth/{id}` | Get gateway auth configuration by ID | [Example](#get-gateway-auth-config) |
| `list_gateway_auth_configs()` | `GET /api/gateway/config/auth` | List all gateway auth configurations | [Example](#list-gateway-auth-configs) |
| `update_gateway_auth_config()` | `PUT /api/gateway/config/auth/{id}` | Update gateway auth configuration | [Example](#update-gateway-auth-config) |
| `delete_gateway_auth_config()` | `DELETE /api/gateway/config/auth/{id}` | Delete gateway auth configuration | [Example](#delete-gateway-auth-config) |

### Create Gateway Auth Config

```python
# Create API Gateway authentication configuration
auth_config = {
    "name": "my-api-gateway-auth",
    "type": "BEARER",
    "enabled": True,
    "config": {
        "headerName": "Authorization",
        "headerPrefix": "Bearer",
        "validateToken": True
    }
}

config = auth_client.create_gateway_auth_config(auth_config)
config_id = config.get('id')
print(f"Created gateway auth config with ID: {config_id}")
```

### Get Gateway Auth Config

```python
# Get gateway auth configuration by ID
config = auth_client.get_gateway_auth_config("config-id-123")
print(f"Config name: {config.get('name')}")
print(f"Config type: {config.get('type')}")
print(f"Enabled: {config.get('enabled')}")
```

### List Gateway Auth Configs

```python
# List all gateway auth configurations
configs = auth_client.list_gateway_auth_configs()
for config in configs:
    print(f"ID: {config.get('id')}")
    print(f"Name: {config.get('name')}")
    print(f"Type: {config.get('type')}")
    print(f"Enabled: {config.get('enabled')}")
    print("---")
```

### Update Gateway Auth Config

```python
# Update gateway auth configuration
updated_config = {
    "name": "my-api-gateway-auth-updated",
    "type": "BEARER",
    "enabled": False,  # Disable the config
    "config": {
        "headerName": "X-API-Key",
        "headerPrefix": "ApiKey",
        "validateToken": True
    }
}

config = auth_client.update_gateway_auth_config("config-id-123", updated_config)
print(f"Updated config: {config.get('name')}")
```

### Delete Gateway Auth Config

```python
# Delete gateway auth configuration
auth_client.delete_gateway_auth_config("config-id-123")
print("Gateway auth config deleted successfully")
```

---

## Models Reference

This section provides detailed information about all the models (data classes) used in authorization APIs.

### Core Models

#### SubjectRef

Represents a user, group, or role that is granted or removed access.

**Module:** `conductor.client.http.models.subject_ref`

**Properties:**
- `type` (str, required): The subject type - one of `USER`, `ROLE`, or `GROUP`
- `id` (str, required): The identifier of the subject (e.g., user email, group ID, role name)

**Subject Types:**
- `USER` - An individual user identified by email or user ID
- `ROLE` - A role name
- `GROUP` - A group identified by group ID

**Example:**
```python
from conductor.client.http.models.subject_ref import SubjectRef, SubjectType

# User subject
user_subject = SubjectRef(SubjectType.USER, "user@example.com")

# Group subject
group_subject = SubjectRef(SubjectType.GROUP, "engineering-team")

# Role subject
role_subject = SubjectRef(SubjectType.ROLE, "workflow-operator")
```

---

#### TargetRef

Represents the object over which access is being granted or removed.

**Module:** `conductor.client.http.models.target_ref`

**Properties:**
- `type` (str, required): The target type (see Target Types below)
- `id` (str, required): The identifier of the target resource

**Target Types:**
- `WORKFLOW_DEF` - Workflow definition (template)
- `WORKFLOW` - Workflow execution instance
- `WORKFLOW_SCHEDULE` - Scheduled workflow
- `TASK_DEF` - Task definition
- `TASK_REF_NAME` - Task reference name
- `TASK_ID` - Specific task instance
- `APPLICATION` - Application
- `USER` - User
- `SECRET_NAME` - Secret
- `ENV_VARIABLE` - Environment variable
- `TAG` - Tag
- `DOMAIN` - Domain
- `INTEGRATION_PROVIDER` - Integration provider
- `INTEGRATION` - Integration
- `PROMPT` - AI prompt template
- `USER_FORM_TEMPLATE` - User form template
- `SCHEMA` - Schema definition
- `CLUSTER_CONFIG` - Cluster configuration
- `WEBHOOK` - Webhook
- `API_GATEWAY_SERVICE` - API Gateway service
- `API_GATEWAY_SERVICE_ROUTE` - API Gateway service route

**Example:**
```python
from conductor.client.http.models.target_ref import TargetRef, TargetType

# Workflow definition target
workflow_target = TargetRef(TargetType.WORKFLOW_DEF, "order-processing")

# Task definition target
task_target = TargetRef(TargetType.TASK_DEF, "send-email")

# Application target
app_target = TargetRef(TargetType.APPLICATION, "payment-service")

# Secret target
secret_target = TargetRef(TargetType.SECRET_NAME, "db-password")
```

---

#### AccessType

Enum representing the types of access that can be granted.

**Module:** `conductor.client.orkes.models.access_type`

**Values:**
- `READ` - Read access to view the resource
- `CREATE` - Create new instances
- `UPDATE` - Modify existing resources
- `EXECUTE` - Execute workflows or tasks
- `DELETE` - Delete resources

**Example:**
```python
from conductor.client.orkes.models.access_type import AccessType

# Grant read and execute permissions
permissions = [AccessType.READ, AccessType.EXECUTE]

# Grant full access
full_access = [AccessType.READ, AccessType.CREATE, AccessType.UPDATE, AccessType.EXECUTE, AccessType.DELETE]
```

---

#### MetadataTag

Represents a metadata tag for categorizing and organizing resources.

**Module:** `conductor.client.orkes.models.metadata_tag`

**Properties:**
- `key` (str, required): The tag key/name
- `value` (str, required): The tag value
- `type` (str, auto-set): Always set to "METADATA"

**Use Cases:**
- Categorize applications by environment (dev, staging, prod)
- Tag resources by team, project, or cost center
- Add custom metadata for organizational purposes

**Example:**
```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

# Create tags
tags = [
    MetadataTag("environment", "production"),
    MetadataTag("team", "platform"),
    MetadataTag("cost-center", "engineering"),
    MetadataTag("version", "2.0")
]

# Apply to application
auth_client.set_application_tags(tags, "my-app-id")
```

---

### Application Models

#### ConductorApplication

Represents an application in the Conductor system.

**Module:** `conductor.client.http.models.conductor_application`

**Properties:**
- `id` (str): Unique application identifier
- `name` (str): Application name
- `createTime` (int): Creation timestamp (epoch millis)
- `createdBy` (str): User who created the application
- `updateTime` (int): Last update timestamp
- `updatedBy` (str): User who last updated the application

**Note:** Application tags are managed through separate tagging APIs (`get_application_tags()`, `set_application_tags()`, `delete_application_tags()`) and are not included in the ConductorApplication object itself.

**Example:**
```python
# Get application
app = auth_client.get_application("app-id-123")
print(f"Application: {app.name}")
print(f"Created by: {app.createdBy}")

# Get tags separately
tags = auth_client.get_application_tags("app-id-123")
print(f"Tags: {[f'{tag.key}={tag.value}' for tag in tags] if tags else 'No tags'}")
```

---

#### CreateOrUpdateApplicationRequest

Request model for creating or updating an application.

**Module:** `conductor.client.http.models.create_or_update_application_request`

**Properties:**
- `name` (str, required): Application name (e.g., "Payment Processors")

**Example:**
```python
from conductor.client.http.models.create_or_update_application_request import CreateOrUpdateApplicationRequest

# Create new application
request = CreateOrUpdateApplicationRequest(name="My Service Application")
app = auth_client.create_application(request)
```

---

### Access Key Models

#### AccessKey

Represents an access key for application authentication.

**Module:** `conductor.client.orkes.models.access_key`

**Properties:**
- `id` (str): Access key ID
- `status` (str): Key status - `ACTIVE` or `INACTIVE`
- `createTime` (int): Creation timestamp
- `createdBy` (str): User who created the key

**Example:**
```python
# List access keys
keys = auth_client.get_access_keys("app-id-123")
for key in keys:
    print(f"Key ID: {key.id}")
    print(f"Status: {key.status}")
    print(f"Created: {key.createTime}")
```

---

#### CreatedAccessKey

Represents a newly created access key (includes the secret).

**Module:** `conductor.client.orkes.models.created_access_key`

**Properties:**
- `id` (str): Access key ID
- `secret` (str): **Access key secret (ONLY available at creation time!)**

**⚠️ Important:** The `secret` field is only returned when the access key is first created. You must save it immediately as it cannot be retrieved later!

**Example:**
```python
# Create access key
created_key = auth_client.create_access_key("app-id-123")

# SAVE THESE IMMEDIATELY - secret is only shown once!
key_id = created_key.id
key_secret = created_key.secret

print(f"Key ID: {key_id}")
print(f"Secret: {key_secret}")  # Save this securely!
```

---

### User and Group Models

#### ConductorUser

Represents a user in the Conductor system.

**Module:** `conductor.client.http.models.conductor_user`

**Properties:**
- `id` (str): User ID (usually email)
- `name` (str): Full name
- `roles` (List[str]): Assigned roles
- `groups` (List[str]): Group memberships
- `applicationUser` (bool): Whether this is an application user
- `namespace` (str): User namespace
- `uuid` (str): Unique user identifier
- `contactInformation` (Dict[str, str]): User contact information (email, phone, etc.)

**Example:**
```python
# Get user
user = auth_client.get_user("user@example.com")
print(f"Name: {user.name}")
print(f"Roles: {user.roles}")
print(f"Groups: {user.groups}")
print(f"Namespace: {user.namespace}")
print(f"Contact: {user.contactInformation if user.contactInformation else 'Not provided'}")
```

---

#### UpsertUserRequest

Request model for creating or updating a user.

**Module:** `conductor.client.http.models.upsert_user_request`

**Properties:**
- `name` (str, required): User's full name
- `roles` (List[str], optional): Roles to assign to the user
- `groups` (List[str], optional): IDs of groups the user belongs to

**Available Roles:**
- `USER` - Basic user access
- `ADMIN` - Full administrative access
- `METADATA_MANAGER` - Manage workflow/task definitions
- `WORKFLOW_MANAGER` - Manage workflow executions
- `WORKER` - Worker task execution access

**Example:**
```python
from conductor.client.http.models.upsert_user_request import UpsertUserRequest

# Create user request
request = UpsertUserRequest(
    name="John Doe",
    roles=["USER", "WORKFLOW_MANAGER"],
    groups=["engineering-team", "ops-team"]
)

user = auth_client.upsert_user(request, "john.doe@example.com")
```

---

#### Group

Represents a user group in the Conductor system.

**Module:** `conductor.client.http.models.group`

**Properties:**
- `id` (str): Group ID
- `description` (str): Group description
- `roles` (List[str]): Roles assigned to the group
- `defaultAccess` (Dict): Default access permissions for the group
- `contactInformation` (Dict): Group contact information

**Example:**
```python
# Get group
group = auth_client.get_group("engineering-team")
print(f"Description: {group.description}")
print(f"Roles: {group.roles}")
```

---

#### UpsertGroupRequest

Request model for creating or updating a group.

**Module:** `conductor.client.http.models.upsert_group_request`

**Properties:**
- `description` (str, required): Description of the group
- `roles` (List[str], optional): Roles to assign to the group
- `defaultAccess` (Dict, optional): Default Map<TargetType, Set<Access>> to share permissions
  - Allowed target types: `WORKFLOW_DEF`, `TASK_DEF`, `WORKFLOW_SCHEDULE`

**Example:**
```python
from conductor.client.http.models.upsert_group_request import UpsertGroupRequest

# Create group with default access
request = UpsertGroupRequest(
    description="Engineering Team",
    roles=["USER", "WORKFLOW_MANAGER"],
    defaultAccess={
        "WORKFLOW_DEF": ["READ", "EXECUTE"],
        "TASK_DEF": ["READ"]
    }
)

group = auth_client.upsert_group(request, "engineering-team")
```

---

### Permission Models

#### GrantedPermission

Represents a granted permission showing the target and access levels.

**Module:** `conductor.client.orkes.models.granted_permission`

**Properties:**
- `target` (TargetRef): The resource the permission applies to
- `access` (List[AccessType]): The types of access granted

**Example:**
```python
# Get user permissions
permissions = auth_client.get_granted_permissions_for_user("user@example.com")

for perm in permissions:
    print(f"Target: {perm.target.type}:{perm.target.id}")
    print(f"Access: {[access.name for access in perm.access]}")
```

---

#### AuthorizationRequest

Request model for granting or removing permissions.

**Module:** Internal model used by API

**Properties:**
- `subject` (SubjectRef, required): The subject being granted/removed access
- `target` (TargetRef, required): The target resource
- `access` (List[AccessType], required): The access types to grant/remove

**Example:**
```python
# This is handled internally by grant_permissions() and remove_permissions()
from conductor.client.http.models.target_ref import TargetRef, TargetType
from conductor.client.http.models.subject_ref import SubjectRef, SubjectType
from conductor.client.orkes.models.access_type import AccessType

target = TargetRef(TargetType.WORKFLOW_DEF, "my-workflow")
subject = SubjectRef(SubjectType.USER, "user@example.com")
access = [AccessType.READ, AccessType.EXECUTE]

auth_client.grant_permissions(subject, target, access)
```

---

### Role Models

#### Role

Represents a role with associated permissions.

**Properties:**
- `name` (str): Role name
- `permissions` (List[Dict]): List of permissions
  - Each permission has:
    - `resource` (str): Resource type (e.g., "WORKFLOW_DEF")
    - `actions` (List[str]): Allowed actions (e.g., ["READ", "EXECUTE"])

**Example:**
```python
# Get role
role = auth_client.get_role("workflow-operator")
print(f"Role: {role['name']}")
print(f"Permissions: {role['permissions']}")
```

---

#### CreateOrUpdateRoleRequest

Request model for creating or updating a custom role.

**Properties:**
- `name` (str, required): Role name
- `permissions` (List[Dict], required): List of permission definitions

**Example:**
```python
# Create custom role
role_request = {
    "name": "data-analyst",
    "description": "Can read and execute data workflows",
    "permissions": [
        {
            "resource": "WORKFLOW_DEF",
            "actions": ["READ", "EXECUTE"]
        },
        {
            "resource": "TASK_DEF",
            "actions": ["READ"]
        }
    ]
}

role = auth_client.create_role(role_request)
```

---

### Token Models

#### GenerateTokenRequest

Request model for generating a JWT token.

**Properties:**
- `keyId` (str, required): Access key ID
- `keySecret` (str, required): Access key secret
- `expiration` (int, optional): Token expiration time in seconds

**Example:**
```python
# Generate JWT token
token_response = auth_client.generate_token(
    key_id="your-key-id",
    key_secret="your-key-secret"
)

jwt_token = token_response.get('token')
```

---

### Gateway Models

#### AuthenticationConfig

Configuration for API Gateway authentication.

**Module:** `conductor.client.http.models.authentication_config`

**Properties:**
- `id` (str, required): Configuration ID
- `applicationId` (str, required): Associated application ID
- `authenticationType` (str, required): Type of authentication - one of: `NONE`, `API_KEY`, `OIDC`
- `apiKeys` (List[str]): List of API keys (when using API_KEY authentication)
- `audience` (str): OAuth audience
- `conductorToken` (str): Conductor token for authentication
- `createdBy` (str): User who created the configuration
- `fallbackToDefaultAuth` (bool): Use default auth as fallback
- `issuerUri` (str): OAuth issuer URI (for OIDC authentication)
- `passthrough` (bool): Whether to pass auth through
- `tokenInWorkflowInput` (bool): Include token in workflow input
- `updatedBy` (str): User who last updated the configuration

**Example:**
```python
# Create gateway auth config with API_KEY authentication
auth_config = {
    "id": "my-gateway-auth",
    "authenticationType": "API_KEY",
    "applicationId": "app-id-123",
    "apiKeys": ["key1", "key2"],
    "fallbackToDefaultAuth": False,
    "tokenInWorkflowInput": True
}

config = auth_client.create_gateway_auth_config(auth_config)

# Create gateway auth config with OIDC authentication
oidc_config = {
    "id": "my-oidc-auth",
    "authenticationType": "OIDC",
    "applicationId": "app-id-123",
    "issuerUri": "https://auth.example.com",
    "audience": "https://api.example.com",
    "passthrough": True
}

config = auth_client.create_gateway_auth_config(oidc_config)
```

---

### Model Import Reference

Quick reference for importing all models:

```python
# Core authorization models
from conductor.client.http.models.subject_ref import SubjectRef, SubjectType
from conductor.client.http.models.target_ref import TargetRef, TargetType
from conductor.client.orkes.models.access_type import AccessType
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.orkes.models.granted_permission import GrantedPermission

# Access key models
from conductor.client.orkes.models.access_key import AccessKey
from conductor.client.orkes.models.created_access_key import CreatedAccessKey

# User and group models
from conductor.client.http.models.conductor_user import ConductorUser
from conductor.client.http.models.upsert_user_request import UpsertUserRequest
from conductor.client.http.models.group import Group
from conductor.client.http.models.upsert_group_request import UpsertGroupRequest

# Application models
from conductor.client.http.models.conductor_application import ConductorApplication
from conductor.client.http.models.create_or_update_application_request import CreateOrUpdateApplicationRequest
```

---

## Complete Example: Setting Up RBAC

Here's a complete example showing how to set up RBAC for a workflow:

```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_authorization_client import OrkesAuthorizationClient
from conductor.client.http.models.upsert_user_request import UpsertUserRequest
from conductor.client.http.models.upsert_group_request import UpsertGroupRequest
from conductor.client.http.models.target_ref import TargetRef, TargetType
from conductor.client.http.models.subject_ref import SubjectRef, SubjectType
from conductor.client.orkes.models.access_type import AccessType

# Initialize
configuration = Configuration()
auth_client = OrkesAuthorizationClient(configuration)

# 1. Create users
developer = auth_client.upsert_user(
    UpsertUserRequest(name="Developer User", roles=["USER"]),
    "developer@example.com"
)

operator = auth_client.upsert_user(
    UpsertUserRequest(name="Operator User", roles=["USER"]),
    "operator@example.com"
)

# 2. Create group
engineering = auth_client.upsert_group(
    UpsertGroupRequest(description="Engineering Team", roles=["USER"]),
    "engineering-team"
)

# 3. Add users to group
auth_client.add_users_to_group("engineering-team", [
    "developer@example.com",
    "operator@example.com"
])

# 4. Grant permissions to group on workflow
workflow_target = TargetRef(TargetType.WORKFLOW_DEF, "order-processing")
group_subject = SubjectRef(SubjectType.GROUP, "engineering-team")

auth_client.grant_permissions(
    group_subject,
    workflow_target,
    [AccessType.READ, AccessType.EXECUTE]
)

# 5. Grant additional permissions to developer
developer_subject = SubjectRef(SubjectType.USER, "developer@example.com")
auth_client.grant_permissions(
    developer_subject,
    workflow_target,
    [AccessType.UPDATE]  # Developers can also modify
)

# 6. Verify permissions
permissions = auth_client.get_permissions(workflow_target)
print("Workflow permissions:")
for access_type, subjects in permissions.items():
    print(f"  {access_type}:")
    for subject in subjects:
        print(f"    - {subject.type}: {subject.id}")

# 7. Check specific user permissions
can_update = auth_client.check_permissions(
    user_id="developer@example.com",
    target_type="WORKFLOW_DEF",
    target_id="order-processing"
)
print(f"Developer can update: {can_update}")
```

---

## Best Practices

1. **Principle of Least Privilege**: Grant only the minimum permissions required for users/groups to perform their tasks.

2. **Use Groups**: Assign permissions to groups rather than individual users for easier management.

3. **Secure Access Keys**:
   - Store access key secrets securely (they're only shown once at creation)
   - Rotate access keys regularly
   - Use inactive status instead of deletion when temporarily revoking access

4. **Audit Regularly**: Use `get_granted_permissions_for_user()` and `get_granted_permissions_for_group()` to audit access.

5. **Role-Based Organization**:
   - Use system roles for standard permissions
   - Create custom roles for specific use cases
   - Document custom role purposes

6. **Testing**: Always verify permissions with `check_permissions()` before granting production access.

7. **Cleanup**: Remove unused users, groups, and applications to maintain security.

---

## Error Handling

All authorization methods may raise exceptions. Always use proper error handling:

```python
from conductor.client.http.rest import RestException

try:
    user = auth_client.get_user("user@example.com")
except RestException as e:
    if e.status == 404:
        print("User not found")
    elif e.status == 403:
        print("Access denied")
    else:
        print(f"Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Complete Working Example

### Authorization Journey - All 49 APIs in Action

For a comprehensive implementation that demonstrates all authorization APIs in a single, cohesive narrative, see:

📚 **[examples/authorization_journey.py](../../examples/authorization_journey.py)**

This complete example includes:

✅ **All 49 Authorization APIs** - 100% coverage with proper model classes
✅ **Real-World Scenario** - E-commerce platform RBAC setup
✅ **Progressive Learning** - 12 chapters building on each other
✅ **Update Operations** - Demonstrates CREATE, READ, UPDATE, DELETE for all entities
✅ **Custom Roles** - Creating and managing custom roles with actual permissions
✅ **Error Handling** - Graceful fallbacks and clear error messages
✅ **Cleanup** - Automatic resource cleanup (can be disabled with `--no-cleanup`)

#### Running the Example

```bash
# Standard execution with automatic cleanup
python3 examples/authorization_journey.py

# Keep resources for inspection
python3 examples/authorization_journey.py --no-cleanup

# Run as pytest
python3 -m pytest examples/authorization_journey.py -v
```

#### Coverage Verification

See [examples/authorization_coverage.md](../../examples/authorization_coverage.md) for detailed verification that all APIs are covered.

---

## See Also

- [Configuration Guide](../README.md)
- [Workflow Management](./WORKFLOW.md)
- [Task Management](./TASK.md)
