import os
import uuid

import pytest
import httpx

from conductor.client.http.models.create_or_update_application_request import \
    CreateOrUpdateApplicationRequestAdapter as CreateOrUpdateApplicationRequest
from conductor.client.http.models.subject_ref import \
    SubjectRefAdapter as SubjectRef
from conductor.client.http.models.target_ref import \
    TargetRefAdapter as TargetRef
from conductor.client.http.models.upsert_group_request import \
    UpsertGroupRequestAdapter as UpsertGroupRequest
from conductor.client.http.models.upsert_user_request import \
    UpsertUserRequestAdapter as UpsertUserRequest
from conductor.client.configuration.configuration import Configuration
from conductor.client.codegen.rest import ApiException
from conductor.client.orkes.models.access_key_status import AccessKeyStatus
from conductor.client.orkes.models.access_type import AccessType
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.orkes.orkes_authorization_client import \
    OrkesAuthorizationClient
from conductor.shared.http.enums.subject_type import SubjectType
from conductor.shared.http.enums.target_type import TargetType


class TestOrkesAuthorizationClientIntegration:
    """
    Integration tests for OrkesAuthorizationClient.

    Environment Variables:
    - CONDUCTOR_SERVER_URL: Base URL for Conductor server (default: http://localhost:8080/api)
    - CONDUCTOR_AUTH_KEY: Authentication key for Orkes
    - CONDUCTOR_AUTH_SECRET: Authentication secret for Orkes
    - CONDUCTOR_UI_SERVER_URL: UI server URL (optional)
    - CONDUCTOR_TEST_TIMEOUT: Test timeout in seconds (default: 30)
    - CONDUCTOR_TEST_CLEANUP: Whether to cleanup test resources (default: true)
    """

    @pytest.fixture(scope="class")
    def configuration(self) -> Configuration:
        """Create configuration from environment variables."""
        config = Configuration()
        config.http_connection = httpx.Client(
            timeout=httpx.Timeout(600.0),
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=1, max_connections=1),
            http2=True
        )
        config.debug = os.getenv("CONDUCTOR_DEBUG", "false").lower() == "true"
        config.apply_logging_config()
        return config

    @pytest.fixture(scope="class")
    def auth_client(self, configuration: Configuration) -> OrkesAuthorizationClient:
        """Create OrkesAuthorizationClient instance."""
        return OrkesAuthorizationClient(configuration)

    @pytest.fixture(scope="class")
    def test_suffix(self) -> str:
        """Generate unique suffix for test resources."""
        return str(uuid.uuid4())[:8]

    @pytest.fixture(scope="class")
    def test_application_name(self, test_suffix: str) -> str:
        """Generate test application name."""
        return f"test_app_{test_suffix}"

    @pytest.fixture(scope="class")
    def test_user_id(self, test_suffix: str) -> str:
        """Generate test user ID."""
        return f"test_user_{test_suffix}@example.com"

    @pytest.fixture(scope="class")
    def test_group_id(self, test_suffix: str) -> str:
        """Generate test group ID."""
        return f"test_group_{test_suffix}"

    @pytest.fixture(scope="class")
    def test_workflow_name(self, test_suffix: str) -> str:
        """Generate test workflow name."""
        return f"test_workflow_{test_suffix}"

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_application_lifecycle(
        self, auth_client: OrkesAuthorizationClient, test_application_name: str
    ):
        """Test complete application lifecycle: create, read, update, delete."""
        try:
            create_request = CreateOrUpdateApplicationRequest(test_application_name)
            created_app = auth_client.create_application(create_request)

            assert created_app.name == test_application_name
            assert created_app.id is not None

            retrieved_app = auth_client.get_application(created_app.id)
            assert retrieved_app.id == created_app.id
            assert retrieved_app.name == test_application_name

            applications = auth_client.list_applications()
            app_ids = [app.id for app in applications]
            assert created_app.id in app_ids

            updated_name = f"{test_application_name}_updated"
            update_request = CreateOrUpdateApplicationRequest(updated_name)
            updated_app = auth_client.update_application(update_request, created_app.id)
            assert updated_app.name == updated_name

            tags = [
                MetadataTag("environment", "test"),
                MetadataTag("owner", "integration_test"),
            ]
            auth_client.set_application_tags(tags, created_app.id)
            retrieved_tags = auth_client.get_application_tags(created_app.id)
            assert len(retrieved_tags) == 2
            tag_keys = [tag.key for tag in retrieved_tags]
            assert "environment" in tag_keys
            assert "owner" in tag_keys

            created_key = auth_client.create_access_key(created_app.id)
            assert created_key.id is not None
            assert created_key.secret is not None

            access_keys = auth_client.get_access_keys(created_app.id)
            assert len(access_keys) >= 1
            key_ids = [key.id for key in access_keys]
            assert created_key.id in key_ids

            toggled_key = auth_client.toggle_access_key_status(
                created_app.id, created_key.id
            )
            assert toggled_key.status == AccessKeyStatus.INACTIVE

            active_key = auth_client.toggle_access_key_status(
                created_app.id, created_key.id
            )
            assert active_key.status == AccessKeyStatus.ACTIVE

            auth_client.delete_access_key(created_app.id, created_key.id)

            auth_client.add_role_to_application_user(created_app.id, "USER")
            app_user_id = f"app:{created_app.id}"
            app_user = auth_client.get_user(app_user_id)
            user_roles = [role.name for role in app_user.roles]
            assert "USER" in user_roles

            auth_client.remove_role_from_application_user(created_app.id, "USER")
            app_user = auth_client.get_user(app_user_id)
            user_roles = [role.name for role in app_user.roles]
            assert "USER" not in user_roles

        finally:
            auth_client.delete_application(created_app.id)

            with pytest.raises(ApiException) as exc_info:
                auth_client.get_application(created_app.id)
            assert exc_info.value.code == 404

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_user_lifecycle(
        self, auth_client: OrkesAuthorizationClient, test_user_id: str
    ):
        """Test complete user lifecycle: create, read, update, delete."""
        try:
            create_request = UpsertUserRequest(name="Test User", roles=["USER"])
            created_user = auth_client.upsert_user(create_request, test_user_id)

            assert created_user.id == test_user_id
            assert created_user.name == "Test User"

            retrieved_user = auth_client.get_user(test_user_id)
            assert retrieved_user.id == test_user_id
            assert retrieved_user.name == "Test User"

            users = auth_client.list_users()
            user_ids = [user.id for user in users]
            assert test_user_id in user_ids

            update_request = UpsertUserRequest(
                name="Updated Test User", roles=["USER", "ADMIN"]
            )
            updated_user = auth_client.upsert_user(update_request, test_user_id)
            assert updated_user.name == "Updated Test User"
            user_roles = [role.name for role in updated_user.roles]
            assert "USER" in user_roles
            assert "ADMIN" in user_roles

        finally:
            auth_client.delete_user(test_user_id)

            with pytest.raises(ApiException) as exc_info:
                auth_client.get_user(test_user_id)
            assert exc_info.value.code == 404

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_group_lifecycle(
        self,
        auth_client: OrkesAuthorizationClient,
        test_group_id: str,
        test_user_id: str,
    ):
        """Test complete group lifecycle: create, read, update, delete."""
        try:
            user_create_request = UpsertUserRequest(name="Test User", roles=["USER"])
            created_user = auth_client.upsert_user(user_create_request, test_user_id)
            assert created_user.id == test_user_id
            assert created_user.name == "Test User"

            create_request = UpsertGroupRequest(
                description="Test Group", roles=["USER"]
            )
            created_group = auth_client.upsert_group(create_request, test_group_id)

            assert created_group.id == test_group_id
            assert created_group.description == "Test Group"

            retrieved_group = auth_client.get_group(test_group_id)
            assert retrieved_group.id == test_group_id
            assert retrieved_group.description == "Test Group"

            groups = auth_client.list_groups()
            group_ids = [group.id for group in groups]
            assert test_group_id in group_ids

            auth_client.add_user_to_group(test_group_id, test_user_id)
            group_users = auth_client.get_users_in_group(test_group_id)
            user_ids = [user.id for user in group_users]
            assert test_user_id in user_ids

            auth_client.remove_user_from_group(test_group_id, test_user_id)
            group_users = auth_client.get_users_in_group(test_group_id)
            user_ids = [user.id for user in group_users]
            assert test_user_id not in user_ids

        finally:
            auth_client.delete_group(test_group_id)
            auth_client.delete_user(test_user_id)

            with pytest.raises(ApiException) as exc_info:
                auth_client.get_group(test_group_id)
            assert exc_info.value.code == 404

            with pytest.raises(ApiException) as exc_info:
                auth_client.get_user(test_user_id)
            assert exc_info.value.code == 404

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_permissions_lifecycle(
        self,
        auth_client: OrkesAuthorizationClient,
        test_user_id: str,
        test_group_id: str,
        test_workflow_name: str,
    ):
        """Test permissions lifecycle: grant, retrieve, remove."""
        try:
            user_create_request = UpsertUserRequest(name="Test User", roles=["USER"])
            created_user = auth_client.upsert_user(user_create_request, test_user_id)
            assert created_user.id == test_user_id
            assert created_user.name == "Test User"

            create_request = UpsertGroupRequest(
                description="Test Group", roles=["USER"]
            )
            created_group = auth_client.upsert_group(create_request, test_group_id)

            assert created_group.id == test_group_id
            assert created_group.description == "Test Group"

            target = TargetRef(test_workflow_name, TargetType.WORKFLOW_DEF)

            user_subject = SubjectRef(test_user_id, SubjectType.USER)
            group_subject = SubjectRef(test_group_id, SubjectType.GROUP)

            user_access = [AccessType.EXECUTE, AccessType.READ]
            auth_client.grant_permissions(user_subject, target, user_access)

            group_access = [AccessType.READ]
            auth_client.grant_permissions(group_subject, target, group_access)

            target_permissions = auth_client.get_permissions(target)

            assert AccessType.EXECUTE in target_permissions
            assert AccessType.READ in target_permissions

            user_perms = target_permissions[AccessType.EXECUTE]
            assert any(
                subject.id == test_user_id and subject.type == SubjectType.USER
                for subject in user_perms
            )

            read_perms = target_permissions[AccessType.READ]
            assert any(
                subject.id == test_user_id and subject.type == SubjectType.USER
                for subject in read_perms
            )
            assert any(
                subject.id == test_group_id and subject.type == SubjectType.GROUP
                for subject in read_perms
            )

            user_granted_perms = auth_client.get_granted_permissions_for_user(
                test_user_id
            )
            assert len(user_granted_perms) >= 1
            user_target_perms = [
                perm
                for perm in user_granted_perms
                if perm.target.id == test_workflow_name
            ]
            assert len(user_target_perms) >= 1
            assert AccessType.EXECUTE in user_target_perms[0].access
            assert AccessType.READ in user_target_perms[0].access

            group_granted_perms = auth_client.get_granted_permissions_for_group(
                test_group_id
            )
            assert len(group_granted_perms) >= 1
            group_target_perms = [
                perm
                for perm in group_granted_perms
                if perm.target.id == test_workflow_name
            ]
            assert len(group_target_perms) >= 1
            assert AccessType.READ in group_target_perms[0].access

            auth_client.remove_permissions(user_subject, target, user_access)
            auth_client.remove_permissions(group_subject, target, group_access)

            target_permissions_after = auth_client.get_permissions(target)
            if AccessType.EXECUTE in target_permissions_after:
                user_perms_after = target_permissions_after[AccessType.EXECUTE]
                assert not any(
                    subject.id == test_user_id and subject.type == SubjectType.USER
                    for subject in user_perms_after
                )

            if AccessType.READ in target_permissions_after:
                read_perms_after = target_permissions_after[AccessType.READ]
                assert not any(
                    subject.id == test_user_id and subject.type == SubjectType.USER
                    for subject in read_perms_after
                )
                assert not any(
                    subject.id == test_group_id and subject.type == SubjectType.GROUP
                    for subject in read_perms_after
                )

        finally:
            auth_client.delete_group(test_group_id)
            auth_client.delete_user(test_user_id)

            with pytest.raises(ApiException) as exc_info:
                auth_client.get_group(test_group_id)
            assert exc_info.value.code == 404

            with pytest.raises(ApiException) as exc_info:
                auth_client.get_user(test_user_id)
            assert exc_info.value.code == 404

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_error_handling(self, auth_client: OrkesAuthorizationClient):
        """Test error handling for non-existent resources."""
        non_existent_id = "non_existent_" + str(uuid.uuid4())

        with pytest.raises(ApiException) as exc_info:
            auth_client.get_application(non_existent_id)
        assert exc_info.value.code == 404

        with pytest.raises(ApiException) as exc_info:
            auth_client.get_user(non_existent_id)
        assert exc_info.value.code == 404

        with pytest.raises(ApiException) as exc_info:
            auth_client.get_group(non_existent_id)
        assert exc_info.value.code == 404

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_concurrent_operations(
        self, auth_client: OrkesAuthorizationClient, test_suffix: str
    ):
        """Test concurrent operations on multiple resources."""
        try:
            import threading
            import time

            results = []
            errors = []
            created_apps = []
            cleanup_lock = threading.Lock()

            def create_and_delete_app(app_suffix: str):
                app_id = None
                try:
                    app_name = f"concurrent_app_{app_suffix}"
                    create_request = CreateOrUpdateApplicationRequest(app_name)
                    created_app = auth_client.create_application(create_request)
                    app_id = created_app.id

                    with cleanup_lock:
                        created_apps.append(app_id)

                    time.sleep(0.1)

                    retrieved_app = auth_client.get_application(created_app.id)
                    assert retrieved_app.name == app_name

                    if os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true":
                        try:
                            auth_client.delete_application(created_app.id)
                            with cleanup_lock:
                                if app_id in created_apps:
                                    created_apps.remove(app_id)
                        except Exception as cleanup_error:
                            print(
                                f"Warning: Failed to cleanup app {app_id} in thread: {str(cleanup_error)}"
                            )

                    results.append(f"app_{app_suffix}_success")
                except Exception as e:
                    errors.append(f"app_{app_suffix}_error: {str(e)}")
                    if app_id and app_id not in created_apps:
                        with cleanup_lock:
                            created_apps.append(app_id)

            threads = []
            for i in range(3):
                thread = threading.Thread(
                    target=create_and_delete_app, args=(f"{test_suffix}_{i}",)
                )
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            assert (
                len(results) == 3
            ), f"Expected 3 successful operations, got {len(results)}. Errors: {errors}"
            assert len(errors) == 0, f"Unexpected errors: {errors}"

        finally:
            for app_id in created_apps:
                try:
                    auth_client.delete_application(app_id)
                except Exception as e:
                    print(f"Warning: Failed to delete app {app_id}: {str(e)}")

            remaining_apps = []
            for app_id in created_apps:
                try:
                    auth_client.get_application(app_id)
                    remaining_apps.append(app_id)
                except ApiException as e:
                    if e.code == 404:
                        pass
                    else:
                        remaining_apps.append(app_id)
                except Exception:
                    remaining_apps.append(app_id)

            if remaining_apps:
                print(
                    f"Warning: {len(remaining_apps)} applications could not be verified as deleted: {remaining_apps}"
                )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_complex_user_management_flow(
        self, auth_client: OrkesAuthorizationClient, test_suffix: str
    ):
        created_resources = {
            "applications": [],
            "users": [],
            "groups": [],
            "access_keys": [],
            "permissions": [],
        }

        try:
            main_app_name = f"main_app_{test_suffix}"
            main_app_request = CreateOrUpdateApplicationRequest(main_app_name)
            main_app = auth_client.create_application(main_app_request)
            created_resources["applications"].append(main_app.id)

            departments = ["engineering", "marketing", "finance", "hr"]
            department_apps = {}

            for dept in departments:
                dept_app_name = f"{dept}_app_{test_suffix}"
                dept_app_request = CreateOrUpdateApplicationRequest(dept_app_name)
                dept_app = auth_client.create_application(dept_app_request)
                department_apps[dept] = dept_app
                created_resources["applications"].append(dept_app.id)

                dept_tags = [
                    MetadataTag("department", dept),
                    MetadataTag("parent_app", main_app.id),
                    MetadataTag("environment", "test"),
                ]
                auth_client.set_application_tags(dept_tags, dept_app.id)

            admin_users = {}
            admin_roles = ["ADMIN"]

            for role in admin_roles:
                admin_id = f"admin_{role.lower()}_{test_suffix}@company.com"
                admin_request = UpsertUserRequest(name=f"Admin {role}", roles=[role])
                admin_user = auth_client.upsert_user(admin_request, admin_id)
                admin_users[role] = admin_user
                created_resources["users"].append(admin_id)

            manager_users = {}
            for dept in departments:
                manager_id = f"manager_{dept}_{test_suffix}@company.com"
                manager_request = UpsertUserRequest(
                    name=f"Manager {dept.title()}", roles=["METADATA_MANAGER", "USER"]
                )
                manager_user = auth_client.upsert_user(manager_request, manager_id)
                manager_users[dept] = manager_user
                created_resources["users"].append(manager_id)

            employee_users = {}
            for dept in departments:
                dept_employees = []
                for i in range(3):
                    emp_id = f"emp_{dept}_{i}_{test_suffix}@company.com"
                    emp_request = UpsertUserRequest(
                        name=f"Employee {i} {dept.title()}", roles=["USER"]
                    )
                    emp_user = auth_client.upsert_user(emp_request, emp_id)
                    dept_employees.append(emp_user)
                    created_resources["users"].append(emp_id)
                employee_users[dept] = dept_employees

            main_groups = {}
            group_roles = ["worker", "user", "metadata_manager", "workflow_manager"]

            for role in group_roles:
                group_id = f"group_{role}_{test_suffix}"
                group_request = UpsertGroupRequest(
                    description=f"Group {role.title()}", roles=[role.upper()]
                )
                group = auth_client.upsert_group(group_request, group_id)
                main_groups[role] = group
                created_resources["groups"].append(group_id)

            dept_groups = {}
            for dept in departments:
                dept_group_id = f"group_{dept}_{test_suffix}"
                dept_group_request = UpsertGroupRequest(
                    description=f"Group {dept.title()}", roles=["USER"]
                )
                dept_group = auth_client.upsert_group(dept_group_request, dept_group_id)
                dept_groups[dept] = dept_group
                created_resources["groups"].append(dept_group_id)

            for admin_user in admin_users.values():
                auth_client.add_user_to_group(main_groups["worker"].id, admin_user.id)

            for dept, manager_user in manager_users.items():
                auth_client.add_user_to_group(
                    main_groups["metadata_manager"].id, manager_user.id
                )
                auth_client.add_user_to_group(dept_groups[dept].id, manager_user.id)

            for dept, employees in employee_users.items():
                for emp_user in employees:
                    auth_client.add_user_to_group(main_groups["user"].id, emp_user.id)
                    auth_client.add_user_to_group(dept_groups[dept].id, emp_user.id)

            main_app_key = auth_client.create_access_key(main_app.id)
            created_resources["access_keys"].append((main_app.id, main_app_key.id))

            for dept, dept_app in department_apps.items():
                dept_key = auth_client.create_access_key(dept_app.id)
                created_resources["access_keys"].append((dept_app.id, dept_key.id))

                if dept in ["engineering", "marketing"]:
                    auth_client.toggle_access_key_status(dept_app.id, dept_key.id)

            workflows = {
                "main": f"main_workflow_{test_suffix}",
                "engineering": f"eng_workflow_{test_suffix}",
                "marketing": f"marketing_workflow_{test_suffix}",
                "finance": f"finance_workflow_{test_suffix}",
                "hr": f"hr_workflow_{test_suffix}",
            }

            for workflow_name in workflows.values():
                workflow_target = TargetRef(workflow_name, TargetType.WORKFLOW_DEF)

                exec_subject = SubjectRef(main_groups["worker"].id, SubjectType.GROUP)
                auth_client.grant_permissions(
                    exec_subject,
                    workflow_target,
                    [AccessType.EXECUTE, AccessType.READ, AccessType.CREATE],
                )
                created_resources["permissions"].append(
                    (
                        exec_subject,
                        workflow_target,
                        [AccessType.EXECUTE, AccessType.READ, AccessType.CREATE],
                    )
                )

                manager_subject = SubjectRef(
                    main_groups["metadata_manager"].id, SubjectType.GROUP
                )
                auth_client.grant_permissions(
                    manager_subject,
                    workflow_target,
                    [AccessType.EXECUTE, AccessType.READ],
                )
                created_resources["permissions"].append(
                    (
                        manager_subject,
                        workflow_target,
                        [AccessType.EXECUTE, AccessType.READ],
                    )
                )

                emp_subject = SubjectRef(main_groups["user"].id, SubjectType.GROUP)
                auth_client.grant_permissions(
                    emp_subject, workflow_target, [AccessType.READ]
                )
                created_resources["permissions"].append(
                    (emp_subject, workflow_target, [AccessType.READ])
                )

            for dept in departments:
                dept_workflow = workflows[dept]
                dept_target = TargetRef(dept_workflow, TargetType.WORKFLOW_DEF)
                dept_group_subject = SubjectRef(dept_groups[dept].id, SubjectType.GROUP)

                auth_client.grant_permissions(
                    dept_group_subject,
                    dept_target,
                    [AccessType.CREATE, AccessType.EXECUTE, AccessType.READ],
                )
                created_resources["permissions"].append(
                    (
                        dept_group_subject,
                        dept_target,
                        [AccessType.CREATE, AccessType.EXECUTE, AccessType.READ],
                    )
                )

            all_apps = auth_client.list_applications()
            app_ids = [app.id for app in all_apps]
            for app_id in created_resources["applications"]:
                assert app_id in app_ids, f"Application {app_id} not found in list"

            all_users = auth_client.list_users()
            user_ids = [user.id for user in all_users]
            for user_id in created_resources["users"]:
                assert user_id in user_ids, f"User {user_id} not found in list"

            all_groups = auth_client.list_groups()
            group_ids = [group.id for group in all_groups]
            for group_id in created_resources["groups"]:
                assert group_id in group_ids, f"Group {group_id} not found in list"

            for dept, manager_user in manager_users.items():
                group_users = auth_client.get_users_in_group(dept_groups[dept].id)
                group_user_ids = [user.id for user in group_users]
                assert (
                    manager_user.id in group_user_ids
                ), f"Manager {manager_user.id} not in {dept} group"

            for workflow_name in workflows.values():
                workflow_target = TargetRef(workflow_name, TargetType.WORKFLOW_DEF)
                permissions = auth_client.get_permissions(workflow_target)

                if AccessType.EXECUTE in permissions:
                    exec_perms = permissions[AccessType.EXECUTE]
                    assert any(
                        subject.id == main_groups["worker"].id
                        and subject.type == SubjectType.GROUP
                        for subject in exec_perms
                    ), f"Worker missing execute permission on {workflow_name}"

            bulk_users = []
            for i in range(5):
                bulk_user_id = f"bulk_user_{i}_{test_suffix}@company.com"
                bulk_user_request = UpsertUserRequest(
                    name=f"Bulk User {i}", roles=["USER"]
                )
                bulk_user = auth_client.upsert_user(bulk_user_request, bulk_user_id)
                bulk_users.append(bulk_user_id)
                created_resources["users"].append(bulk_user_id)

            for user_id in bulk_users:
                auth_client.add_user_to_group(main_groups["user"].id, user_id)

            group_users = auth_client.get_users_in_group(main_groups["user"].id)
            group_user_ids = [user.id for user in group_users]
            for user_id in bulk_users:
                assert (
                    user_id in group_user_ids
                ), f"Bulk user {user_id} not in employees group"

        except Exception as e:
            print(f"Error during complex flow: {str(e)}")
            raise
        finally:
            self._perform_comprehensive_cleanup(auth_client, created_resources)

    def _perform_comprehensive_cleanup(
        self, auth_client: OrkesAuthorizationClient, created_resources: dict
    ):

        cleanup_enabled = os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true"
        if not cleanup_enabled:
            return

        for subject, target, access_types in created_resources["permissions"]:
            try:
                auth_client.remove_permissions(subject, target, access_types)
            except Exception as e:
                print(
                    f"Warning: Failed to remove permission {subject.id} -> {target.id}: {str(e)}"
                )

        for group_id in created_resources["groups"]:
            try:
                group_users = auth_client.get_users_in_group(group_id)
                for user in group_users:
                    if user.id in created_resources["users"]:
                        auth_client.remove_user_from_group(group_id, user.id)
            except Exception as e:
                print(
                    f"Warning: Failed to remove users from group {group_id}: {str(e)}"
                )

        for app_id, key_id in created_resources["access_keys"]:
            try:
                auth_client.delete_access_key(app_id, key_id)
            except Exception as e:
                print(
                    f"Warning: Failed to delete access key {key_id} from app {app_id}: {str(e)}"
                )

        for group_id in created_resources["groups"]:
            try:
                auth_client.delete_group(group_id)
            except Exception as e:
                print(f"Warning: Failed to delete group {group_id}: {str(e)}")

        for user_id in created_resources["users"]:
            try:
                auth_client.delete_user(user_id)
            except Exception as e:
                print(f"Warning: Failed to delete user {user_id}: {str(e)}")

        for app_id in created_resources["applications"]:
            try:
                auth_client.delete_application(app_id)
            except Exception as e:
                print(f"Warning: Failed to delete application {app_id}: {str(e)}")
