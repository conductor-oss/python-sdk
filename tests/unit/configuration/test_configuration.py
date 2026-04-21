import base64
import os
import unittest
from unittest import mock

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api_client import ApiClient


class TestConfiguration(unittest.TestCase):
    @mock.patch.dict(os.environ, {"CONDUCTOR_SERVER_URL": "http://localhost:8080/api"})
    def test_initialization_default(self):
        configuration = Configuration()
        self.assertEqual(
            configuration.host,
            'http://localhost:8080/api'
        )

    def test_initialization_with_base_url(self):
        configuration = Configuration(
            base_url='https://developer.orkescloud.com'
        )
        self.assertEqual(
            configuration.host,
            'https://developer.orkescloud.com/api'
        )

    def test_initialization_with_server_api_url(self):
        configuration = Configuration(
            server_api_url='https://developer.orkescloud.com/api'
        )
        self.assertEqual(
            configuration.host,
            'https://developer.orkescloud.com/api'
        )

    def test_register_schema_default_is_none(self):
        """register_schema defaults to None when not set anywhere"""
        configuration = Configuration(server_api_url='http://localhost:8080/api')
        self.assertIsNone(configuration.register_schema)

    def test_register_schema_explicit_false(self):
        """register_schema can be set explicitly to False"""
        configuration = Configuration(server_api_url='http://localhost:8080/api', register_schema=False)
        self.assertFalse(configuration.register_schema)

    def test_register_schema_explicit_true(self):
        """register_schema can be set explicitly to True"""
        configuration = Configuration(server_api_url='http://localhost:8080/api', register_schema=True)
        self.assertTrue(configuration.register_schema)

    @mock.patch.dict(os.environ, {"CONDUCTOR_REGISTER_SCHEMAS": "false"})
    def test_register_schema_from_env_var(self):
        """register_schema reads CONDUCTOR_REGISTER_SCHEMAS env var"""
        configuration = Configuration(server_api_url='http://localhost:8080/api')
        self.assertFalse(configuration.register_schema)

    @mock.patch.dict(os.environ, {"CONDUCTOR_REGISTER_SCHEMAS": "true"})
    def test_register_schema_from_env_var_true(self):
        """register_schema reads CONDUCTOR_REGISTER_SCHEMAS env var as True"""
        configuration = Configuration(server_api_url='http://localhost:8080/api')
        self.assertTrue(configuration.register_schema)

    @mock.patch.dict(os.environ, {"CONDUCTOR_REGISTER_SCHEMAS": "false"})
    def test_register_schema_explicit_overrides_env(self):
        """Explicit register_schema param takes precedence over env var"""
        configuration = Configuration(server_api_url='http://localhost:8080/api', register_schema=True)
        self.assertTrue(configuration.register_schema)

    def test_initialization_with_basic_auth_server_api_url(self):
        configuration = Configuration(
            server_api_url="https://user:password@developer.orkescloud.com/api"
        )
        basic_auth = "user:password"
        expected_host = f"https://{basic_auth}@developer.orkescloud.com/api"
        self.assertEqual(
            configuration.host, expected_host,
        )
        token = "Basic " + \
                base64.b64encode(bytes(basic_auth, "utf-8")).decode("utf-8")
        api_client = ApiClient(configuration)
        self.assertEqual(
            api_client.default_headers,
            {"Accept-Encoding": "gzip", "authorization": token},
        )
