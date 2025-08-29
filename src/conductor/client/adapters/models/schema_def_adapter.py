from enum import Enum

from conductor.client.codegen.models.schema_def import SchemaDef


class SchemaType(str, Enum):
    JSON = ("JSON",)
    AVRO = ("AVRO",)
    PROTOBUF = "PROTOBUF"

    def __str__(self) -> str:
        return self.name.__str__()


class SchemaDefAdapter(SchemaDef):
    def __init__(self, create_time=None, created_by=None, data=None, external_ref=None, name=None, owner_app=None, type=None, update_time=None, updated_by=None, version=1):  # noqa: E501
        """SchemaDef - a model defined in Swagger"""  # noqa: E501
        self._create_time = None
        self._created_by = None
        self._data = None
        self._external_ref = None
        self._name = None
        self._owner_app = None
        self._type = None
        self._update_time = None
        self._updated_by = None
        self._version = None
        self.discriminator = None
        if create_time is not None:
            self.create_time = create_time
        if created_by is not None:
            self.created_by = created_by
        if data is not None:
            self.data = data
        if external_ref is not None:
            self.external_ref = external_ref
        self.name = name
        if owner_app is not None:
            self.owner_app = owner_app
        self.type = type
        if update_time is not None:
            self.update_time = update_time
        if updated_by is not None:
            self.updated_by = updated_by
        if version is not None:
            self.version = version

    @SchemaDef.type.setter
    def type(self, type):
        """Sets the type of this SchemaDef.


        :param type: The type of this SchemaDef.
        :type: str
        """
        self._type = type

    @SchemaDef.name.setter
    def name(self, name):
        """Sets the name of this SchemaDef.


        :param name: The name of this SchemaDef.  # noqa: E501
        :type: str
        """
        self._name = name

    @SchemaDef.version.setter
    def version(self, version):
        """Sets the data of this SchemaDef.


        :param data: The data of this SchemaDef.  # noqa: E501
        :type: dict(str, object)
        """
        self._version = version
