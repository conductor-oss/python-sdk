from __future__ import annotations
from copy import deepcopy
from typing import Dict, Any, Optional, ClassVar


class KafkaPublishInput:
    swagger_types: ClassVar[Dict[str, str]] = {
        "_bootstrap_servers": "str",
        "_key": "str",
        "_key_serializer": "str",
        "_value": "str",
        "_request_timeout_ms": "str",
        "_max_block_ms": "str",
        "_headers": "dict[str, Any]",
        "_topic": "str",
    }

    attribute_map: ClassVar[Dict[str, str]] = {
        "_bootstrap_servers": "bootStrapServers",
        "_key": "key",
        "_key_serializer": "keySerializer",
        "_value": "value",
        "_request_timeout_ms": "requestTimeoutMs",
        "_max_block_ms": "maxBlockMs",
        "_headers": "headers",
        "_topic": "topic",
    }

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        key: Optional[str] = None,
        key_serializer: Optional[str] = None,
        value: Optional[str] = None,
        request_timeout_ms: Optional[str] = None,
        max_block_ms: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
        topic: Optional[str] = None,
    ) -> None:
        self._bootstrap_servers: Optional[str] = deepcopy(bootstrap_servers)
        self._key: Optional[str] = deepcopy(key)
        self._key_serializer: Optional[str] = deepcopy(key_serializer)
        self._value: Optional[str] = deepcopy(value)
        self._request_timeout_ms: Optional[str] = deepcopy(request_timeout_ms)
        self._max_block_ms: Optional[str] = deepcopy(max_block_ms)
        self._headers: Optional[Dict[str, Any]] = deepcopy(headers)
        self._topic: Optional[str] = deepcopy(topic)

    @property
    def bootstrap_servers(self) -> Optional[str]:
        return self._bootstrap_servers

    @property
    def key(self) -> Optional[str]:
        return self._key

    @property
    def key_serializer(self) -> Optional[str]:
        return self._key_serializer

    @property
    def value(self) -> Optional[str]:
        return self._value

    @property
    def request_timeout_ms(self) -> Optional[str]:
        return self._request_timeout_ms

    @property
    def max_block_ms(self) -> Optional[str]:
        return self._max_block_ms

    @property
    def headers(self) -> Optional[Dict[str, Any]]:
        return self._headers

    @property
    def topic(self) -> Optional[str]:
        return self._topic
