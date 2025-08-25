from __future__ import annotations

from typing import ClassVar, Dict, Optional

from conductor.client.http.models.workflow_task import WorkflowTask


class WorkflowTaskAdapter(WorkflowTask):
    pass


class CacheConfig:  # shared
    swagger_types: ClassVar[Dict[str, str]] = {"key": "str", "ttl_in_second": "int"}

    attribute_map: ClassVar[Dict[str, str]] = {
        "key": "key",
        "ttl_in_second": "ttlInSecond",
    }

    def __init__(self, key: Optional[str] = None, ttl_in_second: Optional[int] = None):
        self._key = key
        self._ttl_in_second = ttl_in_second

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, key):
        self._key = key

    @property
    def ttl_in_second(self):
        return self._ttl_in_second

    @ttl_in_second.setter
    def ttl_in_second(self, ttl_in_second):
        self._ttl_in_second = ttl_in_second
