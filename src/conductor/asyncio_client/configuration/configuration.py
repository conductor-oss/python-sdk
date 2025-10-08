from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional, Union

from conductor.asyncio_client.http.configuration import (
    Configuration as HttpConfiguration,
)


class Configuration:
    """
    Configuration adapter for Orkes Conductor Asyncio Client with environment variable support.

    This adapter wraps the generated HttpConfiguration class and provides:
    - Environment variable support for standard Conductor settings
    - Worker properties configuration (pollInterval, domain, etc.)
    - Backward compatibility with existing code

    Supported Environment Variables:
    --------------------------------
    CONDUCTOR_SERVER_URL: Server URL (e.g., http://localhost:8080/api)
    CONDUCTOR_AUTH_KEY: Authentication key ID
    CONDUCTOR_AUTH_SECRET: Authentication key secret

    Worker Properties (via environment variables):
    ----------------------------------------------
    CONDUCTOR_WORKER_DOMAIN: Default worker domain
    CONDUCTOR_WORKER_POLL_INTERVAL: Polling interval in milliseconds (default: 100)
    CONDUCTOR_WORKER_POLL_INTERVAL_SECONDS: Polling interval in seconds (default: 0)
    CONDUCTOR_WORKER_<TASK_TYPE>_POLLING_INTERVAL: Task-specific polling interval
    CONDUCTOR_WORKER_<TASK_TYPE>_DOMAIN: Task-specific domain

    Authentication Retry Policy (401 Handling):
    -------------------------------------------
    CONDUCTOR_AUTH_401_MAX_ATTEMPTS: Maximum retry attempts per endpoint (default: 6)
    CONDUCTOR_AUTH_401_BASE_DELAY_MS: Base delay in milliseconds (default: 1000.0)
    CONDUCTOR_AUTH_401_MAX_DELAY_MS: Maximum delay cap in milliseconds (default: 60000.0)
    CONDUCTOR_AUTH_401_JITTER_PERCENT: Random jitter percentage 0.0-1.0 (default: 0.2)
    CONDUCTOR_AUTH_401_STOP_BEHAVIOR: Behavior after max attempts: 'stop_worker' or 'continue' (default: 'stop_worker')

    
    Example:
    --------
    ```python
    # Using environment variables
    os.environ['CONDUCTOR_SERVER_URL'] = 'http://localhost:8080/api'
    os.environ['CONDUCTOR_AUTH_KEY'] = 'your_key'
    os.environ['CONDUCTOR_AUTH_SECRET'] = 'your_secret'

    config = Configuration()

    # Or with explicit parameters
    config = Configuration(
        server_url='http://localhost:8080/api',
        auth_key='your_key',
        auth_secret='your_secret'
    )
    ```
    """

    def __init__(
        self,
        server_url: Optional[str] = None,
        auth_key: Optional[str] = None,
        auth_secret: Optional[str] = None,
        debug: bool = False,
        auth_token_ttl_min: int = 45,
        # Worker properties
        polling_interval: Optional[int] = None,
        domain: Optional[str] = None,
        polling_interval_seconds: Optional[int] = None,
        # HTTP Configuration parameters
        api_key: Optional[Dict[str, str]] = None,
        api_key_prefix: Optional[Dict[str, str]] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        access_token: Optional[str] = None,
        server_index: Optional[int] = None,
        server_variables: Optional[Dict[str, str]] = None,
        server_operation_index: Optional[Dict[int, int]] = None,
        server_operation_variables: Optional[Dict[int, Dict[str, str]]] = None,
        ignore_operation_servers: bool = False,
        ssl_ca_cert: Optional[str] = None,
        retries: Optional[int] = None,
        ca_cert_data: Optional[Union[str, bytes]] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        verify_ssl: Optional[bool] = None,
        proxy: Optional[str] = None,
        proxy_headers: Optional[Dict[str, str]] = None,
        # 401-specific configuration
        auth_401_max_attempts: Optional[int] = None,
        auth_401_base_delay_ms: Optional[float] = None,
        auth_401_max_delay_ms: Optional[float] = None,
        auth_401_jitter_percent: Optional[float] = None,
        auth_401_stop_behavior: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize Configuration with environment variable support.

        Parameters:
        -----------
        server_url : str, optional
            Conductor server URL. If not provided, reads from CONDUCTOR_SERVER_URL env var.
        auth_key : str, optional
            Authentication key ID. If not provided, reads from CONDUCTOR_AUTH_KEY env var.
        auth_secret : str, optional
            Authentication key secret. If not provided, reads from CONDUCTOR_AUTH_SECRET env var.
        debug : bool, optional
            Enable debug logging. Default is False.
        polling_interval : int, optional
            Polling interval in milliseconds. If not provided, reads from CONDUCTOR_WORKER_POLL_INTERVAL env var.
        domain : str, optional
            Worker domain. If not provided, reads from CONDUCTOR_WORKER_DOMAIN env var.
        polling_interval_seconds : int, optional
            Polling interval in seconds. If not provided, reads from CONDUCTOR_WORKER_POLL_INTERVAL_SECONDS env var.
        **kwargs : Any
            Additional parameters passed to HttpConfiguration.

        Environment Variables:
        ---------------------
        CONDUCTOR_SERVER_URL: Server URL (e.g., http://localhost:8080/api)
        CONDUCTOR_AUTH_KEY: Authentication key ID
        CONDUCTOR_AUTH_SECRET: Authentication key secret
        CONDUCTOR_PROXY: Proxy URL for HTTP requests
        CONDUCTOR_PROXY_HEADERS: Proxy headers as JSON string or single header value
        """

        # Resolve server URL from parameter or environment variable
        if server_url is not None:
            self.server_url = server_url
        else:
            self.server_url = os.getenv("CONDUCTOR_SERVER_URL")

        if self.server_url is None or self.server_url == "":
            self.server_url = "http://localhost:8080/api"

        # Resolve authentication from parameters or environment variables
        if auth_key is not None:
            self.auth_key = auth_key
        else:
            self.auth_key = os.getenv("CONDUCTOR_AUTH_KEY")

        if auth_secret is not None:
            self.auth_secret = auth_secret
        else:
            self.auth_secret = os.getenv("CONDUCTOR_AUTH_SECRET")

        # Additional worker properties with environment variable fallback
        self.polling_interval = polling_interval or self._get_env_int(
            "CONDUCTOR_WORKER_POLL_INTERVAL", 100
        )
        self.domain = domain or os.getenv("CONDUCTOR_WORKER_DOMAIN", "default_domain")
        self.polling_interval_seconds = polling_interval_seconds or self._get_env_int(
            "CONDUCTOR_WORKER_POLL_INTERVAL_SECONDS", 0
        )

        # Store additional worker properties
        self._worker_properties: Dict[str, Dict[str, Any]] = {}

        # Setup API key authentication if auth credentials are provided
        if api_key is None:
            api_key = {}

        self.__ui_host = os.getenv("CONDUCTOR_UI_SERVER_URL")
        if self.__ui_host is None:
            self.__ui_host = self.server_url.replace("/api", "")

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

        self.logger_format = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"

        # Create the underlying HTTP configuration
        http_config_kwargs = {
            "host": self.server_url,
            "api_key": api_key,
            "api_key_prefix": api_key_prefix,
            "username": username,
            "password": password,
            "access_token": access_token,
            "server_index": server_index,
            "server_variables": server_variables,
            "server_operation_index": server_operation_index,
            "server_operation_variables": server_operation_variables,
            "ignore_operation_servers": ignore_operation_servers,
            "ssl_ca_cert": ssl_ca_cert or os.getenv("CONDUCTOR_SSL_CA_CERT"),
            "retries": retries,
            "ca_cert_data": ca_cert_data or os.getenv("CONDUCTOR_SSL_CA_CERT_DATA"),
            "debug": debug,
        }
        
        # Add SSL parameters if they exist in HttpConfiguration
        if cert_file or os.getenv("CONDUCTOR_CERT_FILE"):
            http_config_kwargs["cert_file"] = cert_file or os.getenv("CONDUCTOR_CERT_FILE")
        if key_file or os.getenv("CONDUCTOR_KEY_FILE"):
            http_config_kwargs["key_file"] = key_file or os.getenv("CONDUCTOR_KEY_FILE")
        if verify_ssl is not None:
            http_config_kwargs["verify_ssl"] = verify_ssl
        elif os.getenv("CONDUCTOR_VERIFY_SSL"):
            http_config_kwargs["verify_ssl"] = self._get_env_bool("CONDUCTOR_VERIFY_SSL", True)
        
        http_config_kwargs.update(kwargs)
        self._http_config = HttpConfiguration(**http_config_kwargs)

        # Set proxy configuration on the HTTP config
        if self.proxy:
            self._http_config.proxy = self.proxy
        if self.proxy_headers:
            self._http_config.proxy_headers = self.proxy_headers

        # Set proxy configuration on the HTTP config
        if self.proxy:
            self._http_config.proxy = self.proxy
        if self.proxy_headers:
            self._http_config.proxy_headers = self.proxy_headers

        # Debug switch and logging setup
        self.__debug = debug
        if self.__debug:
            self.__log_level = logging.DEBUG
        else:
            self.__log_level = logging.INFO
        # Log format
        self.__logger_format = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"

        # Setup logging
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)

        self.is_logger_config_applied = False

        # Orkes Conductor auth token properties
        self.token_update_time = 0
        self.auth_token_ttl_sec = auth_token_ttl_min * 60
        
        # 401-specific configuration
        self.auth_401_max_attempts = auth_401_max_attempts or self._get_env_int(
            "CONDUCTOR_AUTH_401_MAX_ATTEMPTS", 6
        )
        self.auth_401_base_delay_ms = auth_401_base_delay_ms or self._get_env_float(
            "CONDUCTOR_AUTH_401_BASE_DELAY_MS", 1000.0
        )
        self.auth_401_max_delay_ms = auth_401_max_delay_ms or self._get_env_float(
            "CONDUCTOR_AUTH_401_MAX_DELAY_MS", 60000.0
        )
        self.auth_401_jitter_percent = auth_401_jitter_percent or self._get_env_float(
            "CONDUCTOR_AUTH_401_JITTER_PERCENT", 0.2
        )
        self.auth_401_stop_behavior = auth_401_stop_behavior or os.getenv(
            "CONDUCTOR_AUTH_401_STOP_BEHAVIOR", "stop_worker"
        )

    def _get_env_float(self, env_var: str, default: float) -> float:
        """Get float value from environment variable with default fallback."""
        try:
            value = os.getenv(env_var)
            if value is not None:
                return float(value)
        except (ValueError, TypeError):
            self.logger.warning("Invalid float value for %s: %s", env_var, value)
        return default

    def _get_env_int(self, env_var: str, default: int) -> int:
        """Get integer value from environment variable with default fallback."""
        try:
            value = os.getenv(env_var)
            if value is not None:
                return int(value)
        except (ValueError, TypeError):
            self.logger.warning("Invalid float value for %s: %s", env_var, value)
        return default

    def _get_env_bool(self, env_var: str, default: bool) -> bool:
        """Get boolean value from environment variable with default fallback."""
        value = os.getenv(env_var)
        if value is not None:
            return value.lower() in ("true", "1")
        return default

    def get_worker_property_value(
        self, property_name: str, task_type: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get worker property value with task-specific and global fallback.

        Follows the same pattern as the regular client:
        1. Check for task-specific environment variable: CONDUCTOR_WORKER_<TASK_TYPE>_<PROPERTY>
        2. Check for global environment variable: CONDUCTOR_WORKER_<PROPERTY>
        3. Return configured default value

        Parameters:
        -----------
        property_name : str
            Property name (e.g., 'polling_interval', 'domain')
        task_type : str, optional
            Task type for task-specific configuration

        Returns:
        --------
        Any
            Property value or None if not found
        """
        prefix = "conductor_worker"

        # Look for task-specific property
        if task_type:
            key_specific = f"{prefix}_{task_type}_{property_name}".upper()
            value = os.getenv(key_specific)
            if value is not None:
                return self._convert_property_value(property_name, value)

        # Look for global property
        key_global = f"{prefix}_{property_name}".upper()
        value = os.getenv(key_global)
        if value is not None:
            return self._convert_property_value(property_name, value)

        # Return default value
        elif property_name == "domain":
            return self.domain
        elif property_name == "polling_interval":
            return self.polling_interval
        elif property_name == "poll_interval_seconds":
            return self.polling_interval_seconds

        return None

    def _convert_property_value(self, property_name: str, value: str) -> Any:
        """Convert string property value to appropriate type."""
        if property_name == "polling_interval":
            try:
                return float(value)
            except (ValueError, TypeError):
                self.logger.warning("Invalid polling_interval value: %s", value)
                return self.polling_interval
        elif property_name == "polling_interval_seconds":
            try:
                return float(value)
            except (ValueError, TypeError):
                self.logger.warning("Invalid polling_interval_seconds value: %s", value)
                return self.polling_interval_seconds

        # For other properties, return as string
        return value

    def set_worker_property(self, task_type: str, property_name: str, value: Any) -> None:
        """
        Set worker property for a specific task type.

        Parameters:
        -----------
        task_type : str
            Task type name
        property_name : str
            Property name
        value : Any
            Property value
        """
        if task_type not in self._worker_properties:
            self._worker_properties[task_type] = {}
        self._worker_properties[task_type][property_name] = value

    def get_worker_property(self, task_type: str, property_name: str) -> Optional[Any]:
        """
        Get worker property for a specific task type.

        Parameters:
        -----------
        task_type : str
            Task type name
        property_name : str
            Property name

        Returns:
        --------
        Any
            Property value or None if not found
        """
        if task_type in self._worker_properties:
            return self._worker_properties[task_type].get(property_name)
        return None

    def get_polling_interval(self, task_type: Optional[str] = None) -> float:
        """
        Get polling interval for a task type with environment variable support.

        Parameters:
        -----------
        task_type : str, optional
            Task type for task-specific configuration

        Returns:
        --------
        float
            Polling interval in seconds
        """
        value = self.get_worker_property_value("polling_interval", task_type)
        return value if value is not None else self.default_polling_interval

    def get_domain(self, task_type: Optional[str] = None) -> Optional[str]:
        """
        Get domain for a task type with environment variable support.

        Parameters:
        -----------
        task_type : str, optional
            Task type for task-specific configuration

        Returns:
        --------
        str, optional
            Domain name or None
        """
        return self.get_worker_property_value("domain", task_type)

    def get_poll_interval(self, task_type: Optional[str] = None) -> int:
        """
        Get polling interval in milliseconds for a task type with environment variable support.

        Parameters:
        -----------
        task_type : str, optional
            Task type for task-specific configuration

        Returns:
        --------
        int
            Polling interval in milliseconds
        """
        if task_type:
            value = self.get_worker_property_value("polling_interval", task_type)
            if value is not None:
                return int(value)
        return self.polling_interval

    def get_poll_interval_seconds(self) -> int:
        """
        Get polling interval in seconds.

        Returns:
        --------
        int
            Polling interval in seconds
        """
        return self.polling_interval_seconds

    # Properties for commonly used HTTP configuration attributes
    @property
    def host(self) -> str:
        """Get server host URL."""
        if getattr(self, "_http_config", None) is not None:
            return self._http_config.host
        return getattr(self, "_host", None)

    @host.setter
    def host(self, value: str) -> None:
        """Set server host URL."""

        if getattr(self, "_http_config", None) is not None:
            self._http_config.host = value
        self._host = value

    @property
    def debug(self) -> bool:
        """Get debug status."""
        return self._http_config.debug

    @debug.setter
    def debug(self, value: bool) -> None:
        """Set debug status."""
        self._http_config.debug = value
        if value:
            self.logger.setLevel(logging.DEBUG)
            self.__log_level = logging.DEBUG
        else:
            self.logger.setLevel(logging.WARNING)
            self.__log_level = logging.INFO

    @property
    def api_key(self) -> Dict[str, str]:
        """Get API key dictionary."""
        return self._http_config.api_key

    @api_key.setter
    def api_key(self, value: Dict[str, str]) -> None:
        """Set API key dictionary."""
        self._http_config.api_key = value

    @property
    def api_key_prefix(self) -> Dict[str, str]:
        """Get API key prefix dictionary."""
        return self._http_config.api_key_prefix

    @api_key_prefix.setter
    def api_key_prefix(self, value: Dict[str, str]) -> None:
        """Set API key prefix dictionary."""
        self._http_config.api_key_prefix = value

    # Additional commonly used properties
    @property
    def username(self) -> Optional[str]:
        """Get username for HTTP basic authentication."""
        return self._http_config.username

    @username.setter
    def username(self, value: Optional[str]) -> None:
        """Set username for HTTP basic authentication."""
        self._http_config.username = value

    @property
    def password(self) -> Optional[str]:
        """Get password for HTTP basic authentication."""
        return self._http_config.password

    @password.setter
    def password(self, value: Optional[str]) -> None:
        """Set password for HTTP basic authentication."""
        self._http_config.password = value

    @property
    def access_token(self) -> Optional[str]:
        """Get access token."""
        return self._http_config.access_token

    @access_token.setter
    def access_token(self, value: Optional[str]) -> None:
        """Set access token."""
        self._http_config.access_token = value

    @property
    def verify_ssl(self) -> bool:
        """Get SSL verification status."""
        return self._http_config.verify_ssl

    @verify_ssl.setter
    def verify_ssl(self, value: bool) -> None:
        """Set SSL verification status."""
        self._http_config.verify_ssl = value

    @property
    def ssl_ca_cert(self) -> Optional[str]:
        """Get SSL CA certificate path."""
        return self._http_config.ssl_ca_cert

    @ssl_ca_cert.setter
    def ssl_ca_cert(self, value: Optional[str]) -> None:
        """Set SSL CA certificate path."""
        self._http_config.ssl_ca_cert = value

    @property
    def retries(self) -> Optional[int]:
        """Get number of retries."""
        return self._http_config.retries

    @retries.setter
    def retries(self, value: Optional[int]) -> None:
        """Set number of retries."""
        self._http_config.retries = value

    @property
    def logger_format(self) -> str:
        """Get logger format."""
        return self.__logger_format

    @logger_format.setter
    def logger_format(self, value: str) -> None:
        """Set logger format."""
        self.__logger_format = value

    @property
    def log_level(self) -> int:
        """Get log level."""
        return self.__log_level

    def apply_logging_config(self, log_format: Optional[str] = None, level=None):
        """Apply logging configuration for the application."""
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
        """Format a logger name with the current process ID."""
        return f"[pid:{os.getpid()}] {name}"

    @property
    def ui_host(self):
        return self.__ui_host

    # For any other attributes, delegate to the HTTP configuration
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to underlying HTTP configuration."""
        if "_http_config" not in self.__dict__ or self._http_config is None:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )
        return getattr(self._http_config, name)
