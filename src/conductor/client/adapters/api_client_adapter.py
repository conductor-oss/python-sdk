import logging
import time

from conductor.client.codegen.api_client import ApiClient
from conductor.client.configuration.configuration import Configuration
from conductor.client.adapters.rest_adapter import RESTClientObjectAdapter
from conductor.client.exceptions.auth_401_policy import Auth401Policy, Auth401Handler

from conductor.client.codegen.rest import AuthorizationException, ApiException

logger = logging.getLogger(Configuration.get_logging_formatted_name(__name__))


class ApiClientAdapter(ApiClient):
    def __init__(
        self, configuration=None, header_name=None, header_value=None, cookie=None
    ):
        """Initialize the API client adapter with httpx-based REST client."""
        self.configuration = configuration or Configuration()

        # Create httpx-compatible REST client
        self.rest_client = RESTClientObjectAdapter(
            connection=self.configuration.http_connection
        )

        self.default_headers = self._ApiClient__get_default_headers(
            header_name, header_value
        )
        self.cookie = cookie

        # Initialize 401 policy handler BEFORE calling refresh_auth_token
        # because refresh_auth_token can trigger call_api which needs auth_401_handler
        auth_401_policy = Auth401Policy(
            max_attempts=self.configuration.auth_401_max_attempts,
            base_delay_ms=self.configuration.auth_401_base_delay_ms,
            max_delay_ms=self.configuration.auth_401_max_delay_ms,
            jitter_percent=self.configuration.auth_401_jitter_percent,
            stop_behavior=self.configuration.auth_401_stop_behavior,
        )
        self.auth_401_handler = Auth401Handler(auth_401_policy)

        # Call refresh_auth_token AFTER auth_401_handler is initialized
        self._ApiClient__refresh_auth_token()

    def call_api(
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
        async_req=None,
        _return_http_data_only=None,
        collection_formats=None,
        _preload_content=True,
        _request_timeout=None,
    ):
        # Handle async requests by delegating to parent
        if async_req:
            return super().call_api(
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
                async_req=async_req,
                _return_http_data_only=_return_http_data_only,
                collection_formats=collection_formats,
                _preload_content=_preload_content,
                _request_timeout=_request_timeout,
            )

        try:
            logger.debug(
                "HTTP request method: %s; resource_path: %s; header_params: %s",
                method,
                resource_path,
                header_params,
            )
            result = self._ApiClient__call_api_no_retry(
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
            # Record successful call to reset 401 attempt counters
            self.auth_401_handler.record_successful_call(resource_path)
            return result
        except AuthorizationException as ae:
            # Handle 401 errors with the new policy
            if ae.status == 401:
                # Check if this is an auth-dependent call that should trigger 401 policy
                if self.auth_401_handler.policy.is_auth_dependent_call(
                    resource_path, method
                ):
                    # Handle 401 with policy (exponential backoff, max attempts, etc.)
                    result = self.auth_401_handler.handle_401_error(
                        resource_path=resource_path,
                        method=method,
                        status_code=ae.status,
                        error_code=getattr(ae, "_error_code", None),
                    )

                    if result["should_retry"]:
                        # Apply exponential backoff delay
                        if result["delay_seconds"] > 0:
                            logger.info(
                                "401 error on %s %s - waiting %.2fs before retry (attempt %d/%d)",
                                method,
                                resource_path,
                                result["delay_seconds"],
                                result["attempt_count"],
                                result["max_attempts"],
                            )
                            time.sleep(result["delay_seconds"])

                        # Try to refresh token and retry
                        self._ApiClient__force_refresh_auth_token()
                        return self._ApiClient__call_api_no_retry(
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
                    else:
                        # Max attempts reached - stop worker
                        logger.error(
                            "401 error on %s %s - max attempts (%d) reached, stopping worker",
                            method,
                            resource_path,
                            result["max_attempts"],
                        )
                        raise ae
                else:
                    # Non-auth-dependent call with 401 - use original behavior
                    if ae.token_expired or ae.invalid_token:
                        token_status = "expired" if ae.token_expired else "invalid"
                        logger.warning(
                            "HTTP response from: %s; token_status: %s; status code: 401 - obtaining new token",
                            resource_path,
                            token_status,
                        )
                        self._ApiClient__force_refresh_auth_token()
                        return self._ApiClient__call_api_no_retry(
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
