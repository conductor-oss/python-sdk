import asyncio
import json
import logging
import time

from conductor.asyncio_client.adapters.models import GenerateTokenRequest
from conductor.asyncio_client.http import rest
from conductor.asyncio_client.http.api_client import ApiClient
from conductor.asyncio_client.http.exceptions import ApiException

logger = logging.getLogger(__name__)


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
            response_data = await self.rest_client.request(
                method,
                url,
                headers=header_params,
                body=body,
                post_params=post_params,
                _request_timeout=_request_timeout,
            )
            if (
                response_data.status == 401
                and url != self.configuration.host + "/token"
            ):  # noqa: PLR2004 (Unauthorized status code)
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
                    invalid_token = not self.configuration._http_config.api_key.get(
                        "api_key"
                    )

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
            raise e

        return response_data

    async def refresh_authorization_token(self):
        obtain_new_token_response = await self.obtain_new_token()
        token = obtain_new_token_response.get("token")
        self.configuration._http_config.api_key["api_key"] = token
        self.configuration.token_update_time = time.time()
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
