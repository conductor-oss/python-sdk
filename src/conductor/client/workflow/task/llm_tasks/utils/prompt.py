from typing import ClassVar, Dict


class Prompt(object):
    swagger_types: ClassVar[Dict[str, str]] = {"name": "str", "variables": "str"}

    attribute_map: ClassVar[Dict[str, str]] = {"name": "promptName", "variables": "promptVariables"}

    def __init__(self, name: str, variables: Dict[str, object]):
        self._name: str = name
        self._variables: Dict[str, object] = variables

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @property
    def variables(self) -> Dict[str, object]:
        return self._variables

    @variables.setter
    def variables(self, variables: Dict[str, object]) -> None:
        self._variables = variables
