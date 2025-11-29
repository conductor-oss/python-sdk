import base64
import datetime
import logging
import mimetypes
import os
import re
import tempfile
import time
from typing import Dict
import uuid

import six
import urllib3
from requests.structures import CaseInsensitiveDict
from six.moves.urllib.parse import quote

import conductor.client.http.models as http_models
from conductor.client.configuration.configuration import Configuration
from conductor.client.http import async_rest
from conductor.client.http.async_rest import AuthorizationException

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(
        __name__
    )
)


class AsyncApiClient(object):
    """Async version of ApiClient - exact 1:1 copy with async/await."""

    PRIMITIVE_TYPES = (float, bool, bytes, six.text_type) + six.integer_types
    NATIVE_TYPES_MAPPING = {
        'int': int,
        'long': int if six.PY3 else long,  # noqa: F821
        'float': float,
        'str': str,
        'bool': bool,
        'date': datetime.date,
        'datetime': datetime.datetime,
        'object': object,
    }

    def __init__(
            self,
            configuration=None,
            header_name=None,
            header_value=None,
            cookie=None,
            metrics_collector=None
    ):
        if configuration is None:
            configuration = Configuration()
        self.configuration = configuration

        self.async_rest_client = async_rest.AsyncRESTClientObject()

        self.default_headers = self.__get_default_headers(
            header_name, header_value
        )

        self.cookie = cookie

        # Token refresh backoff tracking
        self._token_refresh_failures = 0
        self._last_token_refresh_attempt = 0
        self._max_token_refresh_failures = 5  # Stop after 5 consecutive failures

        # Metrics collector for API request tracking
        self.metrics_collector = metrics_collector

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.async_rest_client.close()

    async def close(self):
        """Close the async REST client."""
        await self.async_rest_client.close()

    async def __call_api(
            self, resource_path, method, path_params=None,
            query_params=None, header_params=None, body=None, post_params=None,
            files=None, response_type=None, auth_settings=None,
            _return_http_data_only=None, collection_formats=None,
            _preload_content=True, _request_timeout=None):
        try:
            return await self.__call_api_no_retry(
                resource_path=resource_path, method=method, path_params=path_params,
                query_params=query_params, header_params=header_params, body=body, post_params=post_params,
                files=files, response_type=response_type, auth_settings=auth_settings,
                _return_http_data_only=_return_http_data_only, collection_formats=collection_formats,
                _preload_content=_preload_content, _request_timeout=_request_timeout
            )
        except AuthorizationException as ae:
            if ae.token_expired or ae.invalid_token:
                token_status = "expired" if ae.token_expired else "invalid"
                logger.info(
                    f'Authentication token is {token_status}, renewing token... (request: {method} {resource_path})')
                # if the token has expired or is invalid, lets refresh the token
                success = await self.__force_refresh_auth_token()
                if success:
                    logger.debug('Authentication token successfully renewed')
                    # and now retry the same request
                    return await self.__call_api_no_retry(
                        resource_path=resource_path, method=method, path_params=path_params,
                        query_params=query_params, header_params=header_params, body=body, post_params=post_params,
                        files=files, response_type=response_type, auth_settings=auth_settings,
                        _return_http_data_only=_return_http_data_only, collection_formats=collection_formats,
                        _preload_content=_preload_content, _request_timeout=_request_timeout
                    )
                else:
                    logger.error('Failed to renew authentication token. Please check your credentials.')
            raise ae

    async def __call_api_no_retry(
            self, resource_path, method, path_params=None,
            query_params=None, header_params=None, body=None, post_params=None,
            files=None, response_type=None, auth_settings=None,
            _return_http_data_only=None, collection_formats=None,
            _preload_content=True, _request_timeout=None):

        config = self.configuration

        # header parameters
        header_params = header_params or {}
        header_params.update(self.default_headers)
        if self.cookie:
            header_params['Cookie'] = self.cookie
        if header_params:
            header_params = self.sanitize_for_serialization(header_params)
            header_params = dict(self.parameters_to_tuples(header_params,
                                                           collection_formats))

        # path parameters
        if path_params:
            path_params = self.sanitize_for_serialization(path_params)
            path_params = self.parameters_to_tuples(path_params,
                                                    collection_formats)
            for k, v in path_params:
                # specified safe chars, encode everything
                resource_path = resource_path.replace(
                    '{%s}' % k,
                    quote(str(v), safe=config.safe_chars_for_path_param)
                )

        # query parameters
        if query_params:
            query_params = self.sanitize_for_serialization(query_params)
            query_params = self.parameters_to_tuples(query_params,
                                                     collection_formats)

        # post parameters
        if post_params or files:
            post_params = self.prepare_post_parameters(post_params, files)
            post_params = self.sanitize_for_serialization(post_params)
            post_params = self.parameters_to_tuples(post_params,
                                                    collection_formats)

        # auth setting
        auth_headers = None
        if self.configuration.authentication_settings is not None and resource_path != '/token':
            auth_headers = await self.__get_authentication_headers()
        self.update_params_for_auth(
            header_params,
            query_params,
            auth_headers
        )

        # body
        if body:
            body = self.sanitize_for_serialization(body)

        # request url
        url = self.configuration.host + resource_path

        # perform request and return response
        response_data = await self.request(
            method, url, query_params=query_params, headers=header_params,
            post_params=post_params, body=body,
            _preload_content=_preload_content,
            _request_timeout=_request_timeout)

        self.last_response = response_data

        return_data = response_data
        if _preload_content:
            # deserialize response data
            if response_type:
                return_data = self.deserialize(response_data, response_type)
            else:
                return_data = None

        if _return_http_data_only:
            return (return_data)
        else:
            return (return_data, response_data.status,
                    response_data.getheaders())

    def sanitize_for_serialization(self, obj):
        """Builds a JSON POST object.

        If obj is None, return None.
        If obj is str, int, long, float, bool, return directly.
        If obj is bytes, decode to string (UTF-8) or base64 if binary.
        If obj is datetime.datetime, datetime.date
            convert to string in iso8601 format.
        If obj is list, sanitize each element in the list.
        If obj is dict, return the dict.
        If obj is swagger model, return the properties dict.

        :param obj: The data to serialize.
        :return: The serialized form of data.
        """
        if obj is None:
            return None
        elif isinstance(obj, bytes):
            # Handle bytes: try UTF-8 decode, fallback to base64 for binary data
            try:
                return obj.decode('utf-8')
            except UnicodeDecodeError:
                # Binary data - encode as base64 string
                return base64.b64encode(obj).decode('ascii')
        elif isinstance(obj, self.PRIMITIVE_TYPES):
            return obj
        elif isinstance(obj, list):
            return [self.sanitize_for_serialization(sub_obj)
                    for sub_obj in obj]
        elif isinstance(obj, tuple):
            return tuple(self.sanitize_for_serialization(sub_obj)
                         for sub_obj in obj)
        elif isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif isinstance(obj, uuid.UUID): # needed for compatibility with Python 3.7
            return str(obj) # Convert UUID to string

        if isinstance(obj, dict) or isinstance(obj, CaseInsensitiveDict):
            obj_dict = obj
        else:
            # Convert model obj to dict except
            # attributes `swagger_types`, `attribute_map`
            # and attributes which value is not None.
            # Convert attribute name to json key in
            # model definition for request.
            if hasattr(obj, 'attribute_map') and hasattr(obj, 'swagger_types'):
                obj_dict = {obj.attribute_map[attr]: getattr(obj, attr)
                            for attr, _ in six.iteritems(obj.swagger_types)
                            if getattr(obj, attr) is not None}
            else:
                try:
                    obj_dict = {name: getattr(obj, name)
                                for name in vars(obj)
                                if getattr(obj, name) is not None}
                except TypeError:
                    # Fallback to string representation.
                    return str(obj)

        return {key: self.sanitize_for_serialization(val)
                for key, val in six.iteritems(obj_dict)}

    def deserialize(self, response, response_type):
        """Deserializes response into an object.

        :param response: RESTResponse object to be deserialized.
        :param response_type: class literal for
            deserialized object, or string of class name.

        :return: deserialized object.
        """
        # handle file downloading
        # save response body into a tmp file and return the instance
        if response_type == "file":
            return self.__deserialize_file(response)

        # fetch data from response object
        try:
            data = response.resp.json()
        except Exception:
            data = response.resp.text

        try:
            return self.__deserialize(data, response_type)
        except ValueError as e:
            logger.error(f'failed to deserialize data {data} into class {response_type}, reason: {e}')
            return None

    def deserialize_class(self, data, klass):
        return self.__deserialize(data, klass)

    def __deserialize(self, data, klass):
        """Deserializes dict, list, str into an object.

        :param data: dict, list or str.
        :param klass: class literal, or string of class name.

        :return: object.
        """
        if data is None:
            return None

        if isinstance(klass, str):
            if klass.startswith('list['):
                sub_kls = re.match(r'list\[(.*)\]', klass).group(1)
                return [self.__deserialize(sub_data, sub_kls)
                        for sub_data in data]

            if klass.startswith('set['):
                sub_kls = re.match(r'set\[(.*)\]', klass).group(1)
                return set(self.__deserialize(sub_data, sub_kls)
                           for sub_data in data)

            if klass.startswith('dict('):
                sub_kls = re.match(r'dict\(([^,]*), (.*)\)', klass).group(2)
                return {k: self.__deserialize(v, sub_kls)
                        for k, v in six.iteritems(data)}

            # convert str to class
            if klass in self.NATIVE_TYPES_MAPPING:
                klass = self.NATIVE_TYPES_MAPPING[klass]
            else:
                klass = getattr(http_models, klass)

        if klass in self.PRIMITIVE_TYPES:
            return self.__deserialize_primitive(data, klass)
        elif klass is object:
            return self.__deserialize_object(data)
        elif klass == datetime.date:
            return self.__deserialize_date(data)
        elif klass == datetime.datetime:
            return self.__deserialize_datatime(data)
        else:
            return self.__deserialize_model(data, klass)

    async def call_api(self, resource_path, method,
                 path_params=None, query_params=None, header_params=None,
                 body=None, post_params=None, files=None,
                 response_type=None, auth_settings=None,
                 _return_http_data_only=None, collection_formats=None,
                 _preload_content=True, _request_timeout=None):
        """Makes the async HTTP request and returns deserialized data.

        :param resource_path: Path to method endpoint.
        :param method: Method to call.
        :param path_params: Path parameters in the url.
        :param query_params: Query parameters in the url.
        :param header_params: Header parameters to be
            placed in the request header.
        :param body: Request body.
        :param post_params dict: Request post form parameters,
            for `application/x-www-form-urlencoded`, `multipart/form-data`.
        :param auth_settings list: Auth Settings names for the request.
        :param response: Response data type.
        :param files dict: key -> filename, value -> filepath,
            for `multipart/form-data`.
        :param _return_http_data_only: response data without head status code
                                       and headers
        :param collection_formats: dict of collection formats for path, query,
            header, and post parameters.
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return:
            The response directly.
        """
        return await self.__call_api(resource_path, method,
                               path_params, query_params, header_params,
                               body, post_params, files,
                               response_type, auth_settings,
                               _return_http_data_only, collection_formats,
                               _preload_content, _request_timeout)

    async def request(self, method, url, query_params=None, headers=None,
                post_params=None, body=None, _preload_content=True,
                _request_timeout=None):
        """Makes the async HTTP request using AsyncRESTClient."""
        # Extract URI path from URL (remove query params and domain)
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            uri = parsed_url.path or url
        except:
            uri = url

        # Start timing
        start_time = time.time()
        status_code = "unknown"

        try:
            if method == "GET":
                response = await self.async_rest_client.GET(url,
                                            query_params=query_params,
                                            _preload_content=_preload_content,
                                            _request_timeout=_request_timeout,
                                            headers=headers)
            elif method == "HEAD":
                response = await self.async_rest_client.HEAD(url,
                                             query_params=query_params,
                                             _preload_content=_preload_content,
                                             _request_timeout=_request_timeout,
                                             headers=headers)
            elif method == "OPTIONS":
                response = await self.async_rest_client.OPTIONS(url,
                                                query_params=query_params,
                                                headers=headers,
                                                post_params=post_params,
                                                _preload_content=_preload_content,
                                                _request_timeout=_request_timeout,
                                                body=body)
            elif method == "POST":
                response = await self.async_rest_client.POST(url,
                                             query_params=query_params,
                                             headers=headers,
                                             post_params=post_params,
                                             _preload_content=_preload_content,
                                             _request_timeout=_request_timeout,
                                             body=body)
            elif method == "PUT":
                response = await self.async_rest_client.PUT(url,
                                            query_params=query_params,
                                            headers=headers,
                                            post_params=post_params,
                                            _preload_content=_preload_content,
                                            _request_timeout=_request_timeout,
                                            body=body)
            elif method == "PATCH":
                response = await self.async_rest_client.PATCH(url,
                                              query_params=query_params,
                                              headers=headers,
                                              post_params=post_params,
                                              _preload_content=_preload_content,
                                              _request_timeout=_request_timeout,
                                              body=body)
            elif method == "DELETE":
                response = await self.async_rest_client.DELETE(url,
                                               query_params=query_params,
                                               headers=headers,
                                               _preload_content=_preload_content,
                                               _request_timeout=_request_timeout,
                                               body=body)
            else:
                raise ValueError(
                    "http method must be `GET`, `HEAD`, `OPTIONS`,"
                    " `POST`, `PATCH`, `PUT` or `DELETE`."
                )

            # Extract status code from response
            status_code = str(response.status) if hasattr(response, 'status') else "200"

            # Record metrics
            if self.metrics_collector is not None:
                elapsed_time = time.time() - start_time
                self.metrics_collector.record_api_request_time(
                    method=method,
                    uri=uri,
                    status=status_code,
                    time_spent=elapsed_time
                )

            return response

        except Exception as e:
            # Extract status code from exception if available
            if hasattr(e, 'status'):
                status_code = str(e.status)
            elif hasattr(e, 'code'):
                status_code = str(e.code)
            else:
                status_code = "error"

            # Record metrics for failed requests
            if self.metrics_collector is not None:
                elapsed_time = time.time() - start_time
                self.metrics_collector.record_api_request_time(
                    method=method,
                    uri=uri,
                    status=status_code,
                    time_spent=elapsed_time
                )

            # Re-raise the exception
            raise

    def parameters_to_tuples(self, params, collection_formats):
        """Get parameters as list of tuples, formatting collections.

        :param params: Parameters as dict or list of two-tuples
        :param dict collection_formats: Parameter collection formats
        :return: Parameters as list of tuples, collections formatted
        """
        new_params = []
        if collection_formats is None:
            collection_formats = {}
        for k, v in six.iteritems(params) if isinstance(params, dict) else params:  # noqa: E501
            if k in collection_formats:
                collection_format = collection_formats[k]
                if collection_format == 'multi':
                    new_params.extend((k, value) for value in v)
                else:
                    if collection_format == 'ssv':
                        delimiter = ' '
                    elif collection_format == 'tsv':
                        delimiter = '\t'
                    elif collection_format == 'pipes':
                        delimiter = '|'
                    else:  # csv is the default
                        delimiter = ','
                    new_params.append(
                        (k, delimiter.join(str(value) for value in v)))
            else:
                new_params.append((k, v))
        return new_params

    def prepare_post_parameters(self, post_params=None, files=None):
        """Builds form parameters.

        :param post_params: Normal form parameters.
        :param files: File parameters.
        :return: Form parameters with files.
        """
        params = []

        if post_params:
            params = post_params

        if files:
            for k, v in six.iteritems(files):
                if not v:
                    continue
                file_names = v if type(v) is list else [v]
                for n in file_names:
                    with open(n, 'rb') as f:
                        filename = os.path.basename(f.name)
                        filedata = f.read()
                        mimetype = (mimetypes.guess_type(filename)[0] or
                                    'application/octet-stream')
                        params.append(
                            tuple([k, tuple([filename, filedata, mimetype])]))

        return params

    def select_header_accept(self, accepts):
        """Returns `Accept` based on an array of accepts provided.

        :param accepts: List of headers.
        :return: Accept (e.g. application/json).
        """
        if not accepts:
            return

        accepts = [x.lower() for x in accepts]

        if 'application/json' in accepts:
            return 'application/json'
        else:
            return ', '.join(accepts)

    def select_header_content_type(self, content_types):
        """Returns `Content-Type` based on an array of content_types provided.

        :param content_types: List of content-types.
        :return: Content-Type (e.g. application/json).
        """
        if not content_types:
            return 'application/json'

        content_types = [x.lower() for x in content_types]

        if 'application/json' in content_types or '*/*' in content_types:
            return 'application/json'
        else:
            return content_types[0]

    def update_params_for_auth(self, headers, querys, auth_settings):
        """Updates header and query params based on authentication setting.

        :param headers: Header parameters dict to be updated.
        :param querys: Query parameters tuple list to be updated.
        :param auth_settings: Authentication setting dict (from __get_authentication_headers).
        """
        if not auth_settings:
            return

        if 'header' in auth_settings:
            for key, value in auth_settings['header'].items():
                headers[key] = value
        if 'query' in auth_settings:
            for key, value in auth_settings['query'].items():
                querys[key] = value

    def __deserialize_file(self, response):
        """Deserializes body to file

        Saves response body into a file in a temporary folder,
        using the filename from the `Content-Disposition` header if provided.

        :param response:  RESTResponse.
        :return: file path.
        """
        fd, path = tempfile.mkstemp(dir=self.configuration.temp_folder_path)
        os.close(fd)
        os.remove(path)

        content_disposition = response.getheader("Content-Disposition")
        if content_disposition:
            filename = re.search(r'filename=[\'"]?([^\'"\s]+)[\'"]?',
                                 content_disposition).group(1)
            path = os.path.join(os.path.dirname(path), filename)
            response_data = response.data
            with open(path, "wb") as f:
                if isinstance(response_data, str):
                    # change str to bytes so we can write it
                    response_data = response_data.encode('utf-8')
                    f.write(response_data)
                else:
                    f.write(response_data)
        return path

    def __deserialize_primitive(self, data, klass):
        """Deserializes string to primitive type.

        :param data: str.
        :param klass: class literal.

        :return: int, long, float, str, bool.
        """
        try:
            if klass is str and isinstance(data, bytes):
                return self.__deserialize_bytes_to_str(data)
            return klass(data)
        except UnicodeEncodeError:
            return six.text_type(data)
        except TypeError:
            return data

    def __deserialize_bytes_to_str(self, data):
        return data.decode('utf-8')

    def __deserialize_object(self, value):
        """Return a original value.

        :return: object.
        """
        return value

    def __deserialize_date(self, string):
        """Deserializes string to date.

        :param string: str.
        :return: date.
        """
        try:
            from dateutil.parser import parse
            return parse(string).date()
        except ImportError:
            return string
        except ValueError:
            raise async_rest.ApiException(
                status=0,
                reason="Failed to parse `{0}` as date object".format(string)
            )

    def __deserialize_datatime(self, string):
        """Deserializes string to datetime.

        The string should be in iso8601 datetime format.

        :param string: str.
        :return: datetime.
        """
        try:
            from dateutil.parser import parse
            return parse(string)
        except ImportError:
            return string
        except ValueError:
            raise async_rest.ApiException(
                status=0,
                reason=(
                    "Failed to parse `{0}` as datetime object"
                    .format(string)
                )
            )

    def __hasattr(self, object, name):
        return name in object.__class__.__dict__

    def __deserialize_model(self, data, klass):
        """Deserializes list or dict to model.

        :param data: dict, list.
        :param klass: class literal.
        :return: model object.
        """
        if not klass.swagger_types and not self.__hasattr(klass, 'get_real_child_model'):
            return data

        kwargs = {}
        if klass.swagger_types is not None:
            for attr, attr_type in six.iteritems(klass.swagger_types):
                if (data is not None and
                        klass.attribute_map[attr] in data and
                        isinstance(data, (list, dict))):
                    value = data[klass.attribute_map[attr]]
                    kwargs[attr] = self.__deserialize(value, attr_type)

        instance = klass(**kwargs)

        if (isinstance(instance, dict) and
                klass.swagger_types is not None and
                isinstance(data, dict)):
            for key, value in data.items():
                if key not in klass.swagger_types:
                    instance[key] = value
        if self.__hasattr(instance, 'get_real_child_model'):
            klass_name = instance.get_real_child_model(data)
            if klass_name:
                instance = self.__deserialize(data, klass_name)
        return instance

    def get_authentication_headers(self):
        return self.__get_authentication_headers()

    async def __get_authentication_headers(self):
        # If no token yet but we have authentication settings, get initial token
        if self.configuration.AUTH_TOKEN is None:
            if self.configuration.authentication_settings is None:
                return None
            # Initial token generation - apply backoff if there were previous failures
            logger.debug('No auth token found, requesting initial token...')
            token = await self.__get_new_token(skip_backoff=False)
            self.configuration.update_token(token)
            if not token:
                # Failed to get initial token
                return None

        now = round(time.time() * 1000)
        time_since_last_update = now - self.configuration.token_update_time

        if time_since_last_update > self.configuration.auth_token_ttl_msec:
            # time to refresh the token - skip backoff for legitimate renewal
            logger.info('Authentication token TTL expired, renewing token...')
            token = await self.__get_new_token(skip_backoff=True)
            self.configuration.update_token(token)
            if token:
                logger.debug('Authentication token successfully renewed')

        return {
            'header': {
                'X-Authorization': self.configuration.AUTH_TOKEN
            }
        }

    async def force_refresh_auth_token(self) -> bool:
        """
        Forces the token refresh - called when server says token is expired/invalid.
        This is a legitimate renewal, so skip backoff.
        Returns True if token was successfully refreshed, False otherwise.
        """
        if self.configuration.authentication_settings is None:
            return False
        # Token renewal after server rejection - skip backoff (credentials should be valid)
        token = await self.__get_new_token(skip_backoff=True)
        if token:
            self.configuration.update_token(token)
            return True
        return False

    async def __force_refresh_auth_token(self) -> bool:
        """Deprecated: Use force_refresh_auth_token() instead"""
        return await self.force_refresh_auth_token()

    async def __get_new_token(self, skip_backoff: bool = False) -> str:
        """
        Get a new authentication token from the server.

        Args:
            skip_backoff: If True, skip backoff logic. Use this for legitimate token renewals
                         (expired token with valid credentials). If False, apply backoff for
                         invalid credentials.
        """
        # Only apply backoff if not skipping and we have failures
        if not skip_backoff:
            # Check if we should back off due to recent failures
            if self._token_refresh_failures >= self._max_token_refresh_failures:
                logger.error(
                    f'Token refresh has failed {self._token_refresh_failures} times. '
                    'Please check your authentication credentials. '
                    'Stopping token refresh attempts.'
                )
                return None

            # Exponential backoff: 2^failures seconds (1s, 2s, 4s, 8s, 16s)
            if self._token_refresh_failures > 0:
                now = time.time()
                backoff_seconds = 2 ** self._token_refresh_failures
                time_since_last_attempt = now - self._last_token_refresh_attempt

                if time_since_last_attempt < backoff_seconds:
                    remaining = backoff_seconds - time_since_last_attempt
                    logger.warning(
                        f'Token refresh backoff active. Please wait {remaining:.1f}s before next attempt. '
                        f'(Failure count: {self._token_refresh_failures})'
                    )
                    return None

        self._last_token_refresh_attempt = time.time()

        try:
            if self.configuration.authentication_settings.key_id is None or self.configuration.authentication_settings.key_secret is None:
                logger.error('Authentication Key or Secret is not set. Failed to get the auth token')
                self._token_refresh_failures += 1
                return None

            logger.debug('Requesting new authentication token from server')
            response = await self.call_api(
                '/token', 'POST',
                header_params={
                    'Content-Type': self.select_header_content_type(['*/*'])
                },
                body={
                    'keyId': self.configuration.authentication_settings.key_id,
                    'keySecret': self.configuration.authentication_settings.key_secret
                },
                _return_http_data_only=True,
                response_type='Token'
            )

            # Success - reset failure counter
            self._token_refresh_failures = 0
            return response.token

        except AuthorizationException as ae:
            # 401 from /token endpoint - invalid credentials
            self._token_refresh_failures += 1
            logger.error(
                f'Authentication failed when getting token (attempt {self._token_refresh_failures}): '
                f'{ae.status} - {ae.error_code}. '
                'Please check your CONDUCTOR_AUTH_KEY and CONDUCTOR_AUTH_SECRET. '
                f'Will retry with exponential backoff ({2 ** self._token_refresh_failures}s).'
            )
            return None

        except Exception as e:
            # Other errors (network, etc)
            self._token_refresh_failures += 1
            logger.error(
                f'Failed to get new token (attempt {self._token_refresh_failures}): {e.args}'
            )
            return None

    def __get_default_headers(self, header_name: str, header_value: object) -> Dict[str, object]:
        headers = {
            'Accept-Encoding': 'gzip',
        }
        if header_name is not None:
            headers[header_name] = header_value
        parsed = urllib3.util.parse_url(self.configuration.host)
        if parsed.auth is not None:
            encrypted_headers = urllib3.util.make_headers(
                basic_auth=parsed.auth
            )
            for key, value in encrypted_headers.items():
                headers[key] = value
        return headers
