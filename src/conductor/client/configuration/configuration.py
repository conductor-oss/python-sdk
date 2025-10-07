from __future__ import annotations

import json

import logging
import os
import time
from typing import Optional, Dict, Union

from conductor.shared.configuration.settings.authentication_settings import (
    AuthenticationSettings,
)


class Configuration:
    AUTH_TOKEN = None

    def __init__(
        self,
        base_url: Optional[str] = None,
        debug: bool = False,
        authentication_settings: AuthenticationSettings = None,
        server_api_url: Optional[str] = None,
        auth_token_ttl_min: int = 45,
        proxy: Optional[str] = None,
        proxy_headers: Optional[Dict[str, str]] = None,
        polling_interval: Optional[float] = None,
        domain: Optional[str] = None,
        polling_interval_seconds: Optional[float] = None,
        ssl_ca_cert: Optional[str] = None,
        ca_cert_data: Optional[Union[str, bytes]] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        verify_ssl: Optional[bool] = None,
    ):
        """
        Initialize Conductor client configuration.

        Args:
            base_url: Base URL of the Conductor server (will append /api)
            debug: Enable debug logging
            authentication_settings: Authentication configuration for Orkes
            server_api_url: Full API URL (overrides base_url)
            auth_token_ttl_min: Authentication token time-to-live in minutes
            proxy: Proxy URL for HTTP requests (supports http, https, socks4, socks5)
            proxy_headers: Headers to send with proxy requests (e.g., authentication)

        Environment Variables:
            CONDUCTOR_SERVER_URL: Server URL (e.g., http://localhost:8080/api)
            CONDUCTOR_AUTH_KEY: Authentication key ID
            CONDUCTOR_AUTH_SECRET: Authentication key secret
            CONDUCTOR_PROXY: Proxy URL for HTTP requests
            CONDUCTOR_PROXY_HEADERS: Proxy headers as JSON string or single header value
        """
        if server_api_url is not None:
            self.host = server_api_url
        elif base_url is not None:
            self.host = base_url + "/api"
        else:
            self.host = os.getenv("CONDUCTOR_SERVER_URL")

        if self.host is None or self.host == "":
            self.host = "http://localhost:8080/api"

        self.temp_folder_path = None
        self.__ui_host = os.getenv("CONDUCTOR_UI_SERVER_URL")
        if self.__ui_host is None:
            self.__ui_host = self.host.replace("8080/api", "5001")

        if authentication_settings is not None:
            self.authentication_settings = authentication_settings
        else:
            key = os.getenv("CONDUCTOR_AUTH_KEY")
            secret = os.getenv("CONDUCTOR_AUTH_SECRET")
            if key is not None and secret is not None:
                self.authentication_settings = AuthenticationSettings(
                    key_id=key, key_secret=secret
                )
            else:
                self.authentication_settings = None

        # Debug switch
        self.debug = debug
        # Log format
        self.logger_format = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
        self.is_logger_config_applied = False

        # SSL/TLS verification
        # Set this to false to skip verifying SSL certificate when calling API
        # from https server.
        if verify_ssl is not None:
            self.verify_ssl = verify_ssl
        else:
            self.verify_ssl = self._get_env_bool("CONDUCTOR_VERIFY_SSL", True)
        # Set this to customize the certificate file to verify the peer.
        self.ssl_ca_cert = ssl_ca_cert or os.getenv("CONDUCTOR_SSL_CA_CERT")
        # Set this to verify the peer using PEM (str) or DER (bytes) certificate data.
        self.ca_cert_data = ca_cert_data or os.getenv("CONDUCTOR_SSL_CA_CERT_DATA")
        # client certificate file
        self.cert_file = cert_file or os.getenv("CONDUCTOR_CERT_FILE")
        # client key file
        self.key_file = key_file or os.getenv("CONDUCTOR_KEY_FILE")
        # Set this to True/False to enable/disable SSL hostname verification.
        self.assert_hostname = None

        # Proxy configuration - can be set via parameter or environment variable
        self.proxy = proxy or os.getenv("CONDUCTOR_PROXY")
        # Proxy headers - can be set via parameter or environment variable
        self.proxy_headers = proxy_headers
        if not self.proxy_headers and os.getenv("CONDUCTOR_PROXY_HEADERS"):
            try:
                self.proxy_headers = json.loads(os.getenv("CONDUCTOR_PROXY_HEADERS"))
            except (json.JSONDecodeError, TypeError):
                # If JSON parsing fails, treat as a single header value
                self.proxy_headers = {
                    "Authorization": os.getenv("CONDUCTOR_PROXY_HEADERS")
                }
        # Safe chars for path_param
        self.safe_chars_for_path_param = ""

        # Provide an alterative to requests.Session() for HTTP connection.
        self.http_connection = None

        # not updated yet
        self.token_update_time = 0
        self.auth_token_ttl_msec = auth_token_ttl_min * 60 * 1000

        # Worker properties
        self.polling_interval = polling_interval or self._get_env_float(
            "CONDUCTOR_WORKER_POLL_INTERVAL", 100
        )
        self.domain = domain or os.getenv("CONDUCTOR_WORKER_DOMAIN", "default_domain")
        self.polling_interval_seconds = polling_interval_seconds or self._get_env_float(
            "CONDUCTOR_WORKER_POLL_INTERVAL_SECONDS", 0
        )

    @property
    def debug(self):
        """Debug status

        :param value: The debug status, True or False.
        :type: bool
        """
        return self.__debug

    @debug.setter
    def debug(self, value):
        """Debug status

        :param value: The debug status, True or False.
        :type: bool
        """
        self.__debug = value
        if self.__debug:
            self.__log_level = logging.DEBUG
        else:
            self.__log_level = logging.INFO

    @property
    def logger_format(self):
        """The logger format.

        The logger_formatter will be updated when sets logger_format.

        :param value: The format string.
        :type: str
        """
        return self.__logger_format

    @logger_format.setter
    def logger_format(self, value):
        """The logger format.

        The logger_formatter will be updated when sets logger_format.

        :param value: The format string.
        :type: str
        """
        self.__logger_format = value

    @property
    def log_level(self):
        """The log level.

        The log_level will be updated when sets logger_format.

        :param value: The format string.
        :type: str
        """
        return self.__log_level

    @property
    def ui_host(self):
        """

        The log_level will be updated when sets logger_format.

        :param value: The format string.
        :type: str
        """
        return self.__ui_host

    def apply_logging_config(self, log_format: Optional[str] = None, level=None):
        if self.is_logger_config_applied:
            return
        if log_format is None:
            log_format = self.logger_format
        if level is None:
            level = self.__log_level
        logging.basicConfig(format=log_format, level=level)
        self.is_logger_config_applied = True

    @staticmethod
    def get_logging_formatted_name(name):
        return f"[pid:{os.getpid()}] {name}"

    def update_token(self, token: str) -> None:
        self.AUTH_TOKEN = token
        self.token_update_time = round(time.time() * 1000)

    def _get_env_float(self, env_var: str, default: float) -> float:
        """Get float value from environment variable with default fallback."""
        try:
            value = os.getenv(env_var)
            if value is not None:
                return float(value)
        except (ValueError, TypeError):
            pass
        return default

    def _get_env_bool(self, env_var: str, default: bool) -> bool:
        """Get boolean value from environment variable with default fallback."""
        value = os.getenv(env_var)
        if value is not None:
            return value.lower() in ("true", "1")
        return default

    def get_poll_interval_seconds(self):
        return self.polling_interval_seconds

    def get_poll_interval(self):
        return self.polling_interval

    def get_domain(self):
        return self.domain
