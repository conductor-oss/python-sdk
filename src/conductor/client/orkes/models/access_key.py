from conductor.client.orkes.models.access_key_status import AccessKeyStatus
from typing import Optional


class AccessKey:
    def __init__(self, id: str, status: AccessKeyStatus, created_at: int) -> None:
        self._id: str = id
        self._status: Optional[AccessKeyStatus] = status
        self._created_at: int = created_at

        if self._status is None:
            self._status = AccessKeyStatus.ACTIVE

    @property
    def id(self) -> str:
        """Gets the id of this CreatedAccessKey.  # noqa: E501

        :return: The id of this CreatedAccessKey.  # noqa: E501
        :rtype: idRef
        """
        return self._id

    @id.setter
    def id(self, id: str) -> None:
        """Sets the id of this CreatedAccessKey.

        :param id: The id of this CreatedAccessKey.  # noqa: E501
        :type: str
        """
        self._id = id

    @property
    def status(self) -> Optional[AccessKeyStatus]:
        """Gets the status of this CreatedAccessKey.  # noqa: E501

        :return: The status of this CreatedAccessKey.  # noqa: E501
        :rtype: str
        """
        return self._status

    @status.setter
    def status(self, status: AccessKeyStatus) -> None:
        """Sets the status of this CreatedAccessKey.

        :param id: The status of this CreatedAccessKey.  # noqa: E501
        :type: str
        """
        self._status = status

    @property
    def created_at(self) -> int:
        """Gets the created_at of this CreatedAccessKey.  # noqa: E501

        :return: The created_at of this CreatedAccessKey.  # noqa: E501
        :rtype: int
        """
        return self._created_at

    def __eq__(self, other: object) -> bool:
        """Returns true if both objects are equal"""
        if not isinstance(other, AccessKey):
            return False

        return self.id == other.id and self.status == other.status

    def __ne__(self, other: object) -> bool:
        """Returns true if both objects are not equal"""
        return not self == other
