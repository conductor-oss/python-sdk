from typing import Dict, Any


class CreatedAccessKey:
    def __init__(self, id: str, secret: str) -> None:
        self._id: str = id
        self._secret: str = secret

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
    def secret(self) -> str:
        """Gets the secret of this CreatedAccessKey.  # noqa: E501

        :return: The secret of this CreatedAccessKey.  # noqa: E501
        :rtype: str
        """
        return self._secret

    @secret.setter
    def secret(self, secret: str) -> None:
        """Sets the secret of this CreatedAccessKey.

        :param id: The secret of this CreatedAccessKey.  # noqa: E501
        :type: str
        """
        self._secret = secret

    def __eq__(self, other: object) -> bool:
        """Returns true if both objects are equal"""
        if not isinstance(other, CreatedAccessKey):
            return False

        return self.id == other.id and self.secret == other.secret

    def __ne__(self, other: object) -> bool:
        """Returns true if both objects are not equal"""
        return not self == other

    @classmethod
    def from_dict(cls, obj: Dict[str, Any]) -> "CreatedAccessKey":
        return cls(
            id=obj["id"],
            secret=obj["secret"],
        )
