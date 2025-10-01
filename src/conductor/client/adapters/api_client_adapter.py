import logging

from conductor.client.codegen.api_client import ApiClient
from conductor.client.configuration.configuration import Configuration
from conductor.client.adapters.rest_adapter import RESTClientObjectAdapter

from conductor.client.codegen.rest import AuthorizationException, ApiException

logger = logging.getLogger(Configuration.get_logging_formatted_name(__name__))


class ApiClientAdapter(ApiClient):
    def __init__(self, configuration=None, header_name=None, header_value=None, cookie=None):
        """Initialize the API client adapter with httpx-based REST client."""
        self.configuration = configuration or Configuration()

        # Create httpx-compatible REST client directly
        self.rest_client = RESTClientObjectAdapter(connection=configuration.http_connection)

        self.default_headers = self._ApiClient__get_default_headers(header_name, header_value)
        self.cookie = cookie
        self._ApiClient__refresh_auth_token()

    def __call_api(
        self,
        resource_path,
        method,
        path_params=None,
        query_params=None,
        header_params=None,
        body=None,
        post_params=None,
        files=None,
        response_type=None,
        auth_settings=None,
        _return_http_data_only=None,
        collection_formats=None,
        _preload_content=True,
        _request_timeout=None,
    ):
        try:
            logger.debug(
                "HTTP request method: %s; resource_path: %s; header_params: %s",
                method,
                resource_path,
                header_params,
            )
            return self.__call_api_no_retry(
                resource_path=resource_path,
                method=method,
                path_params=path_params,
                query_params=query_params,
                header_params=header_params,
                body=body,
                post_params=post_params,
                files=files,
                response_type=response_type,
                auth_settings=auth_settings,
                _return_http_data_only=_return_http_data_only,
                collection_formats=collection_formats,
                _preload_content=_preload_content,
                _request_timeout=_request_timeout,
            )
        except AuthorizationException as ae:
            if ae.token_expired or ae.invalid_token:
                token_status = "expired" if ae.token_expired else "invalid"
                logger.warning(
                    "HTTP response from: %s; token_status: %s; status code: 401 - obtaining new token",
                    resource_path,
                    token_status,
                )
                # if the token has expired or is invalid, lets refresh the token
                self.__force_refresh_auth_token()
                # and now retry the same request
                return self.__call_api_no_retry(
                    resource_path=resource_path,
                    method=method,
                    path_params=path_params,
                    query_params=query_params,
                    header_params=header_params,
                    body=body,
                    post_params=post_params,
                    files=files,
                    response_type=response_type,
                    auth_settings=auth_settings,
                    _return_http_data_only=_return_http_data_only,
                    collection_formats=collection_formats,
                    _preload_content=_preload_content,
                    _request_timeout=_request_timeout,
                )
            raise ae
        except ApiException as e:
            logger.error(
                "HTTP request failed url: %s status: %s; reason: %s",
                resource_path,
                e.status,
                e.reason,
            )
            raise e
