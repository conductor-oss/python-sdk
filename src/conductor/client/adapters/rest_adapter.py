import io
import logging
from typing import Optional, Dict, Any, Union, Tuple

import httpx
from httpx import Response, RequestError, HTTPStatusError, TimeoutException

from conductor.client.codegen.rest import (
    ApiException,
    AuthorizationException,
    RESTClientObject,
)
from conductor.client.configuration.configuration import Configuration

logger = logging.getLogger(Configuration.get_logging_formatted_name(__name__))


class RESTResponse(io.IOBase):
    """HTTP response wrapper for httpx responses."""

    def __init__(self, response: Response):
        self.status = response.status_code
        self.reason = response.reason_phrase
        self.resp = response
        self.headers = response.headers
        
        # Log HTTP protocol version
        http_version = getattr(response, 'http_version', 'Unknown')
        logger.debug(f"HTTP response received - Status: {self.status}, Protocol: {http_version}")
        
        # Log HTTP/2 usage
        if http_version == "HTTP/2":
            logger.info(f"HTTP/2 connection established - URL: {response.url}")
        elif http_version == "HTTP/1.1":
            logger.debug(f"HTTP/1.1 connection used - URL: {response.url}")
        else:
            logger.debug(f"HTTP protocol version: {http_version} - URL: {response.url}")

    def getheaders(self):
        """Get response headers."""
        return self.headers

    def getheader(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a specific response header."""
        return self.headers.get(name, default)

    @property
    def data(self) -> bytes:
        """Get response data as bytes."""
        return self.resp.content

    @property
    def text(self) -> str:
        """Get response data as text."""
        return self.resp.text
    
    @property
    def http_version(self) -> str:
        """Get the HTTP protocol version used."""
        return getattr(self.resp, 'http_version', 'Unknown')
    
    def is_http2(self) -> bool:
        """Check if HTTP/2 was used for this response."""
        return self.http_version == "HTTP/2"


class RESTClientObjectAdapter(RESTClientObject):
    """HTTP client adapter using httpx instead of requests."""

    def __init__(self, connection: Optional[httpx.Client] = None):
        """Initialize the REST client with httpx."""
        # Don't call super().__init__() to avoid requests initialization
        self.connection = connection or httpx.Client(
            timeout=httpx.Timeout(120.0),
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            http2=True  # added explicit configuration
        )

    def close(self):
        """Close the HTTP client connection."""
        if hasattr(self, "connection") and self.connection:
            self.connection.close()
    
    def check_http2_support(self, url: str) -> bool:
        """Check if the server supports HTTP/2 by making a test request."""
        try:
            logger.info(f"Checking HTTP/2 support for: {url}")
            response = self.GET(url)
            is_http2 = response.is_http2()
            
            if is_http2:
                logger.info(f"✓ HTTP/2 supported by {url}")
            else:
                logger.info(f"✗ HTTP/2 not supported by {url}, using {response.http_version}")
            
            return is_http2
        except Exception as e:
            logger.error(f"Failed to check HTTP/2 support for {url}: {e}")
            return False

    def request(
        self,
        method: str,
        url: str,
        query_params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Union[str, bytes, Dict[str, Any]]] = None,
        post_params: Optional[Dict[str, Any]] = None,
        _preload_content: bool = True,
        _request_timeout: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> RESTResponse:
        """Perform HTTP request using httpx.

        :param method: HTTP request method
        :param url: HTTP request URL
        :param query_params: Query parameters in the URL
        :param headers: HTTP request headers
        :param body: Request JSON body for `application/json`
        :param post_params: Request post parameters for
                           `application/x-www-form-urlencoded` and `multipart/form-data`
        :param _preload_content: If False, return raw response without reading content
        :param _request_timeout: Timeout setting for this request
        """
        method = method.upper()
        assert method in ["GET", "HEAD", "DELETE", "POST", "PUT", "PATCH", "OPTIONS"]

        if post_params and body:
            raise ValueError(
                "body parameter cannot be used with post_params parameter."
            )

        post_params = post_params or {}
        headers = headers or {}

        # Set default timeout
        if _request_timeout is not None:
            if isinstance(_request_timeout, (int, float)):
                timeout = httpx.Timeout(_request_timeout)
            else:
                # Tuple format: (connect_timeout, read_timeout)
                timeout = httpx.Timeout(_request_timeout)
        else:
            timeout = httpx.Timeout(120.0)

        # Set default content type
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        try:
            # Log the request attempt
            logger.debug(f"Making HTTP request - Method: {method}, URL: {url}")
            
            # Prepare request parameters
            request_kwargs = {
                "method": method,
                "url": url,
                "headers": headers,
                "timeout": timeout,
            }

            # Handle query parameters
            if query_params:
                request_kwargs["params"] = query_params

            # Handle request body
            if method in ["POST", "PUT", "PATCH", "OPTIONS", "DELETE"]:
                if body is not None:
                    if isinstance(body, (dict, list)):
                        # JSON body
                        request_kwargs["json"] = body
                    elif isinstance(body, str):
                        # String body
                        request_kwargs["content"] = body.encode("utf-8")
                    elif isinstance(body, bytes):
                        # Bytes body
                        request_kwargs["content"] = body
                    else:
                        # Try to serialize as JSON
                        request_kwargs["json"] = body
                elif post_params:
                    # Form data
                    request_kwargs["data"] = post_params

            # Make the request
            response = self.connection.request(**request_kwargs)

            # Create RESTResponse wrapper
            rest_response = RESTResponse(response)

            # Handle authentication errors
            if rest_response.status in [401, 403]:
                raise AuthorizationException(http_resp=rest_response)

            # Handle other HTTP errors
            if not 200 <= rest_response.status <= 299:
                raise ApiException(http_resp=rest_response)

            return rest_response

        except HTTPStatusError as e:
            rest_response = RESTResponse(e.response)
            if rest_response.status in [401, 403]:
                raise AuthorizationException(http_resp=rest_response) from e
            raise ApiException(http_resp=rest_response) from e
        except (RequestError, TimeoutException) as e:
            raise ApiException(status=0, reason=str(e)) from e

    def GET(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        _preload_content: bool = True,
        _request_timeout: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> RESTResponse:
        """Perform GET request."""
        return self.request(
            "GET",
            url,
            headers=headers,
            query_params=query_params,
            _preload_content=_preload_content,
            _request_timeout=_request_timeout,
        )

    def HEAD(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        _preload_content: bool = True,
        _request_timeout: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> RESTResponse:
        """Perform HEAD request."""
        return self.request(
            "HEAD",
            url,
            headers=headers,
            query_params=query_params,
            _preload_content=_preload_content,
            _request_timeout=_request_timeout,
        )

    def OPTIONS(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        post_params: Optional[Dict[str, Any]] = None,
        body: Optional[Union[str, bytes, Dict[str, Any]]] = None,
        _preload_content: bool = True,
        _request_timeout: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> RESTResponse:
        """Perform OPTIONS request."""
        return self.request(
            "OPTIONS",
            url,
            headers=headers,
            query_params=query_params,
            post_params=post_params,
            body=body,
            _preload_content=_preload_content,
            _request_timeout=_request_timeout,
        )

    def DELETE(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        body: Optional[Union[str, bytes, Dict[str, Any]]] = None,
        _preload_content: bool = True,
        _request_timeout: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> RESTResponse:
        """Perform DELETE request."""
        return self.request(
            "DELETE",
            url,
            headers=headers,
            query_params=query_params,
            body=body,
            _preload_content=_preload_content,
            _request_timeout=_request_timeout,
        )

    def POST(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        post_params: Optional[Dict[str, Any]] = None,
        body: Optional[Union[str, bytes, Dict[str, Any]]] = None,
        _preload_content: bool = True,
        _request_timeout: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> RESTResponse:
        """Perform POST request."""
        return self.request(
            "POST",
            url,
            headers=headers,
            query_params=query_params,
            post_params=post_params,
            body=body,
            _preload_content=_preload_content,
            _request_timeout=_request_timeout,
        )

    def PUT(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        post_params: Optional[Dict[str, Any]] = None,
        body: Optional[Union[str, bytes, Dict[str, Any]]] = None,
        _preload_content: bool = True,
        _request_timeout: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> RESTResponse:
        """Perform PUT request."""
        return self.request(
            "PUT",
            url,
            headers=headers,
            query_params=query_params,
            post_params=post_params,
            body=body,
            _preload_content=_preload_content,
            _request_timeout=_request_timeout,
        )

    def PATCH(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        post_params: Optional[Dict[str, Any]] = None,
        body: Optional[Union[str, bytes, Dict[str, Any]]] = None,
        _preload_content: bool = True,
        _request_timeout: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> RESTResponse:
        """Perform PATCH request."""
        return self.request(
            "PATCH",
            url,
            headers=headers,
            query_params=query_params,
            post_params=post_params,
            body=body,
            _preload_content=_preload_content,
            _request_timeout=_request_timeout,
        )
