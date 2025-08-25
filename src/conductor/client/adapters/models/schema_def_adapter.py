from enum import Enum

from conductor.client.http.models.schema_def import SchemaDef


class SchemaType(str, Enum):
    JSON = ("JSON",)
    AVRO = ("AVRO",)
    PROTOBUF = "PROTOBUF"

    def __str__(self) -> str:
        return self.name.__str__()


class SchemaDefAdapter(SchemaDef):
    @SchemaDef.type.setter
    def type(self, type):
        """Sets the type of this SchemaDef.


        :param type: The type of this SchemaDef.
        :type: str
        """
        if type is None:
            raise ValueError("Invalid value for `type`, must not be `None`")
        allowed_values = ["JSON", "AVRO", "PROTOBUF"]
        if type not in allowed_values:
            raise ValueError(
                "Invalid value for `type` ({0}), must be one of {1}".format(
                    type, allowed_values
                )
            )

        self._type = type
