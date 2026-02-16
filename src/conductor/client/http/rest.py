import io
import json
import os
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


class RESTClientObject(object):
    def __init__(self, connection=None):
        if connection is None:
            self._http2_enabled = self._is_http2_enabled()
            self.connection = self._create_default_httpx_client()
            self._owns_connection = True
        else:
            self.connection = connection
            self._owns_connection = False
            self._http2_enabled = None

    def _is_http2_enabled(self) -> bool:
        # Default to HTTP/2 enabled. Some environments (proxies/LBs) may be unstable with long-lived HTTP/2.
        val = os.getenv("CONDUCTOR_HTTP2_ENABLED", "true").strip().lower()
        return val not in ("0", "false", "no", "off")

    def _create_default_httpx_client(self) -> httpx.Client:
        # Create httpx client with connection pooling.
        # Use HTTP/2 when enabled (default), but allow opting out via CONDUCTOR_HTTP2_ENABLED.
        limits = httpx.Limits(
            max_connections=100,           # Total connections across all hosts
            max_keepalive_connections=50,  # Persistent connections to keep alive
            keepalive_expiry=30.0          # Keep connections alive for 30 seconds
        )

        transport = httpx.HTTPTransport(
            retries=3,  # Retry up to 3 times for eligible transport errors
            http2=bool(self._http2_enabled)
        )

        return httpx.Client(
            limits=limits,
            transport=transport,
            timeout=httpx.Timeout(120.0, connect=10.0),  # 120s total, 10s connect
            follow_redirects=True,
            http2=bool(self._http2_enabled)
        )

    def _reset_connection(self) -> None:
        if not getattr(self, "_owns_connection", False):
            return
        try:
            if getattr(self, "connection", None) is not None:
                self.connection.close()
        except Exception:
            pass
        self.connection = self._create_default_httpx_client()

    def __del__(self):
        """Cleanup httpx client on object destruction."""
        if hasattr(self, '_owns_connection') and self._owns_connection:
            if hasattr(self, 'connection') and self.connection is not None:
                try:
                    self.connection.close()
                except Exception:
                    pass

    def close(self):
        """Explicitly close the httpx client."""
        if self._owns_connection and self.connection is not None:
            self.connection.close()

    def request(self, method, url, query_params=None, headers=None,
                body=None, post_params=None, _preload_content=True,
                _request_timeout=None):
        """Perform requests using httpx with HTTP/2 support.

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
        idempotent_methods = {'GET', 'HEAD', 'OPTIONS', 'PUT', 'DELETE'}

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

        for attempt in range(2):
            try:
                # For `POST`, `PUT`, `PATCH`, `OPTIONS`, `DELETE`
                if method in ['POST', 'PUT', 'PATCH', 'OPTIONS', 'DELETE']:
                    request_url = url
                    if query_params:
                        request_url += '?' + urlencode(query_params)
                    if re.search('json', headers['Content-Type'], re.IGNORECASE) or isinstance(body, str):
                        request_body = '{}'
                        if body is not None:
                            request_body = json.dumps(body)
                            if isinstance(body, str):
                                request_body = request_body.strip('"')
                        r = self.connection.request(
                            method, request_url,
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
                    r = self.connection.request(
                        method, url,
                        params=query_params,
                        timeout=timeout,
                        headers=headers
                    )
                break
            except (httpx.ProtocolError, httpx.ReadError, httpx.WriteError) as e:
                # A stale/broken keep-alive connection can cause protocol errors (esp. with HTTP/2).
                # Reset the client to recover without requiring process restart.
                # Only auto-retry idempotent methods to avoid duplicating side effects.
                if attempt == 0 and self._owns_connection:
                    self._reset_connection()
                    if method in idempotent_methods:
                        continue
                msg = f"Protocol error: {e}"
                raise ApiException(status=0, reason=msg)
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

    def GET(self, url, headers=None, query_params=None, _preload_content=True,
            _request_timeout=None):
        return self.request("GET", url,
                            headers=headers,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            query_params=query_params)

    def HEAD(self, url, headers=None, query_params=None, _preload_content=True,
             _request_timeout=None):
        return self.request("HEAD", url,
                            headers=headers,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            query_params=query_params)

    def OPTIONS(self, url, headers=None, query_params=None, post_params=None,
                body=None, _preload_content=True, _request_timeout=None):
        return self.request("OPTIONS", url,
                            headers=headers,
                            query_params=query_params,
                            post_params=post_params,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            body=body)

    def DELETE(self, url, headers=None, query_params=None, body=None,
               _preload_content=True, _request_timeout=None):
        return self.request("DELETE", url,
                            headers=headers,
                            query_params=query_params,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            body=body)

    def POST(self, url, headers=None, query_params=None, post_params=None,
             body=None, _preload_content=True, _request_timeout=None):
        return self.request("POST", url,
                            headers=headers,
                            query_params=query_params,
                            post_params=post_params,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            body=body)

    def PUT(self, url, headers=None, query_params=None, post_params=None,
            body=None, _preload_content=True, _request_timeout=None):
        return self.request("PUT", url,
                            headers=headers,
                            query_params=query_params,
                            post_params=post_params,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            body=body)

    def PATCH(self, url, headers=None, query_params=None, post_params=None,
              body=None, _preload_content=True, _request_timeout=None):
        return self.request("PATCH", url,
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


# Backwards compatible alias for older SDK versions/tests.
# Historically callers imported `RestException` from this module.
RestException = ApiException

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
