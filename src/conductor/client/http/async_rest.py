import io
import json
import re

import httpx
from six.moves.urllib.parse import urlencode


class RESTResponse(io.IOBase):

    def __init__(self, resp):
        self.status = resp.status_code
        # httpx.Response doesn't have reason attribute, derive it from status_code
        self.reason = resp.reason_phrase if hasattr(resp, 'reason_phrase') else self._get_reason_phrase(resp.status_code)
        self.resp = resp
        self.headers = resp.headers

    def _get_reason_phrase(self, status_code):
        """Get HTTP reason phrase from status code."""
        phrases = {
            200: 'OK',
            201: 'Created',
            202: 'Accepted',
            204: 'No Content',
            301: 'Moved Permanently',
            302: 'Found',
            304: 'Not Modified',
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            405: 'Method Not Allowed',
            409: 'Conflict',
            429: 'Too Many Requests',
            500: 'Internal Server Error',
            502: 'Bad Gateway',
            503: 'Service Unavailable',
            504: 'Gateway Timeout',
        }
        return phrases.get(status_code, 'Unknown')

    def getheaders(self):
        return self.headers


class AsyncRESTClientObject(object):
    def __init__(self, connection=None):
        if connection is None:
            # Create httpx async client with HTTP/2 support and connection pooling
            # HTTP/2 provides:
            # - Request/response multiplexing (multiple requests over single connection)
            # - Header compression (HPACK)
            # - Server push capability
            # - Binary protocol (more efficient than HTTP/1.1 text)
            limits = httpx.Limits(
                max_connections=100,      # Total connections across all hosts
                max_keepalive_connections=50,  # Persistent connections to keep alive
                keepalive_expiry=30.0     # Keep connections alive for 30 seconds
            )

            # Retry configuration for transient failures
            transport = httpx.AsyncHTTPTransport(
                retries=3,  # Retry up to 3 times
                http2=True  # Enable HTTP/2 support
            )

            self.connection = httpx.AsyncClient(
                limits=limits,
                transport=transport,
                timeout=httpx.Timeout(120.0, connect=10.0),  # 120s total, 10s connect
                follow_redirects=True,
                http2=True  # Enable HTTP/2 globally
            )
            self._owns_connection = True
        else:
            self.connection = connection
            self._owns_connection = False

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Explicitly close the httpx async client."""
        if self._owns_connection and self.connection is not None:
            await self.connection.aclose()

    async def request(self, method, url, query_params=None, headers=None,
                body=None, post_params=None, _preload_content=True,
                _request_timeout=None):
        """Perform async requests using httpx with HTTP/2 support.

        :param method: http request method
        :param url: http request url
        :param query_params: query parameters in the url
        :param headers: http request headers
        :param body: request json body, for `application/json`
        :param post_params: request post parameters,
                            `application/x-www-form-urlencoded`
                            and `multipart/form-data`
        :param _preload_content: if False, the httpx.Response object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        """
        method = method.upper()
        assert method in ['GET', 'HEAD', 'DELETE', 'POST', 'PUT',
                          'PATCH', 'OPTIONS']

        if post_params and body:
            raise ValueError(
                "body parameter cannot be used with post_params parameter."
            )

        post_params = post_params or {}
        headers = headers or {}

        # Convert timeout to httpx format
        if _request_timeout is not None:
            if isinstance(_request_timeout, tuple):
                timeout = httpx.Timeout(_request_timeout[1], connect=_request_timeout[0])
            else:
                timeout = httpx.Timeout(_request_timeout)
        else:
            timeout = None  # Use client default

        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'

        try:
            # For `POST`, `PUT`, `PATCH`, `OPTIONS`, `DELETE`
            if method in ['POST', 'PUT', 'PATCH', 'OPTIONS', 'DELETE']:
                if query_params:
                    url += '?' + urlencode(query_params)
                if re.search('json', headers['Content-Type'], re.IGNORECASE) or isinstance(body, str):
                    request_body = '{}'
                    if body is not None:
                        request_body = json.dumps(body)
                        if isinstance(body, str):
                            request_body = request_body.strip('"')
                    r = await self.connection.request(
                        method, url,
                        content=request_body,
                        timeout=timeout,
                        headers=headers
                    )
                else:
                    # Cannot generate the request from given parameters
                    msg = """Cannot prepare a request message for provided
                             arguments. Please check that your arguments match
                             declared content type."""
                    raise ApiException(status=0, reason=msg)
            # For `GET`, `HEAD`
            else:
                r = await self.connection.request(
                    method, url,
                    params=query_params,
                    timeout=timeout,
                    headers=headers
                )
        except httpx.TimeoutException as e:
            msg = f"Request timeout: {e}"
            raise ApiException(status=0, reason=msg)
        except httpx.ConnectError as e:
            msg = f"Connection error: {e}"
            raise ApiException(status=0, reason=msg)
        except Exception as e:
            msg = "{0}\n{1}".format(type(e).__name__, str(e))
            raise ApiException(status=0, reason=msg)

        if _preload_content:
            r = RESTResponse(r)

        if r.status == 401 or r.status == 403:
            raise AuthorizationException(http_resp=r)

        if not 200 <= r.status <= 299:
            raise ApiException(http_resp=r)

        return r

    async def GET(self, url, headers=None, query_params=None, _preload_content=True,
            _request_timeout=None):
        return await self.request("GET", url,
                            headers=headers,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            query_params=query_params)

    async def HEAD(self, url, headers=None, query_params=None, _preload_content=True,
             _request_timeout=None):
        return await self.request("HEAD", url,
                            headers=headers,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            query_params=query_params)

    async def OPTIONS(self, url, headers=None, query_params=None, post_params=None,
                body=None, _preload_content=True, _request_timeout=None):
        return await self.request("OPTIONS", url,
                            headers=headers,
                            query_params=query_params,
                            post_params=post_params,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            body=body)

    async def DELETE(self, url, headers=None, query_params=None, body=None,
               _preload_content=True, _request_timeout=None):
        return await self.request("DELETE", url,
                            headers=headers,
                            query_params=query_params,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            body=body)

    async def POST(self, url, headers=None, query_params=None, post_params=None,
             body=None, _preload_content=True, _request_timeout=None):
        return await self.request("POST", url,
                            headers=headers,
                            query_params=query_params,
                            post_params=post_params,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            body=body)

    async def PUT(self, url, headers=None, query_params=None, post_params=None,
            body=None, _preload_content=True, _request_timeout=None):
        return await self.request("PUT", url,
                            headers=headers,
                            query_params=query_params,
                            post_params=post_params,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            body=body)

    async def PATCH(self, url, headers=None, query_params=None, post_params=None,
              body=None, _preload_content=True, _request_timeout=None):
        return await self.request("PATCH", url,
                            headers=headers,
                            query_params=query_params,
                            post_params=post_params,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            body=body)


class ApiException(Exception):

    def __init__(self, status=None, reason=None, http_resp=None, body=None):
        if http_resp:
            self.status = http_resp.status
            self.code = http_resp.status
            self.reason = http_resp.reason
            self.body = http_resp.resp.text
            try:
                if http_resp.resp.text:
                    error = json.loads(http_resp.resp.text)
                    self.message = error['message']
                else:
                    self.message = http_resp.resp.text
            except Exception as e:
                self.message = http_resp.resp.text
            self.headers = http_resp.getheaders()
        else:
            self.status = status
            self.code = status
            self.reason = reason
            self.body = body
            self.message = body
            self.headers = None

    def __str__(self):
        """Custom error messages for exception"""
        error_message = "({0})\n" \
                        "Reason: {1}\n".format(self.status, self.reason)
        if self.headers:
            error_message += "HTTP response headers: {0}\n".format(
                self.headers)

        if self.body:
            error_message += "HTTP response body: {0}\n".format(self.body)

        return error_message

    def is_not_found(self) -> bool:
        return self.code == 404

class AuthorizationException(ApiException):
    def __init__(self, status=None, reason=None, http_resp=None, body=None):
        try:
            data = json.loads(http_resp.resp.text)
            if 'error' in data:
                self._error_code = data['error']
            else:
                self._error_code = ''
        except (Exception):
            self._error_code = ''
        super().__init__(status, reason, http_resp, body)

    @property
    def error_code(self):
        return self._error_code

    @property
    def status_code(self):
        return self.status

    @property
    def token_expired(self) -> bool:
        return self._error_code == 'EXPIRED_TOKEN'

    @property
    def invalid_token(self) -> bool:
        return self._error_code == 'INVALID_TOKEN'

    def __str__(self):
        """Custom error messages for exception"""
        error_message = f'authorization error: {self._error_code}.  status_code: {self.status}, reason: {self.reason}'

        if self.headers:
            error_message += f', headers: {self.headers}'

        if self.body:
            error_message += f', response: {self.body}'

        return error_message
