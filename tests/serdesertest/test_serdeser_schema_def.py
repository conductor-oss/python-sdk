import unittest
import json
from conductor.client.http.models.schema_def import SchemaDef, SchemaType
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


class TestSchemaDefSerDes(unittest.TestCase):
    def setUp(self):
        # Load JSON template
        self.server_json_str = JsonTemplateResolver.get_json_string("SchemaDef")
        self.server_json = json.loads(self.server_json_str)

    def test_schema_def_serdes(self):
        # 1. Create a SchemaDef instance with all fields from the JSON
        schema_def = SchemaDef(
            name=self.server_json.get("name"),
            version=self.server_json.get("version"),
            type=SchemaType(self.server_json.get("type")) if self.server_json.get("type") else None,
            data=self.server_json.get("data"),
            external_ref=self.server_json.get("externalRef")
        )

        # Set the auditable fields
        schema_def.owner_app = self.server_json.get("ownerApp")
        schema_def.create_time = self.server_json.get("createTime")
        schema_def.update_time = self.server_json.get("updateTime")
        schema_def.created_by = self.server_json.get("createdBy")
        schema_def.updated_by = self.server_json.get("updatedBy")

        # 2. Verify all fields are properly populated
        self.assertEqual(self.server_json.get("name"), schema_def.name)
        self.assertEqual(self.server_json.get("version"), schema_def.version)
        if self.server_json.get("type"):
            self.assertEqual(SchemaType(self.server_json.get("type")), schema_def.type)
        self.assertEqual(self.server_json.get("data"), schema_def.data)
        self.assertEqual(self.server_json.get("externalRef"), schema_def.external_ref)
        self.assertEqual(self.server_json.get("ownerApp"), schema_def.owner_app)
        self.assertEqual(self.server_json.get("createTime"), schema_def.create_time)
        self.assertEqual(self.server_json.get("updateTime"), schema_def.update_time)
        self.assertEqual(self.server_json.get("createdBy"), schema_def.created_by)
        self.assertEqual(self.server_json.get("updatedBy"), schema_def.updated_by)

        # 3. Test serialization from SDK model back to JSON
        model_dict = schema_def.to_dict()

        # Create the expected JSON with proper field mappings
        model_json = {}

        # Map the fields using the attribute_map
        for attr, json_key in {**SchemaDef.attribute_map}.items():
            value = model_dict.get(attr)
            if value is not None:
                if attr == "type" and value is not None:
                    model_json[json_key] = str(value)
                else:
                    model_json[json_key] = value

        # 4. Verify the resulting JSON matches the original
        for key, value in self.server_json.items():
            if key == "type" and value is not None and model_json.get(key) is not None:
                # Handle enum conversion
                self.assertEqual(value, model_json.get(key))
            else:
                self.assertEqual(value, model_json.get(key), f"Field {key} doesn't match")


if __name__ == '__main__':
    unittest.main()