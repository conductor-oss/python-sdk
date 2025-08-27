import logging
import unittest
from conductor.client.configuration.configuration import Configuration
from conductor.client.adapters.models import SchemaDef, SchemaType
from conductor.client.orkes.orkes_schema_client import OrkesSchemaClient

SCHEMA_NAME = 'ut_schema'
SCHEMA_VERSION = 1

schema = {
  "name": "schema-test",
  "type": "JSON",
  "data": {
    "type": "object",
    "properties": {
      "$schema": "http://json-schema.org/draft-07/schema"
    }
  }
}
class TestOrkesSchemaClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        configuration = Configuration()
        cls.schema_client = OrkesSchemaClient(configuration)

    def setUp(self):
        self.schemaDef = SchemaDef(name=SCHEMA_NAME, version=SCHEMA_VERSION, type=SchemaType.JSON, data=schema, external_ref='http://example.com')
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_init(self):
        message = "schemaApi is not of type SchemaApi"
        self.assertIsInstance(self.schema_client.schemaApi, SchemaResourceApi, message)

    def test_registerSchema(self):
        self.schema_client.register_schema(self.schemaDef)
        response = self.schema_client.schemaApi.get_schema_by_name_and_version(name=SCHEMA_NAME, version=SCHEMA_VERSION)
        self.assertEqual(response.name, SCHEMA_NAME)
        self.assertEqual(response.version, SCHEMA_VERSION)
        self.assertEqual(response.type, SchemaType.JSON)

    def test_getSchema(self):
        self.schema_client.register_schema(self.schemaDef)
        schema = self.schema_client.get_schema(SCHEMA_NAME, SCHEMA_VERSION)
        self.assertEqual(schema.name, SCHEMA_NAME)
        self.assertEqual(schema.version, SCHEMA_VERSION)

    def test_getAllSchemas(self):
        schemaDef2 = SchemaDef(name='ut_schema_2', version=1, type=SchemaType.JSON, data=schema, external_ref='http://example.com/2')
        self.schema_client.register_schema(self.schemaDef)
        self.schema_client.register_schema(schemaDef2)
        schemas = self.schema_client.get_all_schemas()
        self.assertGreaterEqual(len(schemas), 2)

    def test_deleteSchema(self):
        self.schema_client.register_schema(self.schemaDef)
        self.schema_client.delete_schema(SCHEMA_NAME, SCHEMA_VERSION)
        with self.assertRaises(Exception):
            self.schema_client.get_schema(SCHEMA_NAME, SCHEMA_VERSION)

    def test_deleteSchemaByName(self):
        self.schema_client.register_schema(self.schemaDef)
        self.schema_client.delete_schema_by_name(SCHEMA_NAME)
        with self.assertRaises(Exception):
            self.schema_client.get_schema(SCHEMA_NAME, SCHEMA_VERSION)


if __name__ == '__main__':
    unittest.main()
