from typing import ClassVar, Dict


class Prompt(object):
    swagger_types: ClassVar[Dict[str, str]] = {"name": "str", "variables": "str"}

    attribute_map: ClassVar[Dict[str, str]] = {"name": "promptName", "variables": "promptVariables"}

    def __init__(self, name: str, variables: Dict[str, object]):
        self._name = name
        self._variables = variables

    @property
    def name(self) -> str:
        return self._name

    @property
    def variables(self) -> str:
        return self._variables

    @name.setter
    def name(self, name: str):
        self._name = name

    @variables.setter
    def variables(self, variables: str):
        self._variables = variables
