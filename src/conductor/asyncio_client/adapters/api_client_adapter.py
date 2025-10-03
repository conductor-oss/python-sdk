from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Dict, Optional

from conductor.asyncio_client.adapters.models import GenerateTokenRequest
from conductor.asyncio_client.configuration import Configuration
from conductor.asyncio_client.http import rest
from conductor.asyncio_client.http.api_client import ApiClient
from conductor.asyncio_client.http.api_response import ApiResponse
from conductor.asyncio_client.http.api_response import T as ApiResponseT
from conductor.asyncio_client.http.exceptions import ApiException

logger = logging.getLogger(Configuration.get_logging_formatted_name(__name__))


class ApiClientAdapter(ApiClient):
    def __init__(self, *args, **kwargs):
        self._token_lock = asyncio.Lock()
        super().__init__(*args, **kwargs)

    async def call_api(
        self,
        method,
        url,
        header_params=None,
        body=None,
        post_params=None,
        _request_timeout=None,
    ) -> rest.RESTResponse:
        """Makes the HTTP request (synchronous)
        :param method: Method to call.
        :param url: Path to method endpoint.
        :param header_params: Header parameters to be
            placed in the request header.
        :param body: Request body.
        :param post_params dict: Request post form parameters,
            for `application/x-www-form-urlencoded`, `multipart/form-data`.
        :param _request_timeout: timeout setting for this request.
        :return: RESTResponse
        """

        try:
            logger.debug(
                "HTTP request method: %s; url: %s; header_params: %s", method, url, header_params
            )
            response_data = await self.rest_client.request(
                method,
                url,
                headers=header_params,
                body=body,
                post_params=post_params,
                _request_timeout=_request_timeout,
            )
            if (
                response_data.status == 401  # noqa: PLR2004 (Unauthorized status code)
                and url != self.configuration.host + "/token"
            ):
                logger.warning(
                    "HTTP response from: %s; status code: 401 - obtaining new token", url
                )
                async with self._token_lock:
                    # The lock is intentionally broad (covers the whole block including the token state)
                    # to avoid race conditions: without it, other coroutines could mis-evaluate
                    # token state during a context switch and trigger redundant refreshes
                    token_expired = (
                        self.configuration.token_update_time > 0
                        and time.time()
                        >= self.configuration.token_update_time
                        + self.configuration.auth_token_ttl_sec
                    )
                    invalid_token = not self.configuration._http_config.api_key.get("api_key")

                    if invalid_token or token_expired:
                        token = await self.refresh_authorization_token()
                    else:
                        token = self.configuration._http_config.api_key["api_key"]
                    header_params["X-Authorization"] = token
                    response_data = await self.rest_client.request(
                        method,
                        url,
                        headers=header_params,
                        body=body,
                        post_params=post_params,
                        _request_timeout=_request_timeout,
                    )
        except ApiException as e:
            logger.error(
                "HTTP request failed url: %s status: %s; reason: %s", url, e.status, e.reason
            )
            raise e

        return response_data

    def response_deserialize(
        self,
        response_data: rest.RESTResponse,
        response_types_map: Optional[Dict[str, ApiResponseT]] = None,
    ) -> ApiResponse[ApiResponseT]:
        """Deserializes response into an object.
        :param response_data: RESTResponse object to be deserialized.
        :param response_types_map: dict of response types.
        :return: ApiResponse
        """

        msg = "RESTResponse.read() must be called before passing it to response_deserialize()"
        assert response_data.data is not None, msg

        response_type = response_types_map.get(str(response_data.status), None)
        if (
            not response_type
            and isinstance(response_data.status, int)
            and 100 <= response_data.status <= 599  # noqa: PLR2004
        ):
            # if not found, look for '1XX', '2XX', etc.
            response_type = response_types_map.get(str(response_data.status)[0] + "XX", None)

        # deserialize response data
        response_text = None
        return_data = None
        try:
            if response_type == "bytearray":
                return_data = response_data.data
            elif response_type == "file":
                return_data = self.__deserialize_file(response_data)
            elif response_type is not None:
                match = None
                content_type = response_data.getheader("content-type")
                if content_type is not None:
                    match = re.search(r"charset=([a-zA-Z\-\d]+)[\s;]?", content_type)
                encoding = match.group(1) if match else "utf-8"
                response_text = response_data.data.decode(encoding)
                return_data = self.deserialize(response_text, response_type, content_type)
        finally:
            if not 200 <= response_data.status <= 299:  #  noqa: PLR2004
                logger.error("Unexpected response status code: %s", response_data.status)
                raise ApiException.from_response(
                    http_resp=response_data,
                    body=response_text,
                    data=return_data,
                )

        return ApiResponse(
            status_code=response_data.status,
            data=return_data,
            headers=response_data.getheaders(),
            raw_data=response_data.data,
        )

    async def refresh_authorization_token(self):
        obtain_new_token_response = await self.obtain_new_token()
        token = obtain_new_token_response.get("token")
        self.configuration._http_config.api_key["api_key"] = token
        self.configuration.token_update_time = time.time()
        logger.debug("New auth token been set")
        return token

    async def obtain_new_token(self):
        body = GenerateTokenRequest(
            key_id=self.configuration.auth_key,
            key_secret=self.configuration.auth_secret,
        )
        _param = self.param_serialize(
            method="POST",
            resource_path="/token",
            body=body.to_dict(),
        )
        response = await self.call_api(
            *_param,
        )
        await response.read()
        return json.loads(response.data)

    @classmethod
    def get_default(cls):
        """Return new instance of ApiClient.
        This method returns newly created, based on default constructor,
        object of ApiClient class or returns a copy of default
        ApiClient.
        :return: The ApiClient object.
        """
        if cls._default is None:
            cls._default = ApiClientAdapter()
        return cls._default
