from typing import ClassVar, Dict
from conductor.client.codegen.models import BulkResponse


class BulkResponseAdapter(BulkResponse):
    swagger_types: ClassVar[Dict[str, str]] = {  # type: ignore[misc]
        **BulkResponse.swagger_types,
        "bulk_successful_results": "list[str]",
        "message": "str",
    }

    attribute_map: ClassVar[Dict[str, str]] = {  # type: ignore[misc]
        **BulkResponse.attribute_map,
        "message": "message",
    }

    def __init__(
        self, bulk_error_results=None, bulk_successful_results=None, message=None, *_args, **_kwargs
    ):
        if bulk_error_results is None:
            bulk_error_results = {}
        if bulk_successful_results is None:
            bulk_successful_results = []

        super().__init__(
            bulk_error_results=bulk_error_results,
            bulk_successful_results=bulk_successful_results,
        )
        self._message = "Bulk Request has been processed."
        if message is not None:
            self._message = message

    @property
    def message(self):
        """Gets the message of this BulkResponse.  # noqa: E501


        :return: The message of this BulkResponse.  # noqa: E501
        :rtype: str
        """
        return self._message

    @message.setter
    def message(self, message):
        """Sets the message of this BulkResponse.


        :param message: The message of this BulkResponse.  # noqa: E501
        :type: str
        """

        self._message = message

    def append_successful_response(self, result) -> None:
        """Appends a successful result to the bulk_successful_results list.

        :param result: The successful result to append
        :type result: T
        """
        self._bulk_successful_results.append(result)

    def append_failed_response(self, id: str, error_message: str) -> None:
        """Appends a failed response to the bulk_error_results map.

        :param id: The entity ID
        :type id: str
        :param error_message: The error message
        :type error_message: str
        """
        self._bulk_error_results[id] = error_message
