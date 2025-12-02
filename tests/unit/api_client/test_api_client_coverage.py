import unittest
import datetime
import tempfile
import os
import time
import uuid
from unittest.mock import Mock, MagicMock, patch, mock_open, call
from requests.structures import CaseInsensitiveDict

from conductor.client.http.api_client import ApiClient
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.http import rest
from conductor.client.http.rest import AuthorizationException, ApiException
from conductor.client.http.models.token import Token


class TestApiClientCoverage(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.config = Configuration(
            base_url="http://localhost:8080",
            authentication_settings=None
        )

    def test_init_with_no_configuration(self):
        """Test ApiClient initialization with no configuration"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient()
            self.assertIsNotNone(client.configuration)
            self.assertIsInstance(client.configuration, Configuration)

    def test_init_with_custom_headers(self):
        """Test ApiClient initialization with custom headers"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(
                configuration=self.config,
                header_name='X-Custom-Header',
                header_value='custom-value'
            )
            self.assertIn('X-Custom-Header', client.default_headers)
            self.assertEqual(client.default_headers['X-Custom-Header'], 'custom-value')

    def test_init_with_cookie(self):
        """Test ApiClient initialization with cookie"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config, cookie='session=abc123')
            self.assertEqual(client.cookie, 'session=abc123')

    def test_init_with_metrics_collector(self):
        """Test ApiClient initialization with metrics collector"""
        metrics_collector = Mock()
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config, metrics_collector=metrics_collector)
            self.assertEqual(client.metrics_collector, metrics_collector)

    def test_sanitize_for_serialization_none(self):
        """Test sanitize_for_serialization with None"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)
            result = client.sanitize_for_serialization(None)
            self.assertIsNone(result)

    def test_sanitize_for_serialization_bytes_utf8(self):
        """Test sanitize_for_serialization with UTF-8 bytes"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)
            data = b'hello world'
            result = client.sanitize_for_serialization(data)
            self.assertEqual(result, 'hello world')

    def test_sanitize_for_serialization_bytes_binary(self):
        """Test sanitize_for_serialization with binary bytes"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)
            # Binary data that can't be decoded as UTF-8
            data = b'\x80\x81\x82'
            result = client.sanitize_for_serialization(data)
            # Should be base64 encoded
            self.assertTrue(isinstance(result, str))

    def test_sanitize_for_serialization_tuple(self):
        """Test sanitize_for_serialization with tuple"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)
            data = (1, 2, 'test')
            result = client.sanitize_for_serialization(data)
            self.assertEqual(result, (1, 2, 'test'))

    def test_sanitize_for_serialization_datetime(self):
        """Test sanitize_for_serialization with datetime"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)
            dt = datetime.datetime(2025, 1, 1, 12, 0, 0)
            result = client.sanitize_for_serialization(dt)
            self.assertEqual(result, '2025-01-01T12:00:00')

    def test_sanitize_for_serialization_date(self):
        """Test sanitize_for_serialization with date"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)
            d = datetime.date(2025, 1, 1)
            result = client.sanitize_for_serialization(d)
            self.assertEqual(result, '2025-01-01')

    def test_sanitize_for_serialization_case_insensitive_dict(self):
        """Test sanitize_for_serialization with CaseInsensitiveDict"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)
            data = CaseInsensitiveDict({'Key': 'value'})
            result = client.sanitize_for_serialization(data)
            self.assertEqual(result, {'Key': 'value'})

    def test_sanitize_for_serialization_object_with_attribute_map(self):
        """Test sanitize_for_serialization with object having attribute_map"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            # Create a mock object with swagger_types and attribute_map
            obj = Mock()
            obj.swagger_types = {'field1': 'str', 'field2': 'int'}
            obj.attribute_map = {'field1': 'json_field1', 'field2': 'json_field2'}
            obj.field1 = 'value1'
            obj.field2 = 42

            result = client.sanitize_for_serialization(obj)
            self.assertEqual(result, {'json_field1': 'value1', 'json_field2': 42})

    def test_sanitize_for_serialization_object_with_vars(self):
        """Test sanitize_for_serialization with object having __dict__"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            # Create a simple object without swagger_types
            class SimpleObj:
                def __init__(self):
                    self.field1 = 'value1'
                    self.field2 = 42

            obj = SimpleObj()
            result = client.sanitize_for_serialization(obj)
            self.assertEqual(result, {'field1': 'value1', 'field2': 42})

    def test_sanitize_for_serialization_object_fallback_to_string(self):
        """Test sanitize_for_serialization fallback to string"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            # Create an object that can't be serialized normally
            obj = object()
            result = client.sanitize_for_serialization(obj)
            self.assertTrue(isinstance(result, str))

    def test_deserialize_file(self):
        """Test deserialize with file response_type"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            # Mock response
            response = Mock()
            response.getheader.return_value = 'attachment; filename="test.txt"'
            response.data = b'file content'

            with patch('tempfile.mkstemp') as mock_mkstemp, \
                 patch('os.close') as mock_close, \
                 patch('os.remove') as mock_remove, \
                 patch('builtins.open', mock_open()) as mock_file:

                mock_mkstemp.return_value = (123, '/tmp/tempfile')

                result = client.deserialize(response, 'file')

                self.assertTrue(result.endswith('test.txt'))
                mock_close.assert_called_once_with(123)
                mock_remove.assert_called_once_with('/tmp/tempfile')

    def test_deserialize_with_json_response(self):
        """Test deserialize with JSON response"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            # Mock response with JSON
            response = Mock()
            response.resp.json.return_value = {'key': 'value'}

            result = client.deserialize(response, 'dict(str, str)')
            self.assertEqual(result, {'key': 'value'})

    def test_deserialize_with_text_response(self):
        """Test deserialize with text response when JSON parsing fails"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            # Mock response that fails JSON parsing
            response = Mock()
            response.resp.json.side_effect = Exception("Not JSON")
            response.resp.text = "plain text"

            with patch.object(client, '_ApiClient__deserialize', return_value="deserialized") as mock_deserialize:
                result = client.deserialize(response, 'str')
                mock_deserialize.assert_called_once_with("plain text", 'str')

    def test_deserialize_with_value_error(self):
        """Test deserialize with ValueError during deserialization"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            response = Mock()
            response.resp.json.return_value = {'key': 'value'}

            with patch.object(client, '_ApiClient__deserialize', side_effect=ValueError("Invalid")):
                result = client.deserialize(response, 'SomeClass')
                self.assertIsNone(result)

    def test_deserialize_class(self):
        """Test deserialize_class method"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch.object(client, '_ApiClient__deserialize', return_value="result") as mock_deserialize:
                result = client.deserialize_class({'key': 'value'}, 'str')
                mock_deserialize.assert_called_once_with({'key': 'value'}, 'str')
                self.assertEqual(result, "result")

    def test_deserialize_list(self):
        """Test __deserialize with list type"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            data = [1, 2, 3]
            result = client.deserialize_class(data, 'list[int]')
            self.assertEqual(result, [1, 2, 3])

    def test_deserialize_set(self):
        """Test __deserialize with set type"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            data = [1, 2, 3, 2]
            result = client.deserialize_class(data, 'set[int]')
            self.assertEqual(result, {1, 2, 3})

    def test_deserialize_dict(self):
        """Test __deserialize with dict type"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            data = {'key1': 'value1', 'key2': 'value2'}
            result = client.deserialize_class(data, 'dict(str, str)')
            self.assertEqual(result, {'key1': 'value1', 'key2': 'value2'})

    def test_deserialize_native_type(self):
        """Test __deserialize with native type"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            result = client.deserialize_class('42', 'int')
            self.assertEqual(result, 42)

    def test_deserialize_object_type(self):
        """Test __deserialize with object type"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            data = {'key': 'value'}
            result = client.deserialize_class(data, 'object')
            self.assertEqual(result, {'key': 'value'})

    def test_deserialize_date_type(self):
        """Test __deserialize with date type"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            result = client.deserialize_class('2025-01-01', datetime.date)
            self.assertIsInstance(result, datetime.date)

    def test_deserialize_datetime_type(self):
        """Test __deserialize with datetime type"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            result = client.deserialize_class('2025-01-01T12:00:00', datetime.datetime)
            self.assertIsInstance(result, datetime.datetime)

    def test_deserialize_date_with_invalid_string(self):
        """Test __deserialize date with invalid string"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with self.assertRaises(ApiException):
                client.deserialize_class('invalid-date', datetime.date)

    def test_deserialize_datetime_with_invalid_string(self):
        """Test __deserialize datetime with invalid string"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with self.assertRaises(ApiException):
                client.deserialize_class('invalid-datetime', datetime.datetime)

    def test_deserialize_bytes_to_str(self):
        """Test __deserialize_bytes_to_str"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            result = client.deserialize_class(b'test', str)
            self.assertEqual(result, 'test')

    def test_deserialize_primitive_with_unicode_error(self):
        """Test __deserialize_primitive with UnicodeEncodeError"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            # This should handle the UnicodeEncodeError path
            data = 'test\u200b'  # Zero-width space
            result = client.deserialize_class(data, str)
            self.assertIsInstance(result, str)

    def test_deserialize_primitive_with_type_error(self):
        """Test __deserialize_primitive with TypeError"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            # Pass data that can't be converted - use a type that will trigger TypeError
            data = ['list', 'data']  # list can't be converted to int
            result = client.deserialize_class(data, int)
            # Should return original data on TypeError
            self.assertEqual(result, data)

    def test_call_api_sync(self):
        """Test call_api in synchronous mode"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch.object(client, '_ApiClient__call_api', return_value='result') as mock_call:
                result = client.call_api(
                    '/test', 'GET',
                    async_req=False
                )
                self.assertEqual(result, 'result')
                mock_call.assert_called_once()

    def test_call_api_async(self):
        """Test call_api in asynchronous mode"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch('conductor.client.http.api_client.AwaitableThread') as mock_thread:
                mock_thread_instance = Mock()
                mock_thread.return_value = mock_thread_instance

                result = client.call_api(
                    '/test', 'GET',
                    async_req=True
                )

                self.assertEqual(result, mock_thread_instance)
                mock_thread_instance.start.assert_called_once()

    def test_call_api_with_expired_token(self):
        """Test __call_api with expired token that gets renewed"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            # Create mock expired token exception
            expired_exception = AuthorizationException(status=401, reason='Expired')
            expired_exception._error_code = 'EXPIRED_TOKEN'

            with patch.object(client, '_ApiClient__call_api_no_retry') as mock_call_no_retry, \
                 patch.object(client, '_ApiClient__force_refresh_auth_token', return_value=True) as mock_refresh:

                # First call raises exception, second call succeeds
                mock_call_no_retry.side_effect = [expired_exception, 'success']

                result = client.call_api('/test', 'GET')

                self.assertEqual(result, 'success')
                self.assertEqual(mock_call_no_retry.call_count, 2)
                mock_refresh.assert_called_once()

    def test_call_api_with_invalid_token(self):
        """Test __call_api with invalid token that gets renewed"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            # Create mock invalid token exception
            invalid_exception = AuthorizationException(status=401, reason='Invalid')
            invalid_exception._error_code = 'INVALID_TOKEN'

            with patch.object(client, '_ApiClient__call_api_no_retry') as mock_call_no_retry, \
                 patch.object(client, '_ApiClient__force_refresh_auth_token', return_value=True) as mock_refresh:

                # First call raises exception, second call succeeds
                mock_call_no_retry.side_effect = [invalid_exception, 'success']

                result = client.call_api('/test', 'GET')

                self.assertEqual(result, 'success')
                self.assertEqual(mock_call_no_retry.call_count, 2)
                mock_refresh.assert_called_once()

    def test_call_api_with_failed_token_refresh(self):
        """Test __call_api when token refresh fails"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            expired_exception = AuthorizationException(status=401, reason='Expired')
            expired_exception._error_code = 'EXPIRED_TOKEN'

            with patch.object(client, '_ApiClient__call_api_no_retry') as mock_call_no_retry, \
                 patch.object(client, '_ApiClient__force_refresh_auth_token', return_value=False) as mock_refresh:

                mock_call_no_retry.side_effect = [expired_exception]

                with self.assertRaises(AuthorizationException):
                    client.call_api('/test', 'GET')

                mock_refresh.assert_called_once()

    def test_call_api_no_retry_with_cookie(self):
        """Test __call_api_no_retry with cookie"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config, cookie='session=abc')

            with patch.object(client, 'request', return_value=Mock(status=200, data='{}')) as mock_request:
                mock_response = Mock()
                mock_response.status = 200
                mock_request.return_value = mock_response

                result = client.call_api('/test', 'GET', _return_http_data_only=False)

                # Check that Cookie header was added
                call_args = mock_request.call_args
                headers = call_args[1]['headers']
                self.assertIn('Cookie', headers)
                self.assertEqual(headers['Cookie'], 'session=abc')

    def test_call_api_no_retry_with_path_params(self):
        """Test __call_api_no_retry with path parameters"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch.object(client, 'request', return_value=Mock(status=200)) as mock_request:
                mock_response = Mock()
                mock_response.status = 200
                mock_request.return_value = mock_response

                client.call_api(
                    '/test/{id}',
                    'GET',
                    path_params={'id': 'test-id'},
                    _return_http_data_only=False
                )

                # Check URL was constructed with path param
                call_args = mock_request.call_args
                url = call_args[0][1]
                self.assertIn('test-id', url)

    def test_call_api_no_retry_with_query_params(self):
        """Test __call_api_no_retry with query parameters"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch.object(client, 'request', return_value=Mock(status=200)) as mock_request:
                mock_response = Mock()
                mock_response.status = 200
                mock_request.return_value = mock_response

                client.call_api(
                    '/test',
                    'GET',
                    query_params={'key': 'value'},
                    _return_http_data_only=False
                )

                # Check query params were passed
                call_args = mock_request.call_args
                query_params = call_args[1].get('query_params')
                self.assertIsNotNone(query_params)

    def test_call_api_no_retry_with_post_params(self):
        """Test __call_api_no_retry with post parameters"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch.object(client, 'request', return_value=Mock(status=200)) as mock_request:
                mock_response = Mock()
                mock_response.status = 200
                mock_request.return_value = mock_response

                client.call_api(
                    '/test',
                    'POST',
                    post_params={'key': 'value'},
                    _return_http_data_only=False
                )

                mock_request.assert_called_once()

    def test_call_api_no_retry_with_files(self):
        """Test __call_api_no_retry with files"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
                tmp.write('test content')
                tmp_path = tmp.name

            try:
                with patch.object(client, 'request', return_value=Mock(status=200)) as mock_request:
                    mock_response = Mock()
                    mock_response.status = 200
                    mock_request.return_value = mock_response

                    client.call_api(
                        '/test',
                        'POST',
                        files={'file': tmp_path},
                        _return_http_data_only=False
                    )

                    mock_request.assert_called_once()
            finally:
                os.unlink(tmp_path)

    def test_call_api_no_retry_with_auth_settings(self):
        """Test __call_api_no_retry with authentication settings"""
        auth_settings = AuthenticationSettings(key_id='test-key', key_secret='test-secret')
        config = Configuration(
            base_url="http://localhost:8080",
            authentication_settings=auth_settings
        )

        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=config)
            client.configuration.AUTH_TOKEN = 'test-token'
            client.configuration.token_update_time = round(time.time() * 1000)  # Set as recent

            with patch.object(client, 'request', return_value=Mock(status=200)) as mock_request:
                mock_response = Mock()
                mock_response.status = 200
                mock_request.return_value = mock_response

                client.call_api(
                    '/test',
                    'GET',
                    _return_http_data_only=False
                )

                # Check auth header was added
                call_args = mock_request.call_args
                headers = call_args[1]['headers']
                self.assertIn('X-Authorization', headers)
                self.assertEqual(headers['X-Authorization'], 'test-token')

    def test_call_api_no_retry_with_preload_content_false(self):
        """Test __call_api_no_retry with _preload_content=False"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch.object(client, 'request') as mock_request:
                mock_response = Mock()
                mock_response.status = 200
                mock_request.return_value = mock_response

                result = client.call_api(
                    '/test',
                    'GET',
                    _preload_content=False,
                    _return_http_data_only=False
                )

                # Should return response data directly without deserialization
                self.assertEqual(result[0], mock_response)

    def test_call_api_no_retry_with_response_type(self):
        """Test __call_api_no_retry with response_type"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch.object(client, 'request') as mock_request, \
                 patch.object(client, 'deserialize', return_value={'key': 'value'}) as mock_deserialize:
                mock_response = Mock()
                mock_response.status = 200
                mock_request.return_value = mock_response

                result = client.call_api(
                    '/test',
                    'GET',
                    response_type='dict(str, str)',
                    _return_http_data_only=True
                )

                mock_deserialize.assert_called_once_with(mock_response, 'dict(str, str)')
                self.assertEqual(result, {'key': 'value'})

    def test_request_get(self):
        """Test request method with GET"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch.object(client.rest_client, 'GET', return_value=Mock(status=200)) as mock_get:
                client.request('GET', 'http://localhost:8080/test')
                mock_get.assert_called_once()

    def test_request_head(self):
        """Test request method with HEAD"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch.object(client.rest_client, 'HEAD', return_value=Mock(status=200)) as mock_head:
                client.request('HEAD', 'http://localhost:8080/test')
                mock_head.assert_called_once()

    def test_request_options(self):
        """Test request method with OPTIONS"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch.object(client.rest_client, 'OPTIONS', return_value=Mock(status=200)) as mock_options:
                client.request('OPTIONS', 'http://localhost:8080/test', body={'key': 'value'})
                mock_options.assert_called_once()

    def test_request_post(self):
        """Test request method with POST"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch.object(client.rest_client, 'POST', return_value=Mock(status=200)) as mock_post:
                client.request('POST', 'http://localhost:8080/test', body={'key': 'value'})
                mock_post.assert_called_once()

    def test_request_put(self):
        """Test request method with PUT"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch.object(client.rest_client, 'PUT', return_value=Mock(status=200)) as mock_put:
                client.request('PUT', 'http://localhost:8080/test', body={'key': 'value'})
                mock_put.assert_called_once()

    def test_request_patch(self):
        """Test request method with PATCH"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch.object(client.rest_client, 'PATCH', return_value=Mock(status=200)) as mock_patch:
                client.request('PATCH', 'http://localhost:8080/test', body={'key': 'value'})
                mock_patch.assert_called_once()

    def test_request_delete(self):
        """Test request method with DELETE"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch.object(client.rest_client, 'DELETE', return_value=Mock(status=200)) as mock_delete:
                client.request('DELETE', 'http://localhost:8080/test')
                mock_delete.assert_called_once()

    def test_request_invalid_method(self):
        """Test request method with invalid HTTP method"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with self.assertRaises(ValueError) as context:
                client.request('INVALID', 'http://localhost:8080/test')

            self.assertIn('http method must be', str(context.exception))

    def test_request_with_metrics_collector(self):
        """Test request method with metrics collector"""
        metrics_collector = Mock()
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config, metrics_collector=metrics_collector)

            with patch.object(client.rest_client, 'GET', return_value=Mock(status=200)):
                client.request('GET', 'http://localhost:8080/test')

                metrics_collector.record_api_request_time.assert_called_once()
                call_args = metrics_collector.record_api_request_time.call_args
                self.assertEqual(call_args[1]['method'], 'GET')
                self.assertEqual(call_args[1]['status'], '200')

    def test_request_with_metrics_collector_on_error(self):
        """Test request method with metrics collector on error"""
        metrics_collector = Mock()
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config, metrics_collector=metrics_collector)

            error = Exception('Test error')
            error.status = 500

            with patch.object(client.rest_client, 'GET', side_effect=error):
                with self.assertRaises(Exception):
                    client.request('GET', 'http://localhost:8080/test')

                metrics_collector.record_api_request_time.assert_called_once()
                call_args = metrics_collector.record_api_request_time.call_args
                self.assertEqual(call_args[1]['status'], '500')

    def test_request_with_metrics_collector_on_error_no_status(self):
        """Test request method with metrics collector on error without status"""
        metrics_collector = Mock()
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config, metrics_collector=metrics_collector)

            error = Exception('Test error')

            with patch.object(client.rest_client, 'GET', side_effect=error):
                with self.assertRaises(Exception):
                    client.request('GET', 'http://localhost:8080/test')

                metrics_collector.record_api_request_time.assert_called_once()
                call_args = metrics_collector.record_api_request_time.call_args
                self.assertEqual(call_args[1]['status'], 'error')

    def test_parameters_to_tuples_with_collection_format_multi(self):
        """Test parameters_to_tuples with multi collection format"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            params = {'key': ['val1', 'val2', 'val3']}
            collection_formats = {'key': 'multi'}

            result = client.parameters_to_tuples(params, collection_formats)

            self.assertEqual(result, [('key', 'val1'), ('key', 'val2'), ('key', 'val3')])

    def test_parameters_to_tuples_with_collection_format_ssv(self):
        """Test parameters_to_tuples with ssv collection format"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            params = {'key': ['val1', 'val2', 'val3']}
            collection_formats = {'key': 'ssv'}

            result = client.parameters_to_tuples(params, collection_formats)

            self.assertEqual(result, [('key', 'val1 val2 val3')])

    def test_parameters_to_tuples_with_collection_format_tsv(self):
        """Test parameters_to_tuples with tsv collection format"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            params = {'key': ['val1', 'val2', 'val3']}
            collection_formats = {'key': 'tsv'}

            result = client.parameters_to_tuples(params, collection_formats)

            self.assertEqual(result, [('key', 'val1\tval2\tval3')])

    def test_parameters_to_tuples_with_collection_format_pipes(self):
        """Test parameters_to_tuples with pipes collection format"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            params = {'key': ['val1', 'val2', 'val3']}
            collection_formats = {'key': 'pipes'}

            result = client.parameters_to_tuples(params, collection_formats)

            self.assertEqual(result, [('key', 'val1|val2|val3')])

    def test_parameters_to_tuples_with_collection_format_csv(self):
        """Test parameters_to_tuples with csv collection format (default)"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            params = {'key': ['val1', 'val2', 'val3']}
            collection_formats = {'key': 'csv'}

            result = client.parameters_to_tuples(params, collection_formats)

            self.assertEqual(result, [('key', 'val1,val2,val3')])

    def test_prepare_post_parameters_with_post_params(self):
        """Test prepare_post_parameters with post_params"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            post_params = [('key', 'value')]
            result = client.prepare_post_parameters(post_params=post_params)

            self.assertEqual(result, [('key', 'value')])

    def test_prepare_post_parameters_with_files(self):
        """Test prepare_post_parameters with files"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
                tmp.write('test content')
                tmp_path = tmp.name

            try:
                result = client.prepare_post_parameters(files={'file': tmp_path})

                self.assertEqual(len(result), 1)
                self.assertEqual(result[0][0], 'file')
                filename, filedata, mimetype = result[0][1]
                self.assertTrue(filename.endswith(os.path.basename(tmp_path)))
                self.assertEqual(filedata, b'test content')
            finally:
                os.unlink(tmp_path)

    def test_prepare_post_parameters_with_file_list(self):
        """Test prepare_post_parameters with list of files"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp1, \
                 tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp2:
                tmp1.write('content1')
                tmp2.write('content2')
                tmp1_path = tmp1.name
                tmp2_path = tmp2.name

            try:
                result = client.prepare_post_parameters(files={'files': [tmp1_path, tmp2_path]})

                self.assertEqual(len(result), 2)
            finally:
                os.unlink(tmp1_path)
                os.unlink(tmp2_path)

    def test_prepare_post_parameters_with_empty_files(self):
        """Test prepare_post_parameters with empty files"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            result = client.prepare_post_parameters(files={'file': None})

            self.assertEqual(result, [])

    def test_select_header_accept_none(self):
        """Test select_header_accept with None"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            result = client.select_header_accept(None)
            self.assertIsNone(result)

    def test_select_header_accept_empty(self):
        """Test select_header_accept with empty list"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            result = client.select_header_accept([])
            self.assertIsNone(result)

    def test_select_header_accept_with_json(self):
        """Test select_header_accept with application/json"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            result = client.select_header_accept(['application/json', 'text/plain'])
            self.assertEqual(result, 'application/json')

    def test_select_header_accept_without_json(self):
        """Test select_header_accept without application/json"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            result = client.select_header_accept(['text/plain', 'text/html'])
            self.assertEqual(result, 'text/plain, text/html')

    def test_select_header_content_type_none(self):
        """Test select_header_content_type with None"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            result = client.select_header_content_type(None)
            self.assertEqual(result, 'application/json')

    def test_select_header_content_type_empty(self):
        """Test select_header_content_type with empty list"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            result = client.select_header_content_type([])
            self.assertEqual(result, 'application/json')

    def test_select_header_content_type_with_json(self):
        """Test select_header_content_type with application/json"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            result = client.select_header_content_type(['application/json', 'text/plain'])
            self.assertEqual(result, 'application/json')

    def test_select_header_content_type_with_wildcard(self):
        """Test select_header_content_type with */*"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            result = client.select_header_content_type(['*/*'])
            self.assertEqual(result, 'application/json')

    def test_select_header_content_type_without_json(self):
        """Test select_header_content_type without application/json"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            result = client.select_header_content_type(['text/plain', 'text/html'])
            self.assertEqual(result, 'text/plain')

    def test_update_params_for_auth_none(self):
        """Test update_params_for_auth with None"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            headers = {}
            querys = {}
            client.update_params_for_auth(headers, querys, None)

            self.assertEqual(headers, {})
            self.assertEqual(querys, {})

    def test_update_params_for_auth_with_header(self):
        """Test update_params_for_auth with header auth"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            headers = {}
            querys = {}
            auth_settings = {
                'header': {'X-Auth-Token': 'token123'}
            }
            client.update_params_for_auth(headers, querys, auth_settings)

            self.assertEqual(headers, {'X-Auth-Token': 'token123'})

    def test_update_params_for_auth_with_query(self):
        """Test update_params_for_auth with query auth"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            headers = {}
            querys = {}
            auth_settings = {
                'query': {'api_key': 'key123'}
            }
            client.update_params_for_auth(headers, querys, auth_settings)

            self.assertEqual(querys, {'api_key': 'key123'})

    def test_get_authentication_headers(self):
        """Test get_authentication_headers public method"""
        auth_settings = AuthenticationSettings(key_id='test-key', key_secret='test-secret')
        config = Configuration(
            base_url="http://localhost:8080",
            authentication_settings=auth_settings
        )

        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=config)
            client.configuration.AUTH_TOKEN = 'test-token'
            client.configuration.token_update_time = round(time.time() * 1000)

            headers = client.get_authentication_headers()

            self.assertEqual(headers['header']['X-Authorization'], 'test-token')

    def test_get_authentication_headers_with_no_token(self):
        """Test __get_authentication_headers with no token"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)
            client.configuration.AUTH_TOKEN = None

            headers = client.get_authentication_headers()

            self.assertIsNone(headers)

    def test_get_authentication_headers_with_expired_token(self):
        """Test __get_authentication_headers with expired token"""
        auth_settings = AuthenticationSettings(key_id='test-key', key_secret='test-secret')
        config = Configuration(
            base_url="http://localhost:8080",
            authentication_settings=auth_settings
        )

        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=config)
            client.configuration.AUTH_TOKEN = 'old-token'
            # Set token update time to past (expired)
            client.configuration.token_update_time = 0

            with patch.object(client, '_ApiClient__get_new_token', return_value='new-token') as mock_get_token:
                headers = client.get_authentication_headers()

                mock_get_token.assert_called_once_with(skip_backoff=True)
                self.assertEqual(headers['header']['X-Authorization'], 'new-token')

    def test_refresh_auth_token_with_existing_token(self):
        """Test __refresh_auth_token with existing token"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)
            client.configuration.AUTH_TOKEN = 'existing-token'

            # Call the actual method
            with patch.object(client, '_ApiClient__get_new_token') as mock_get_token:
                client._ApiClient__refresh_auth_token()

                # Should not try to get new token if one exists
                mock_get_token.assert_not_called()

    def test_refresh_auth_token_without_auth_settings(self):
        """Test __refresh_auth_token without authentication settings"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)
            client.configuration.AUTH_TOKEN = None
            client.configuration.authentication_settings = None

            with patch.object(client, '_ApiClient__get_new_token') as mock_get_token:
                client._ApiClient__refresh_auth_token()

                # Should not try to get new token without auth settings
                mock_get_token.assert_not_called()

    def test_refresh_auth_token_initial(self):
        """Test __refresh_auth_token initial token generation"""
        auth_settings = AuthenticationSettings(key_id='test-key', key_secret='test-secret')
        config = Configuration(
            base_url="http://localhost:8080",
            authentication_settings=auth_settings
        )

        # Don't patch __refresh_auth_token, let it run naturally
        with patch.object(ApiClient, '_ApiClient__get_new_token', return_value='new-token') as mock_get_token:
            client = ApiClient(configuration=config)

            # The __init__ calls __refresh_auth_token which should call __get_new_token
            mock_get_token.assert_called_once_with(skip_backoff=False)

    def test_force_refresh_auth_token_success(self):
        """Test force_refresh_auth_token with success"""
        auth_settings = AuthenticationSettings(key_id='test-key', key_secret='test-secret')
        config = Configuration(
            base_url="http://localhost:8080",
            authentication_settings=auth_settings
        )

        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=config)

            with patch.object(client, '_ApiClient__get_new_token', return_value='new-token') as mock_get_token:
                result = client.force_refresh_auth_token()

                self.assertTrue(result)
                mock_get_token.assert_called_once_with(skip_backoff=True)
                self.assertEqual(client.configuration.AUTH_TOKEN, 'new-token')

    def test_force_refresh_auth_token_failure(self):
        """Test force_refresh_auth_token with failure"""
        auth_settings = AuthenticationSettings(key_id='test-key', key_secret='test-secret')
        config = Configuration(
            base_url="http://localhost:8080",
            authentication_settings=auth_settings
        )

        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=config)

            with patch.object(client, '_ApiClient__get_new_token', return_value=None):
                result = client.force_refresh_auth_token()

                self.assertFalse(result)

    def test_force_refresh_auth_token_without_auth_settings(self):
        """Test force_refresh_auth_token without authentication settings"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)
            client.configuration.authentication_settings = None

            result = client.force_refresh_auth_token()

            self.assertFalse(result)

    def test_get_new_token_success(self):
        """Test __get_new_token with successful token generation"""
        auth_settings = AuthenticationSettings(key_id='test-key', key_secret='test-secret')
        config = Configuration(
            base_url="http://localhost:8080",
            authentication_settings=auth_settings
        )

        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=config)

            mock_token = Token(token='new-token')

            with patch.object(client, 'call_api', return_value=mock_token) as mock_call_api:
                result = client._ApiClient__get_new_token(skip_backoff=True)

                self.assertEqual(result, 'new-token')
                self.assertEqual(client._token_refresh_failures, 0)
                mock_call_api.assert_called_once_with(
                    '/token', 'POST',
                    header_params={'Content-Type': 'application/json'},
                    body={'keyId': 'test-key', 'keySecret': 'test-secret'},
                    _return_http_data_only=True,
                    response_type='Token'
                )

    def test_get_new_token_with_missing_credentials(self):
        """Test __get_new_token with missing credentials"""
        auth_settings = AuthenticationSettings(key_id=None, key_secret=None)
        config = Configuration(
            base_url="http://localhost:8080",
            authentication_settings=auth_settings
        )

        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=config)

            result = client._ApiClient__get_new_token(skip_backoff=True)

            self.assertIsNone(result)
            self.assertEqual(client._token_refresh_failures, 1)

    def test_get_new_token_with_authorization_exception(self):
        """Test __get_new_token with AuthorizationException"""
        auth_settings = AuthenticationSettings(key_id='test-key', key_secret='test-secret')
        config = Configuration(
            base_url="http://localhost:8080",
            authentication_settings=auth_settings
        )

        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=config)

            auth_exception = AuthorizationException(status=401, reason='Invalid credentials')
            auth_exception._error_code = 'INVALID_CREDENTIALS'

            with patch.object(client, 'call_api', side_effect=auth_exception):
                result = client._ApiClient__get_new_token(skip_backoff=True)

                self.assertIsNone(result)
                self.assertEqual(client._token_refresh_failures, 1)

    def test_get_new_token_with_general_exception(self):
        """Test __get_new_token with general exception"""
        auth_settings = AuthenticationSettings(key_id='test-key', key_secret='test-secret')
        config = Configuration(
            base_url="http://localhost:8080",
            authentication_settings=auth_settings
        )

        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=config)

            with patch.object(client, 'call_api', side_effect=Exception('Network error')):
                result = client._ApiClient__get_new_token(skip_backoff=True)

                self.assertIsNone(result)
                self.assertEqual(client._token_refresh_failures, 1)

    def test_get_new_token_with_backoff_max_failures(self):
        """Test __get_new_token with max failures reached"""
        auth_settings = AuthenticationSettings(key_id='test-key', key_secret='test-secret')
        config = Configuration(
            base_url="http://localhost:8080",
            authentication_settings=auth_settings
        )

        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=config)
            client._token_refresh_failures = 5

            result = client._ApiClient__get_new_token(skip_backoff=False)

            self.assertIsNone(result)

    def test_get_new_token_with_backoff_active(self):
        """Test __get_new_token with active backoff"""
        auth_settings = AuthenticationSettings(key_id='test-key', key_secret='test-secret')
        config = Configuration(
            base_url="http://localhost:8080",
            authentication_settings=auth_settings
        )

        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=config)
            client._token_refresh_failures = 2
            client._last_token_refresh_attempt = time.time()  # Just attempted

            result = client._ApiClient__get_new_token(skip_backoff=False)

            self.assertIsNone(result)

    def test_get_new_token_with_backoff_expired(self):
        """Test __get_new_token with expired backoff"""
        auth_settings = AuthenticationSettings(key_id='test-key', key_secret='test-secret')
        config = Configuration(
            base_url="http://localhost:8080",
            authentication_settings=auth_settings
        )

        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=config)
            client._token_refresh_failures = 1
            client._last_token_refresh_attempt = time.time() - 10  # 10 seconds ago (backoff is 2 seconds)

            mock_token = Token(token='new-token')

            with patch.object(client, 'call_api', return_value=mock_token):
                result = client._ApiClient__get_new_token(skip_backoff=False)

                self.assertEqual(result, 'new-token')
                self.assertEqual(client._token_refresh_failures, 0)

    def test_get_default_headers_with_basic_auth(self):
        """Test __get_default_headers with basic auth in URL"""
        config = Configuration(
            server_api_url="http://user:pass@localhost:8080/api"
        )

        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            with patch('urllib3.util.parse_url') as mock_parse_url:
                # Mock the parsed URL with auth
                mock_parsed = Mock()
                mock_parsed.auth = 'user:pass'
                mock_parse_url.return_value = mock_parsed

                with patch('urllib3.util.make_headers', return_value={'Authorization': 'Basic dXNlcjpwYXNz'}):
                    client = ApiClient(configuration=config, header_name='X-Custom', header_value='value')

                    self.assertIn('Authorization', client.default_headers)
                    self.assertIn('X-Custom', client.default_headers)
                    self.assertEqual(client.default_headers['X-Custom'], 'value')

    def test_deserialize_file_without_content_disposition(self):
        """Test __deserialize_file without Content-Disposition header"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            response = Mock()
            response.getheader.return_value = None
            response.data = b'file content'

            with patch('tempfile.mkstemp', return_value=(123, '/tmp/tempfile')) as mock_mkstemp, \
                 patch('os.close') as mock_close, \
                 patch('os.remove') as mock_remove:

                result = client._ApiClient__deserialize_file(response)

                self.assertEqual(result, '/tmp/tempfile')
                mock_close.assert_called_once_with(123)
                mock_remove.assert_called_once_with('/tmp/tempfile')

    def test_deserialize_file_with_string_data(self):
        """Test __deserialize_file with string data"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            response = Mock()
            response.getheader.return_value = 'attachment; filename="test.txt"'
            response.data = 'string content'

            with patch('tempfile.mkstemp', return_value=(123, '/tmp/tempfile')) as mock_mkstemp, \
                 patch('os.close') as mock_close, \
                 patch('os.remove') as mock_remove, \
                 patch('builtins.open', mock_open()) as mock_file:

                result = client._ApiClient__deserialize_file(response)

                self.assertTrue(result.endswith('test.txt'))

    def test_deserialize_model(self):
        """Test __deserialize_model with swagger model"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            # Create a mock model class
            mock_model_class = Mock()
            mock_model_class.swagger_types = {'field1': 'str', 'field2': 'int'}
            mock_model_class.attribute_map = {'field1': 'field1', 'field2': 'field2'}
            mock_instance = Mock()
            mock_model_class.return_value = mock_instance

            data = {'field1': 'value1', 'field2': 42}

            result = client._ApiClient__deserialize_model(data, mock_model_class)

            mock_model_class.assert_called_once()
            self.assertIsNotNone(result)

    def test_deserialize_model_no_swagger_types(self):
        """Test __deserialize_model with no swagger_types"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            mock_model_class = Mock()
            mock_model_class.swagger_types = None

            data = {'field1': 'value1'}

            result = client._ApiClient__deserialize_model(data, mock_model_class)

            self.assertEqual(result, data)

    def test_deserialize_model_with_extra_fields(self):
        """Test __deserialize_model with extra fields not in swagger_types"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            mock_model_class = Mock()
            mock_model_class.swagger_types = {'field1': 'str'}
            mock_model_class.attribute_map = {'field1': 'field1'}

            # Return a dict instance to simulate dict-like model
            mock_instance = {}
            mock_model_class.return_value = mock_instance

            data = {'field1': 'value1', 'extra_field': 'extra_value'}

            result = client._ApiClient__deserialize_model(data, mock_model_class)

            # Extra field should be added to instance
            self.assertIn('extra_field', result)

    def test_deserialize_model_with_real_child_model(self):
        """Test __deserialize_model with get_real_child_model"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            mock_model_class = Mock()
            mock_model_class.swagger_types = {'field1': 'str'}
            mock_model_class.attribute_map = {'field1': 'field1'}

            mock_instance = Mock()
            mock_instance.get_real_child_model.return_value = 'ChildModel'
            mock_model_class.return_value = mock_instance

            data = {'field1': 'value1', 'type': 'ChildModel'}

            with patch.object(client, '_ApiClient__deserialize', return_value='child_instance') as mock_deserialize:
                result = client._ApiClient__deserialize_model(data, mock_model_class)

                # Should call __deserialize again with child model name
                mock_deserialize.assert_called()


    def test_call_api_no_retry_with_body(self):
        """Test __call_api_no_retry with body parameter"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch.object(client, 'request', return_value=Mock(status=200)) as mock_request:
                mock_response = Mock()
                mock_response.status = 200
                mock_request.return_value = mock_response

                client.call_api(
                    '/test',
                    'POST',
                    body={'key': 'value'},
                    _return_http_data_only=False
                )

                # Verify body was passed
                call_args = mock_request.call_args
                self.assertIsNotNone(call_args[1].get('body'))

    def test_deserialize_date_import_error(self):
        """Test __deserialize_date when dateutil is not available"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            # Mock import error for dateutil
            import sys
            original_modules = sys.modules.copy()

            try:
                # Remove dateutil from modules
                if 'dateutil.parser' in sys.modules:
                    del sys.modules['dateutil.parser']

                # This should return the string as-is when dateutil is not available
                with patch('builtins.__import__', side_effect=ImportError('No module named dateutil')):
                    result = client._ApiClient__deserialize_date('2025-01-01')
                    # When dateutil import fails, it returns the string
                    self.assertEqual(result, '2025-01-01')
            finally:
                # Restore modules
                sys.modules.update(original_modules)

    def test_deserialize_datetime_import_error(self):
        """Test __deserialize_datatime when dateutil is not available"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            # Mock import error for dateutil
            import sys
            original_modules = sys.modules.copy()

            try:
                # Remove dateutil from modules
                if 'dateutil.parser' in sys.modules:
                    del sys.modules['dateutil.parser']

                # This should return the string as-is when dateutil is not available
                with patch('builtins.__import__', side_effect=ImportError('No module named dateutil')):
                    result = client._ApiClient__deserialize_datatime('2025-01-01T12:00:00')
                    # When dateutil import fails, it returns the string
                    self.assertEqual(result, '2025-01-01T12:00:00')
            finally:
                # Restore modules
                sys.modules.update(original_modules)

    def test_request_with_exception_having_code_attribute(self):
        """Test request method with exception having code attribute"""
        metrics_collector = Mock()
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config, metrics_collector=metrics_collector)

            error = Exception('Test error')
            error.code = 404

            with patch.object(client.rest_client, 'GET', side_effect=error):
                with self.assertRaises(Exception):
                    client.request('GET', 'http://localhost:8080/test')

                # Verify metrics were recorded with code
                metrics_collector.record_api_request_time.assert_called_once()
                call_args = metrics_collector.record_api_request_time.call_args
                self.assertEqual(call_args[1]['status'], '404')

    def test_request_url_parsing_exception(self):
        """Test request method when URL parsing fails"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            with patch('urllib.parse.urlparse', side_effect=Exception('Parse error')):
                with patch.object(client.rest_client, 'GET', return_value=Mock(status=200)) as mock_get:
                    client.request('GET', 'http://localhost:8080/test')
                    # Should still work, falling back to using url as-is
                    mock_get.assert_called_once()

    def test_deserialize_model_without_get_real_child_model(self):
        """Test __deserialize_model without get_real_child_model returning None"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            mock_model_class = Mock()
            mock_model_class.swagger_types = {'field1': 'str'}
            mock_model_class.attribute_map = {'field1': 'field1'}

            mock_instance = Mock()
            mock_instance.get_real_child_model.return_value = None  # Returns None
            mock_model_class.return_value = mock_instance

            data = {'field1': 'value1'}

            result = client._ApiClient__deserialize_model(data, mock_model_class)

            # Should return mock_instance since get_real_child_model returned None
            self.assertEqual(result, mock_instance)

    def test_deprecated_force_refresh_auth_token(self):
        """Test deprecated __force_refresh_auth_token method"""
        auth_settings = AuthenticationSettings(key_id='test-key', key_secret='test-secret')
        config = Configuration(
            base_url="http://localhost:8080",
            authentication_settings=auth_settings
        )

        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=config)

            with patch.object(client, 'force_refresh_auth_token', return_value=True) as mock_public:
                # Call the deprecated private method
                result = client._ApiClient__force_refresh_auth_token()

                self.assertTrue(result)
                mock_public.assert_called_once()

    def test_deserialize_with_none_data(self):
        """Test __deserialize with None data"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            result = client.deserialize_class(None, 'str')
            self.assertIsNone(result)

    def test_deserialize_with_http_model_class(self):
        """Test __deserialize with http_models class"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            # Test with a class that should be fetched from http_models
            with patch('conductor.client.http.models.Token') as MockToken:
                mock_instance = Mock()
                mock_instance.swagger_types = {'token': 'str'}
                mock_instance.attribute_map = {'token': 'token'}
                MockToken.return_value = mock_instance

                # This will trigger line 313 (getattr(http_models, klass))
                result = client.deserialize_class({'token': 'test-token'}, 'Token')

                # Verify Token was instantiated
                MockToken.assert_called_once()

    def test_deserialize_bytes_to_str_direct(self):
        """Test __deserialize_bytes_to_str directly"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            # Test the private method directly
            result = client._ApiClient__deserialize_bytes_to_str(b'hello world')
            self.assertEqual(result, 'hello world')

    def test_deserialize_datetime_with_unicode_encode_error(self):
        """Test __deserialize_primitive with bytes and str causing UnicodeEncodeError"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            # This tests line 647-648 (UnicodeEncodeError handling)
            # Use a mock to force the UnicodeEncodeError path
            with patch.object(client, '_ApiClient__deserialize_bytes_to_str', return_value='decoded'):
                result = client.deserialize_class(b'test', str)
                self.assertEqual(result, 'decoded')

    def test_deserialize_model_with_extra_fields_not_dict_instance(self):
        """Test __deserialize_model where instance is not a dict but has extra fields"""
        with patch.object(ApiClient, '_ApiClient__refresh_auth_token'):
            client = ApiClient(configuration=self.config)

            mock_model_class = Mock()
            mock_model_class.swagger_types = {'field1': 'str'}
            mock_model_class.attribute_map = {'field1': 'field1'}

            # Return a non-dict instance to skip lines 728-730
            mock_instance = object()  # Plain object, not dict
            mock_model_class.return_value = mock_instance

            data = {'field1': 'value1', 'extra': 'value2'}

            result = client._ApiClient__deserialize_model(data, mock_model_class)

            # Should return the mock_instance as-is
            self.assertEqual(result, mock_instance)


if __name__ == '__main__':
    unittest.main()
