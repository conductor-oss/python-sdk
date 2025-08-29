# Access Control Management

## Authorization Client

### Initialization
```python
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_authorization_client import OrkesAuthorizationClient

configuration = Configuration()

authorization_client = OrkesAuthorizationClient(configuration)
```

### Application Management

#### Creating Application
Creates an application and returns a ConductorApplication object.

```python
from conductor.client.http.models import CreateOrUpdateApplicationRequest
from conductor.client.orkes.orkes_authorization_client import OrkesAuthorizationClient
from conductor.client.configuration.configuration import Configuration

configuration = Configuration()
authorization_client = OrkesAuthorizationClient(configuration)

request = CreateOrUpdateApplicationRequest(name="APPLICATION_NAME")
app = authorization_client.create_application(request)
application_id = app.id
```

#### Get Application

```python
app = authorization_client.get_application(application_id)
```

#### List All Applications

```python
apps = authorization_client.list_applications()
```

#### Update Application
Updates an application and returns a ConductorApplication object.

```python
request = CreateOrUpdateApplicationRequest("APPLICATION_NAME")
updated_app = authorization_client.update_application(request, application_id)
```

#### Delete Application

```python
authorization_client.delete_application(application_id)
```

#### Add a role for an Application user
Add one of the roles out of ["USER", "ADMIN", "METADATA_MANAGER", "WORKFLOW_MANAGER", "USER_READ_ONLY"]
to an application user.

```python
authorization_client.add_role_to_application_user(application_id, "USER")
```

#### Remove a role assigned to an Application user

```python
authorization_client.remove_role_from_application_user(application_id, "USER")
```

#### Set Application tags

```python
from conductor.client.orkes.models.metadata_tag import MetadataTag

tags = [
    MetadataTag("auth_tag", "val"), MetadataTag("auth_tag_2", "val2")
]
authorization_client.get_application_tags(tags, application_id)
```

#### Get Application tags

```python
tags = authorization_client.get_application_tags(application_id)
```

#### Delete Application tags

```python
tags = [
    MetadataTag("auth_tag", "val"), MetadataTag("auth_tag_2", "val2")
]
authorization_client.delete_application_tags(tags, application_id)
```

### Access Key Management

#### Create Access Key
Creates an access key for the specified application and returns a CreatedAccessKey object.
The SECRET for this access key is available in the returned object. This is the only time
when the secret for this newly created access key can be retrieved and saved.

```python
from conductor.client.orkes.models.created_access_key import CreatedAccessKey

created_access_key = authorization_client.create_access_key(application_id)
```

#### Get Access Key
Retrieves all access keys for the specified application as List[AccessKey].

```python
from conductor.client.orkes.models.access_key import AccessKey

access_keys = authorization_client.get_access_keys(application_id)
```

#### Enabling / Disabling Access Key
Toggle access key status between ACTIVE and INACTIVE.

```python
 access_key = authorization_client.toggle_access_key_status(application_id, created_access_key.id)
```

#### Delete Acccess Key

```python
authorization_client.delete_access_key(application_id, created_access_key.id)
```

### User Management

#### Create or Update User
Creates or updates a user and returns a ConductorUser object.

```python
from conductor.client.http.models.upsert_user_request import UpsertUserRequest
from conductor.client.http.models import ConductorUser

user_id = 'test.user@company.com'
user_name = "Test User"
roles = ["USER"]
req = UpsertUserRequest(user_name, roles)
user = authorization_client.upsert_user(req, user_id)
```

#### Get User

```python
user = authorization_client.get_user(user_id)
```

#### List All Users

```python
users = authorization_client.list_users()
```

#### Delete User

```python
authorization_client.delete_user(user_id)
```

### Group Management

#### Create or Update a Group
Creates or updates a user group and returns a Group object.

```python
from conductor.client.http.models import UpsertGroupRequest, Group

group_id = 'test_group'
group_name = "Test Group"
group_user_roles = ["USER"]
req = UpsertGroupRequest("Integration Test Group", group_user_roles)
group = authorization_client.upsert_group(req, group_id)
```

#### Get Group

```python
group = authorization_client.get_group(group_id)
```

#### List All Groups
Retrives all groups as a List[Group]

```python
users = authorization_client.list_groups()
```

#### Delete Group

```python
authorization_client.delete_group(group_id)
```

#### Add users to a Group

```python
 authorization_client.add_user_to_group(group_id, user_id)
```

#### Get all users in a Group
Retrives all users in a group as List[ConductorUser]

```python
users = self.authorization_client.get_users_in_group(group_id)
```

#### Remove users from a group

```python
authorization_client.remove_user_from_group(group_id, user_id)
```

### Permission Management

#### Grant Permissions
Grants a set of accesses to the specified Subject for a given Target.

```python
from conductor.client.http.models import TargetRef, SubjectRef
from conductor.shared.http.enums.target_type import TargetType
from conductor.shared.http.enums.subject_type import SubjectType
from conductor.client.orkes.models.access_type import AccessType

target = TargetRef(TargetType.WORKFLOW_DEF, "TEST_WORKFLOW")
subject_group = SubjectRef(SubjectType.GROUP, group_id)
access_group = [AccessType.EXECUTE]

subject_user = SubjectRef(SubjectType.USER, user_id)
access_user = [AccessType.EXECUTE, AccessType.READ]

authorization_client.grant_permissions(subject_group, target, access_group)
authorization_client.grant_permissions(subject_user, target, access_user)
```

#### Get Permissions for a Target
Given the target, returns all permissions associated with it as a Dict[str, List[SubjectRef]].
In the returned dictionary, key is AccessType and value is a list of subjects.

```python
from conductor.client.http.models import TargetRef
from conductor.shared.http.enums.target_type import TargetType

target = TargetRef(TargetType.WORKFLOW_DEF, WORKFLOW_NAME)
target_permissions = authorization_client.get_permissions(target)
```

#### Get Permissions granted to a Group
Given a group id, returns all the permissions granted to a group as List[GrantedPermission].

```python
from conductor.client.orkes.models.granted_permission import GrantedPermission

group_permissions = authorization_client.get_granted_permissions_for_group(group_id)
```

#### Get Permissions granted to a User
Given a user id, returns all the permissions granted to a user as List[GrantedPermission].

```python
from conductor.client.orkes.models.granted_permission import GrantedPermission

user_permissions = authorization_client.get_granted_permissions_for_user(user_id)
```

#### Remove Permissions
Removes a set of accesses from a specified Subject for a given Target.

```python
from conductor.client.http.models import TargetRef, SubjectRef
from conductor.shared.http.enums.target_type import TargetType
from conductor.shared.http.enums.subject_type import SubjectType
from conductor.client.orkes.models.access_type import AccessType

target = TargetRef(TargetType.WORKFLOW_DEF, "TEST_WORKFLOW")
subject_group = SubjectRef(SubjectType.GROUP, group_id)
access_group = [AccessType.EXECUTE]

subject_user = SubjectRef(SubjectType.USER, user_id)
access_user = [AccessType.EXECUTE, AccessType.READ]

authorization_client.remove_permissions(subject_group, target, access_group)
authorization_client.remove_permissions(subject_user, target, access_user)
```
