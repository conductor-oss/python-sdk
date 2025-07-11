from dataclasses import dataclass, field
from typing import Optional
from abc import ABC
import six


@dataclass
class Auditable(ABC):
    """
    Abstract base class for objects that need auditing information.

    Equivalent to the Java Auditable class from Conductor.
    """
    swagger_types = {
        'owner_app': 'str',
        'create_time': 'int',
        'update_time': 'int',
        'created_by': 'str',
        'updated_by': 'str'
    }

    attribute_map = {
        'owner_app': 'ownerApp',
        'create_time': 'createTime',
        'update_time': 'updateTime',
        'created_by': 'createdBy',
        'updated_by': 'updatedBy'
    }
    _owner_app: Optional[str] = field(default=None, repr=False)
    _create_time: Optional[int] = field(default=None, repr=False)
    _update_time: Optional[int] = field(default=None, repr=False)
    _created_by: Optional[str] = field(default=None, repr=False)
    _updated_by: Optional[str] = field(default=None, repr=False)

    @property
    def owner_app(self) -> Optional[str]:
        return self._owner_app

    @owner_app.setter
    def owner_app(self, value: Optional[str]) -> None:
        self._owner_app = value

    @property
    def create_time(self) -> Optional[int]:
        return self._create_time

    @create_time.setter
    def create_time(self, value: Optional[int]) -> None:
        self._create_time = value

    @property
    def update_time(self) -> Optional[int]:
        return self._update_time

    @update_time.setter
    def update_time(self, value: Optional[int]) -> None:
        self._update_time = value

    @property
    def created_by(self) -> Optional[str]:
        return self._created_by

    @created_by.setter
    def created_by(self, value: Optional[str]) -> None:
        self._created_by = value

    @property
    def updated_by(self) -> Optional[str]:
        return self._updated_by

    @updated_by.setter
    def updated_by(self, value: Optional[str]) -> None:
        self._updated_by = value

    def get_create_time(self) -> int:
        """Returns create_time or 0 if None - maintains Java API compatibility"""
        return 0 if self._create_time is None else self._create_time

    def get_update_time(self) -> int:
        """Returns update_time or 0 if None - maintains Java API compatibility"""
        return 0 if self._update_time is None else self._update_time

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}
        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if value is not None:
                result[attr] = value
        return result