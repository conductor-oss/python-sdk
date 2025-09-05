import pprint

import six


class IntegrationDefApi(object):  # Model from v5.2.6 spec
    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """

    swagger_types = {
        "api": "str",
        "description": "str",
        "input_schema": "SchemaDef",
        "integration_type": "str",
        "output_schema": "SchemaDef",
    }

    attribute_map = {
        "api": "api",
        "description": "description",
        "input_schema": "inputSchema",
        "integration_type": "integrationType",
        "output_schema": "outputSchema",
    }

    def __init__(
        self,
        api=None,
        description=None,
        input_schema=None,
        integration_type=None,
        output_schema=None,
    ):  # noqa: E501
        """IntegrationDefApi - a model defined in Swagger"""  # noqa: E501
        self._api = None
        self._description = None
        self._input_schema = None
        self._integration_type = None
        self._output_schema = None
        self.discriminator = None
        if api is not None:
            self.api = api
        if description is not None:
            self.description = description
        if input_schema is not None:
            self.input_schema = input_schema
        if integration_type is not None:
            self.integration_type = integration_type
        if output_schema is not None:
            self.output_schema = output_schema

    @property
    def api(self):
        """Gets the api of this IntegrationDefApi.  # noqa: E501


        :return: The api of this IntegrationDefApi.  # noqa: E501
        :rtype: str
        """
        return self._api

    @api.setter
    def api(self, api):
        """Sets the api of this IntegrationDefApi.


        :param api: The api of this IntegrationDefApi.  # noqa: E501
        :type: str
        """

        self._api = api

    @property
    def description(self):
        """Gets the description of this IntegrationDefApi.  # noqa: E501


        :return: The description of this IntegrationDefApi.  # noqa: E501
        :rtype: str
        """
        return self._description

    @description.setter
    def description(self, description):
        """Sets the description of this IntegrationDefApi.


        :param description: The description of this IntegrationDefApi.  # noqa: E501
        :type: str
        """

        self._description = description

    @property
    def input_schema(self):
        """Gets the input_schema of this IntegrationDefApi.  # noqa: E501


        :return: The input_schema of this IntegrationDefApi.  # noqa: E501
        :rtype: SchemaDef
        """
        return self._input_schema

    @input_schema.setter
    def input_schema(self, input_schema):
        """Sets the input_schema of this IntegrationDefApi.


        :param input_schema: The input_schema of this IntegrationDefApi.  # noqa: E501
        :type: SchemaDef
        """

        self._input_schema = input_schema

    @property
    def integration_type(self):
        """Gets the integration_type of this IntegrationDefApi.  # noqa: E501


        :return: The integration_type of this IntegrationDefApi.  # noqa: E501
        :rtype: str
        """
        return self._integration_type

    @integration_type.setter
    def integration_type(self, integration_type):
        """Sets the integration_type of this IntegrationDefApi.


        :param integration_type: The integration_type of this IntegrationDefApi.  # noqa: E501
        :type: str
        """

        self._integration_type = integration_type

    @property
    def output_schema(self):
        """Gets the output_schema of this IntegrationDefApi.  # noqa: E501


        :return: The output_schema of this IntegrationDefApi.  # noqa: E501
        :rtype: SchemaDef
        """
        return self._output_schema

    @output_schema.setter
    def output_schema(self, output_schema):
        """Sets the output_schema of this IntegrationDefApi.


        :param output_schema: The output_schema of this IntegrationDefApi.  # noqa: E501
        :type: SchemaDef
        """

        self._output_schema = output_schema

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(
                    map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value)
                )
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(
                    map(
                        lambda item: (
                            (item[0], item[1].to_dict())
                            if hasattr(item[1], "to_dict")
                            else item
                        ),
                        value.items(),
                    )
                )
            else:
                result[attr] = value
        if issubclass(IntegrationDefApi, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, IntegrationDefApi):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
