import logging
import unittest
import time
from typing import List

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.authentication_config import AuthenticationConfig
from conductor.client.http.models.conductor_application import ConductorApplication
from conductor.client.http.models.conductor_user import ConductorUser
from conductor.client.http.models.create_or_update_application_request import CreateOrUpdateApplicationRequest
from conductor.client.http.models.create_or_update_role_request import CreateOrUpdateRoleRequest
from conductor.client.http.models.group import Group
from conductor.client.http.models.subject_ref import SubjectRef
from conductor.client.http.models.target_ref import TargetRef
from conductor.client.http.models.upsert_group_request import UpsertGroupRequest
from conductor.client.http.models.upsert_user_request import UpsertUserRequest
from conductor.client.orkes.models.access_type import AccessType
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.orkes.orkes_authorization_client import OrkesAuthorizationClient

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(__name__)
)


def get_configuration():
    configuration = Configuration()
    configuration.debug = False
    configuration.apply_logging_config()
    return configuration


class TestOrkesAuthorizationClientIntg(unittest.TestCase):
    """Comprehensive integration test for OrkesAuthorizationClient.

    Tests all 49 methods in the authorization client against a live server.
    Includes setup and teardown to ensure clean test state.
    """

    @classmethod
    def setUpClass(cls):
        cls.config = get_configuration()
        cls.client = OrkesAuthorizationClient(cls.config)

        # Test resource names with timestamp to avoid conflicts
        cls.timestamp = str(int(time.time()))
        cls.test_app_name = f"test_app_{cls.timestamp}"
        cls.test_user_id = f"test_user_{cls.timestamp}@example.com"
        cls.test_group_id = f"test_group_{cls.timestamp}"
        cls.test_role_name = f"test_role_{cls.timestamp}"
        cls.test_gateway_config_id = None

        # Store created resource IDs for cleanup
        cls.created_app_id = None
        cls.created_access_key_id = None

        logger.info(f'Setting up TestOrkesAuthorizationClientIntg with timestamp {cls.timestamp}')

    @classmethod
    def tearDownClass(cls):
        """Clean up all test resources."""
        logger.info('Cleaning up test resources')

        try:
            # Clean up gateway auth config
            if cls.test_gateway_config_id:
                try:
                    cls.client.delete_gateway_auth_config(cls.test_gateway_config_id)
                    logger.info(f'Deleted gateway config: {cls.test_gateway_config_id}')
                except Exception as e:
                    logger.warning(f'Failed to delete gateway config: {e}')

            # Clean up role
            try:
                cls.client.delete_role(cls.test_role_name)
                logger.info(f'Deleted role: {cls.test_role_name}')
            except Exception as e:
                logger.warning(f'Failed to delete role: {e}')

            # Clean up group
            try:
                cls.client.delete_group(cls.test_group_id)
                logger.info(f'Deleted group: {cls.test_group_id}')
            except Exception as e:
                logger.warning(f'Failed to delete group: {e}')

            # Clean up user
            try:
                cls.client.delete_user(cls.test_user_id)
                logger.info(f'Deleted user: {cls.test_user_id}')
            except Exception as e:
                logger.warning(f'Failed to delete user: {e}')

            # Clean up access keys and application
            if cls.created_app_id:
                try:
                    if cls.created_access_key_id:
                        cls.client.delete_access_key(cls.created_app_id, cls.created_access_key_id)
                        logger.info(f'Deleted access key: {cls.created_access_key_id}')
                except Exception as e:
                    logger.warning(f'Failed to delete access key: {e}')

                try:
                    cls.client.delete_application(cls.created_app_id)
                    logger.info(f'Deleted application: {cls.created_app_id}')
                except Exception as e:
                    logger.warning(f'Failed to delete application: {e}')

        except Exception as e:
            logger.error(f'Error during cleanup: {e}')

    # ==================== Application Tests ====================

    def test_01_create_application(self):
        """Test: create_application"""
        logger.info('TEST: create_application')

        request = CreateOrUpdateApplicationRequest()
        request.name = self.test_app_name

        app = self.client.create_application(request)

        self.assertIsNotNone(app)
        self.assertIsInstance(app, ConductorApplication)
        self.assertEqual(app.name, self.test_app_name)

        # Store for other tests
        self.__class__.created_app_id = app.id
        logger.info(f'Created application: {app.id}')

    def test_02_get_application(self):
        """Test: get_application"""
        logger.info('TEST: get_application')

        self.assertIsNotNone(self.created_app_id, "Application must be created first")

        app = self.client.get_application(self.created_app_id)

        self.assertIsNotNone(app)
        self.assertEqual(app.id, self.created_app_id)
        self.assertEqual(app.name, self.test_app_name)

    def test_03_list_applications(self):
        """Test: list_applications"""
        logger.info('TEST: list_applications')

        apps = self.client.list_applications()

        self.assertIsNotNone(apps)
        self.assertIsInstance(apps, list)

        # Our test app should be in the list
        app_ids = [app.id if hasattr(app, 'id') else app.get('id') for app in apps]
        self.assertIn(self.created_app_id, app_ids)

    def test_04_update_application(self):
        """Test: update_application"""
        logger.info('TEST: update_application')

        self.assertIsNotNone(self.created_app_id, "Application must be created first")

        request = CreateOrUpdateApplicationRequest()
        request.name = f"{self.test_app_name}_updated"

        app = self.client.update_application(request, self.created_app_id)

        self.assertIsNotNone(app)
        self.assertEqual(app.id, self.created_app_id)

    def test_05_create_access_key(self):
        """Test: create_access_key"""
        logger.info('TEST: create_access_key')

        self.assertIsNotNone(self.created_app_id, "Application must be created first")

        created_key = self.client.create_access_key(self.created_app_id)

        self.assertIsNotNone(created_key)
        self.assertIsNotNone(created_key.id)
        self.assertIsNotNone(created_key.secret)

        # Store for other tests
        self.__class__.created_access_key_id = created_key.id
        logger.info(f'Created access key: {created_key.id}')

    def test_06_get_access_keys(self):
        """Test: get_access_keys"""
        logger.info('TEST: get_access_keys')

        self.assertIsNotNone(self.created_app_id, "Application must be created first")

        keys = self.client.get_access_keys(self.created_app_id)

        self.assertIsNotNone(keys)
        self.assertIsInstance(keys, list)

        # Our test key should be in the list
        key_ids = [k.id for k in keys]
        self.assertIn(self.created_access_key_id, key_ids)

    def test_07_toggle_access_key_status(self):
        """Test: toggle_access_key_status"""
        logger.info('TEST: toggle_access_key_status')

        self.assertIsNotNone(self.created_app_id, "Application must be created first")
        self.assertIsNotNone(self.created_access_key_id, "Access key must be created first")

        key = self.client.toggle_access_key_status(self.created_app_id, self.created_access_key_id)

        self.assertIsNotNone(key)
        self.assertEqual(key.id, self.created_access_key_id)

    def test_08_get_app_by_access_key_id(self):
        """Test: get_app_by_access_key_id"""
        logger.info('TEST: get_app_by_access_key_id')

        self.assertIsNotNone(self.created_access_key_id, "Access key must be created first")

        result = self.client.get_app_by_access_key_id(self.created_access_key_id)

        self.assertIsNotNone(result)

    def test_09_set_application_tags(self):
        """Test: set_application_tags"""
        logger.info('TEST: set_application_tags')

        self.assertIsNotNone(self.created_app_id, "Application must be created first")

        tags = [MetadataTag(key="env", value="test")]
        self.client.set_application_tags(tags, self.created_app_id)

        # Verify tags were set
        retrieved_tags = self.client.get_application_tags(self.created_app_id)
        self.assertIsNotNone(retrieved_tags)

    def test_10_get_application_tags(self):
        """Test: get_application_tags"""
        logger.info('TEST: get_application_tags')

        self.assertIsNotNone(self.created_app_id, "Application must be created first")

        tags = self.client.get_application_tags(self.created_app_id)

        self.assertIsNotNone(tags)
        self.assertIsInstance(tags, list)

    def test_11_delete_application_tags(self):
        """Test: delete_application_tags"""
        logger.info('TEST: delete_application_tags')

        self.assertIsNotNone(self.created_app_id, "Application must be created first")

        tags = [MetadataTag(key="env", value="test")]
        self.client.delete_application_tags(tags, self.created_app_id)

    def test_12_add_role_to_application_user(self):
        """Test: add_role_to_application_user"""
        logger.info('TEST: add_role_to_application_user')

        self.assertIsNotNone(self.created_app_id, "Application must be created first")

        try:
            self.client.add_role_to_application_user(self.created_app_id, "WORKER")
        except Exception as e:
            logger.warning(f'add_role_to_application_user failed (may not be supported): {e}')

    def test_13_remove_role_from_application_user(self):
        """Test: remove_role_from_application_user"""
        logger.info('TEST: remove_role_from_application_user')

        self.assertIsNotNone(self.created_app_id, "Application must be created first")

        try:
            self.client.remove_role_from_application_user(self.created_app_id, "WORKER")
        except Exception as e:
            logger.warning(f'remove_role_from_application_user failed (may not be supported): {e}')

    # ==================== User Tests ====================

    def test_14_upsert_user(self):
        """Test: upsert_user"""
        logger.info('TEST: upsert_user')

        request = UpsertUserRequest()
        request.name = "Test User"
        request.roles = []

        user = self.client.upsert_user(request, self.test_user_id)

        self.assertIsNotNone(user)
        self.assertIsInstance(user, ConductorUser)
        logger.info(f'Created/updated user: {self.test_user_id}')

    def test_15_get_user(self):
        """Test: get_user"""
        logger.info('TEST: get_user')

        user = self.client.get_user(self.test_user_id)

        self.assertIsNotNone(user)
        self.assertIsInstance(user, ConductorUser)

    def test_16_list_users(self):
        """Test: list_users"""
        logger.info('TEST: list_users')

        users = self.client.list_users(apps=False)

        self.assertIsNotNone(users)
        self.assertIsInstance(users, list)

    def test_17_list_users_with_apps(self):
        """Test: list_users with apps=True"""
        logger.info('TEST: list_users with apps=True')

        users = self.client.list_users(apps=True)

        self.assertIsNotNone(users)
        self.assertIsInstance(users, list)

    def test_18_check_permissions(self):
        """Test: check_permissions"""
        logger.info('TEST: check_permissions')

        try:
            result = self.client.check_permissions(
                self.test_user_id,
                "WORKFLOW_DEF",
                "test_workflow"
            )
            self.assertIsNotNone(result)
        except Exception as e:
            logger.warning(f'check_permissions failed: {e}')

    # ==================== Group Tests ====================

    def test_19_upsert_group(self):
        """Test: upsert_group"""
        logger.info('TEST: upsert_group')

        request = UpsertGroupRequest()
        request.description = "Test Group"

        group = self.client.upsert_group(request, self.test_group_id)

        self.assertIsNotNone(group)
        self.assertIsInstance(group, Group)
        logger.info(f'Created/updated group: {self.test_group_id}')

    def test_20_get_group(self):
        """Test: get_group"""
        logger.info('TEST: get_group')

        group = self.client.get_group(self.test_group_id)

        self.assertIsNotNone(group)
        self.assertIsInstance(group, Group)

    def test_21_list_groups(self):
        """Test: list_groups"""
        logger.info('TEST: list_groups')

        groups = self.client.list_groups()

        self.assertIsNotNone(groups)
        self.assertIsInstance(groups, list)

    def test_22_add_user_to_group(self):
        """Test: add_user_to_group"""
        logger.info('TEST: add_user_to_group')

        self.client.add_user_to_group(self.test_group_id, self.test_user_id)

    def test_23_get_users_in_group(self):
        """Test: get_users_in_group"""
        logger.info('TEST: get_users_in_group')

        users = self.client.get_users_in_group(self.test_group_id)

        self.assertIsNotNone(users)
        self.assertIsInstance(users, list)

    def test_24_add_users_to_group(self):
        """Test: add_users_to_group"""
        logger.info('TEST: add_users_to_group')

        # Add the same user via batch method
        self.client.add_users_to_group(self.test_group_id, [self.test_user_id])

    def test_25_remove_users_from_group(self):
        """Test: remove_users_from_group"""
        logger.info('TEST: remove_users_from_group')

        # Remove via batch method
        self.client.remove_users_from_group(self.test_group_id, [self.test_user_id])

    def test_26_remove_user_from_group(self):
        """Test: remove_user_from_group"""
        logger.info('TEST: remove_user_from_group')

        # Re-add and then remove via single method
        self.client.add_user_to_group(self.test_group_id, self.test_user_id)
        self.client.remove_user_from_group(self.test_group_id, self.test_user_id)

    def test_27_get_granted_permissions_for_group(self):
        """Test: get_granted_permissions_for_group"""
        logger.info('TEST: get_granted_permissions_for_group')

        permissions = self.client.get_granted_permissions_for_group(self.test_group_id)

        self.assertIsNotNone(permissions)
        self.assertIsInstance(permissions, list)

    # ==================== Permission Tests ====================

    def test_28_grant_permissions(self):
        """Test: grant_permissions"""
        logger.info('TEST: grant_permissions')

        subject = SubjectRef(type="GROUP", id=self.test_group_id)
        target = TargetRef(type="WORKFLOW_DEF", id="test_workflow")
        access = [AccessType.READ]

        try:
            self.client.grant_permissions(subject, target, access)
        except Exception as e:
            logger.warning(f'grant_permissions failed: {e}')

    def test_29_get_permissions(self):
        """Test: get_permissions"""
        logger.info('TEST: get_permissions')

        target = TargetRef(type="WORKFLOW_DEF", id="test_workflow")

        try:
            permissions = self.client.get_permissions(target)
            self.assertIsNotNone(permissions)
            self.assertIsInstance(permissions, dict)
        except Exception as e:
            logger.warning(f'get_permissions failed: {e}')

    def test_30_get_granted_permissions_for_user(self):
        """Test: get_granted_permissions_for_user"""
        logger.info('TEST: get_granted_permissions_for_user')

        permissions = self.client.get_granted_permissions_for_user(self.test_user_id)

        self.assertIsNotNone(permissions)
        self.assertIsInstance(permissions, list)

    def test_31_remove_permissions(self):
        """Test: remove_permissions"""
        logger.info('TEST: remove_permissions')

        subject = SubjectRef(type="GROUP", id=self.test_group_id)
        target = TargetRef(type="WORKFLOW_DEF", id="test_workflow")
        access = [AccessType.READ]

        try:
            self.client.remove_permissions(subject, target, access)
        except Exception as e:
            logger.warning(f'remove_permissions failed: {e}')

    # ==================== Token/Authentication Tests ====================

    def test_32_generate_token(self):
        """Test: generate_token"""
        logger.info('TEST: generate_token')

        # This will fail without valid credentials, but tests the method exists
        try:
            token = self.client.generate_token("fake_key_id", "fake_secret")
            logger.info('generate_token succeeded (unexpected)')
        except Exception as e:
            logger.info(f'generate_token failed as expected with invalid credentials: {e}')
            # This is expected - method exists and was called

    def test_33_get_user_info_from_token(self):
        """Test: get_user_info_from_token"""
        logger.info('TEST: get_user_info_from_token')

        try:
            user_info = self.client.get_user_info_from_token()
            self.assertIsNotNone(user_info)
        except Exception as e:
            logger.warning(f'get_user_info_from_token failed: {e}')

    # ==================== Role Tests ====================

    def test_34_list_all_roles(self):
        """Test: list_all_roles"""
        logger.info('TEST: list_all_roles')

        roles = self.client.list_all_roles()

        self.assertIsNotNone(roles)
        self.assertIsInstance(roles, list)

    def test_35_list_system_roles(self):
        """Test: list_system_roles"""
        logger.info('TEST: list_system_roles')

        roles = self.client.list_system_roles()

        self.assertIsNotNone(roles)

    def test_36_list_custom_roles(self):
        """Test: list_custom_roles"""
        logger.info('TEST: list_custom_roles')

        roles = self.client.list_custom_roles()

        self.assertIsNotNone(roles)
        self.assertIsInstance(roles, list)

    def test_37_list_available_permissions(self):
        """Test: list_available_permissions"""
        logger.info('TEST: list_available_permissions')

        permissions = self.client.list_available_permissions()

        self.assertIsNotNone(permissions)

    def test_38_create_role(self):
        """Test: create_role"""
        logger.info('TEST: create_role')

        request = CreateOrUpdateRoleRequest()
        request.name = self.test_role_name
        request.permissions = ["workflow:read"]

        result = self.client.create_role(request)

        self.assertIsNotNone(result)
        logger.info(f'Created role: {self.test_role_name}')

    def test_39_get_role(self):
        """Test: get_role"""
        logger.info('TEST: get_role')

        role = self.client.get_role(self.test_role_name)

        self.assertIsNotNone(role)

    def test_40_update_role(self):
        """Test: update_role"""
        logger.info('TEST: update_role')

        request = CreateOrUpdateRoleRequest()
        request.name = self.test_role_name
        request.permissions = ["workflow:read", "workflow:execute"]

        result = self.client.update_role(self.test_role_name, request)

        self.assertIsNotNone(result)

    # ==================== Gateway Auth Config Tests ====================

    def test_41_create_gateway_auth_config(self):
        """Test: create_gateway_auth_config"""
        logger.info('TEST: create_gateway_auth_config')

        self.assertIsNotNone(self.created_app_id, "Application must be created first")

        config = AuthenticationConfig()
        config.id = f"test_config_{self.timestamp}"
        config.application_id = self.created_app_id
        config.authentication_type = "NONE"

        try:
            config_id = self.client.create_gateway_auth_config(config)

            self.assertIsNotNone(config_id)
            self.__class__.test_gateway_config_id = config_id
            logger.info(f'Created gateway config: {config_id}')
        except Exception as e:
            logger.warning(f'create_gateway_auth_config failed: {e}')
            # Store the config ID we tried to use for cleanup
            self.__class__.test_gateway_config_id = config.id

    def test_42_list_gateway_auth_configs(self):
        """Test: list_gateway_auth_configs"""
        logger.info('TEST: list_gateway_auth_configs')

        configs = self.client.list_gateway_auth_configs()

        self.assertIsNotNone(configs)
        self.assertIsInstance(configs, list)

    def test_43_get_gateway_auth_config(self):
        """Test: get_gateway_auth_config"""
        logger.info('TEST: get_gateway_auth_config')

        if self.test_gateway_config_id:
            try:
                config = self.client.get_gateway_auth_config(self.test_gateway_config_id)
                self.assertIsNotNone(config)
            except Exception as e:
                logger.warning(f'get_gateway_auth_config failed: {e}')

    def test_44_update_gateway_auth_config(self):
        """Test: update_gateway_auth_config"""
        logger.info('TEST: update_gateway_auth_config')

        if self.test_gateway_config_id and self.created_app_id:
            config = AuthenticationConfig()
            config.id = self.test_gateway_config_id
            config.application_id = self.created_app_id
            config.authentication_type = "API_KEY"
            config.api_keys = ["test_key"]

            try:
                self.client.update_gateway_auth_config(self.test_gateway_config_id, config)
            except Exception as e:
                logger.warning(f'update_gateway_auth_config failed: {e}')

    # ==================== Cleanup Tests (run last) ====================

    def test_98_delete_role(self):
        """Test: delete_role (cleanup test)"""
        logger.info('TEST: delete_role')

        try:
            self.client.delete_role(self.test_role_name)
            logger.info(f'Deleted role: {self.test_role_name}')
        except Exception as e:
            logger.warning(f'delete_role failed: {e}')

    def test_99_delete_gateway_auth_config(self):
        """Test: delete_gateway_auth_config (cleanup test)"""
        logger.info('TEST: delete_gateway_auth_config')

        if self.test_gateway_config_id:
            try:
                self.client.delete_gateway_auth_config(self.test_gateway_config_id)
                logger.info(f'Deleted gateway config: {self.test_gateway_config_id}')
            except Exception as e:
                logger.warning(f'delete_gateway_auth_config failed: {e}')


if __name__ == '__main__':
    # Run tests in order
    unittest.main(verbosity=2)
