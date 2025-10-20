from __future__ import annotations

from typing import ClassVar, Dict

from conductor.client.codegen.models import IntegrationDef


class IntegrationDefAdapter(IntegrationDef):
    swagger_types: ClassVar[Dict[str, str]] = {
        "category": "str",
        "category_label": "str",
        "configuration": "list[IntegrationDefFormField]",
        "description": "str",
        "enabled": "bool",
        "icon_name": "str",
        "name": "str",
        "tags": "list[str]",
        "type": "str",
        "apis": "list[IntegrationDefApi]",
    }

    attribute_map: ClassVar[Dict[str, str]] = {
        "category": "category",
        "category_label": "categoryLabel",
        "configuration": "configuration",
        "description": "description",
        "enabled": "enabled",
        "icon_name": "iconName",
        "name": "name",
        "tags": "tags",
        "type": "type",
        "apis": "apis",
    }

    def __init__(
        self,
        category=None,
        category_label=None,
        configuration=None,
        description=None,
        enabled=None,
        icon_name=None,
        name=None,
        tags=None,
        type=None,
        apis=None,
    ):
        self._category = None
        self._category_label = None
        self._configuration = None
        self._description = None
        self._enabled = None
        self._icon_name = None
        self._name = None
        self._tags = None
        self._type = None
        self._apis = None
        self.discriminator = None
        if category is not None:
            self.category = category
        if category_label is not None:
            self.category_label = category_label
        if configuration is not None:
            self.configuration = configuration
        if description is not None:
            self.description = description
        if enabled is not None:
            self.enabled = enabled
        if icon_name is not None:
            self.icon_name = icon_name
        if name is not None:
            self.name = name
        if tags is not None:
            self.tags = tags
        if type is not None:
            self.type = type
        if apis is not None:
            self.apis = apis

    @property
    def apis(self):
        return self._apis

    @apis.setter
    def apis(self, apis):
        self._apis = apis

    @IntegrationDef.category.setter
    def category(self, category):
        """Sets the category of this IntegrationUpdate.


        :param category: The category of this IntegrationUpdate.  # noqa: E501
        :type: str
        """
        allowed_values = [
            "API",
            "AI_MODEL",
            "VECTOR_DB",
            "RELATIONAL_DB",
            "MESSAGE_BROKER",
            "GIT",
            "EMAIL",
            "MCP",
            "CLOUD",
        ]
        if category not in allowed_values:
            raise ValueError(
                "Invalid value for `category` ({0}), must be one of {1}".format(
                    category, allowed_values
                )
            )

        self._category = category
