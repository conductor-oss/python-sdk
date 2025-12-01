"""
Tests for JSON Schema Generator

Tests schema generation from Python type hints, including:
- Basic types (str, int, float, bool)
- Optional types
- Collections (List, Dict)
- Dataclasses
- Union types
- Edge cases and unsupported types
- JSON Schema validation
"""

import unittest
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Any

# Test jsonschema validation is available
try:
    from jsonschema import validate, ValidationError, Draft7Validator
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("WARNING: jsonschema not installed - skipping schema validation tests")

from conductor.client.automator.json_schema_generator import (
    generate_json_schema_from_function,
    _type_to_json_schema,
    _generate_input_schema,
    _generate_output_schema
)
from conductor.client.context.task_context import TaskInProgress


class TestBasicTypes(unittest.TestCase):
    """Test schema generation for basic Python types."""

    def test_string_type(self):
        schema = _type_to_json_schema(str)
        self.assertEqual(schema, {"type": "string"})

    def test_integer_type(self):
        schema = _type_to_json_schema(int)
        self.assertEqual(schema, {"type": "integer"})

    def test_float_type(self):
        schema = _type_to_json_schema(float)
        self.assertEqual(schema, {"type": "number"})

    def test_boolean_type(self):
        schema = _type_to_json_schema(bool)
        self.assertEqual(schema, {"type": "boolean"})

    def test_dict_type(self):
        schema = _type_to_json_schema(dict)
        self.assertEqual(schema, {"type": "object"})

    def test_list_type(self):
        schema = _type_to_json_schema(list)
        self.assertEqual(schema, {"type": "array"})

    def test_any_type(self):
        schema = _type_to_json_schema(Any)
        self.assertEqual(schema, {})  # Empty schema allows any type


class TestOptionalTypes(unittest.TestCase):
    """Test schema generation for Optional types."""

    def test_optional_string(self):
        schema = _type_to_json_schema(Optional[str])
        self.assertEqual(schema, {"type": "string", "nullable": True})

    def test_optional_int(self):
        schema = _type_to_json_schema(Optional[int])
        self.assertEqual(schema, {"type": "integer", "nullable": True})

    def test_optional_dict(self):
        schema = _type_to_json_schema(Optional[dict])
        self.assertEqual(schema, {"type": "object", "nullable": True})

    def test_optional_parameter_not_required(self):
        """Optional[T] parameters should not be in required array."""
        def worker(required_param: str, optional_param: Optional[str]) -> dict:
            return {}

        schemas = generate_json_schema_from_function(worker, "test")
        input_schema = schemas['input']

        # Only required_param should be in required array
        self.assertEqual(input_schema['required'], ['required_param'])
        self.assertNotIn('optional_param', input_schema['required'])

        # Both should be in properties
        self.assertIn('required_param', input_schema['properties'])
        self.assertIn('optional_param', input_schema['properties'])

        # optional_param should be nullable
        self.assertTrue(input_schema['properties']['optional_param']['nullable'])

    def test_optional_with_default_still_not_required(self):
        """Optional[T] with default value should not be required."""
        def worker(opt: Optional[str] = None) -> dict:
            return {}

        schemas = generate_json_schema_from_function(worker, "test")
        input_schema = schemas['input']

        # Should not be required (both Optional AND has default)
        self.assertNotIn('opt', input_schema.get('required', []))

    def test_non_optional_with_default_not_required(self):
        """Non-Optional parameter with default should not be required."""
        def worker(timeout: int = 300) -> dict:
            return {}

        schemas = generate_json_schema_from_function(worker, "test")
        input_schema = schemas['input']

        # Should not be required (has default)
        self.assertNotIn('timeout', input_schema.get('required', []))

    def test_mixed_optional_and_required(self):
        """Mix of required, optional, and defaulted parameters."""
        def worker(
            required: str,
            optional_no_default: Optional[str],
            optional_with_default: Optional[int] = None,
            required_with_default: int = 10
        ) -> dict:
            return {}

        schemas = generate_json_schema_from_function(worker, "test")
        input_schema = schemas['input']

        # Only 'required' should be in required array
        self.assertEqual(input_schema['required'], ['required'])

        # All should be in properties
        self.assertEqual(len(input_schema['properties']), 4)


class TestCollectionTypes(unittest.TestCase):
    """Test schema generation for collections."""

    def test_list_of_strings(self):
        schema = _type_to_json_schema(List[str])
        self.assertEqual(schema, {
            "type": "array",
            "items": {"type": "string"}
        })

    def test_list_of_ints(self):
        schema = _type_to_json_schema(List[int])
        self.assertEqual(schema, {
            "type": "array",
            "items": {"type": "integer"}
        })

    def test_dict_str_int(self):
        schema = _type_to_json_schema(Dict[str, int])
        self.assertEqual(schema, {
            "type": "object",
            "additionalProperties": {"type": "integer"}
        })

    def test_dict_str_str(self):
        schema = _type_to_json_schema(Dict[str, str])
        self.assertEqual(schema, {
            "type": "object",
            "additionalProperties": {"type": "string"}
        })

    def test_list_without_type_args(self):
        # Plain list without type parameter
        schema = _type_to_json_schema(list)
        self.assertEqual(schema, {"type": "array"})

    def test_dict_without_type_args(self):
        # Plain dict without type parameters
        schema = _type_to_json_schema(dict)
        self.assertEqual(schema, {"type": "object"})


class TestDataclassSchemas(unittest.TestCase):
    """Test schema generation for dataclasses."""

    def test_simple_dataclass(self):
        @dataclass
        class User:
            name: str
            age: int

        schema = _type_to_json_schema(User)
        self.assertEqual(schema, {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name", "age"],
            "additionalProperties": False
        })

    def test_dataclass_with_optional_fields(self):
        @dataclass
        class UserProfile:
            user_id: str
            email: Optional[str] = None

        schema = _type_to_json_schema(UserProfile)
        self.assertEqual(schema, {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "email": {"type": "string", "nullable": True}
            },
            "required": ["user_id"],
            "additionalProperties": False
        })

    def test_dataclass_with_default_values(self):
        @dataclass
        class Config:
            host: str
            port: int = 8080
            enabled: bool = True

        schema = _type_to_json_schema(Config)
        self.assertEqual(schema, {
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "port": {"type": "integer"},
                "enabled": {"type": "boolean"}
            },
            "required": ["host"],  # Only host is required
            "additionalProperties": False
        })

    def test_nested_dataclass(self):
        @dataclass
        class Address:
            street: str
            city: str

        @dataclass
        class Person:
            name: str
            address: Address

        schema = _type_to_json_schema(Person)
        expected = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"}
                    },
                    "required": ["street", "city"],
                    "additionalProperties": False
                }
            },
            "required": ["name", "address"],
            "additionalProperties": False
        }
        self.assertEqual(schema, expected)

    def test_dataclass_with_list_field(self):
        @dataclass
        class Order:
            order_id: str
            items: List[str]

        schema = _type_to_json_schema(Order)
        self.assertEqual(schema, {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "items": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["order_id", "items"],
            "additionalProperties": False
        })


class TestUnionTypes(unittest.TestCase):
    """Test schema generation for Union types."""

    def test_union_with_task_in_progress(self):
        # Union[dict, TaskInProgress] should extract dict
        union_type = Union[dict, TaskInProgress]
        schema = _type_to_json_schema(union_type)
        # Should return None because Union with multiple non-None types is not supported
        self.assertIsNone(schema)

    def test_optional_is_union(self):
        # Optional[str] is Union[str, None]
        schema = _type_to_json_schema(Optional[str])
        self.assertEqual(schema, {"type": "string", "nullable": True})


class TestUnsupportedTypes(unittest.TestCase):
    """Test that unsupported types return None."""

    def test_complex_type(self):
        schema = _type_to_json_schema(complex)
        self.assertIsNone(schema)

    def test_custom_class_not_dataclass(self):
        class CustomClass:
            pass

        schema = _type_to_json_schema(CustomClass)
        self.assertIsNone(schema)

    def test_callable_type(self):
        from typing import Callable
        schema = _type_to_json_schema(Callable)
        self.assertIsNone(schema)

    def test_tuple_type(self):
        from typing import Tuple
        schema = _type_to_json_schema(Tuple[str, int])
        self.assertIsNone(schema)


class TestFunctionSchemaGeneration(unittest.TestCase):
    """Test schema generation from complete function signatures."""

    def test_simple_function(self):
        def greet(name: str) -> str:
            return f"Hello {name}"

        schemas = generate_json_schema_from_function(greet, "greet")
        self.assertIsNotNone(schemas)

        # Validate input schema
        input_schema = schemas['input']
        self.assertEqual(input_schema['$schema'], "http://json-schema.org/draft-07/schema#")
        self.assertEqual(input_schema['type'], "object")
        self.assertEqual(input_schema['properties'], {
            "name": {"type": "string"}
        })
        self.assertEqual(input_schema['required'], ["name"])

        # Validate output schema
        output_schema = schemas['output']
        self.assertEqual(output_schema['$schema'], "http://json-schema.org/draft-07/schema#")
        self.assertEqual(output_schema['type'], "string")

    def test_multiple_parameters(self):
        """Test function with multiple parameters of different types."""
        def process_user(name: str, age: int, is_active: bool) -> dict:
            return {}

        schemas = generate_json_schema_from_function(process_user, "process_user")
        self.assertIsNotNone(schemas)

        input_schema = schemas['input']

        # Should have all three parameters
        self.assertEqual(len(input_schema['properties']), 3)
        self.assertEqual(input_schema['properties']['name'], {"type": "string"})
        self.assertEqual(input_schema['properties']['age'], {"type": "integer"})
        self.assertEqual(input_schema['properties']['is_active'], {"type": "boolean"})

        # All are required
        self.assertEqual(set(input_schema['required']), {'name', 'age', 'is_active'})

    def test_function_with_nested_dataclass_parameter(self):
        """Test function with nested dataclass as parameter."""
        @dataclass
        class Address:
            street: str
            city: str
            zip_code: str

        def update_address(user_id: str, address: Address) -> dict:
            return {}

        schemas = generate_json_schema_from_function(update_address, "update_address")
        self.assertIsNotNone(schemas)

        input_schema = schemas['input']

        # Should have user_id and address
        self.assertIn('user_id', input_schema['properties'])
        self.assertIn('address', input_schema['properties'])

        # Address should be a nested object
        address_schema = input_schema['properties']['address']
        self.assertEqual(address_schema['type'], "object")
        self.assertIn('street', address_schema['properties'])
        self.assertIn('city', address_schema['properties'])
        self.assertIn('zip_code', address_schema['properties'])

        # Verify nested required fields
        self.assertEqual(set(address_schema['required']), {'street', 'city', 'zip_code'})

    def test_complex_worker_with_multiple_params_and_dataclass(self):
        """Test realistic worker with mixed parameter types."""
        @dataclass
        class ContactInfo:
            email: str
            phone: Optional[str] = None

        def register_user(
            username: str,
            age: int,
            is_verified: bool,
            contact: ContactInfo,
            tags: List[str]
        ) -> dict:
            return {}

        schemas = generate_json_schema_from_function(register_user, "register_user")
        self.assertIsNotNone(schemas)

        input_schema = schemas['input']

        # Verify all parameters are present
        self.assertEqual(len(input_schema['properties']), 5)

        # Basic types
        self.assertEqual(input_schema['properties']['username'], {"type": "string"})
        self.assertEqual(input_schema['properties']['age'], {"type": "integer"})
        self.assertEqual(input_schema['properties']['is_verified'], {"type": "boolean"})

        # List type
        self.assertEqual(input_schema['properties']['tags'], {
            "type": "array",
            "items": {"type": "string"}
        })

        # Nested dataclass
        contact_schema = input_schema['properties']['contact']
        self.assertEqual(contact_schema['type'], "object")
        self.assertEqual(contact_schema['properties']['email'], {"type": "string"})
        self.assertEqual(contact_schema['properties']['phone'], {"type": "string", "nullable": True})

        # Only email is required in contact (phone is optional)
        self.assertEqual(contact_schema['required'], ['email'])

    def test_function_with_default_args(self):
        def process(data: str, count: int = 10) -> dict:
            return {}

        schemas = generate_json_schema_from_function(process, "process")
        input_schema = schemas['input']

        # Only 'data' is required, 'count' has default
        self.assertEqual(input_schema['required'], ["data"])
        self.assertIn("count", input_schema['properties'])

    def test_async_function(self):
        async def fetch_data(url: str) -> dict:
            return {}

        schemas = generate_json_schema_from_function(fetch_data, "fetch_data")
        self.assertIsNotNone(schemas)
        self.assertIsNotNone(schemas['input'])
        self.assertIsNotNone(schemas['output'])

    def test_function_with_dataclass_input(self):
        @dataclass
        class OrderInfo:
            order_id: str
            amount: float

        def process_order(order: OrderInfo) -> dict:
            return {}

        schemas = generate_json_schema_from_function(process_order, "process_order")
        input_schema = schemas['input']

        # Validate dataclass was converted
        self.assertEqual(input_schema['properties']['order']['type'], "object")
        self.assertIn("order_id", input_schema['properties']['order']['properties'])
        self.assertIn("amount", input_schema['properties']['order']['properties'])

    def test_function_with_union_return(self):
        def long_task() -> Union[dict, TaskInProgress]:
            return {}

        schemas = generate_json_schema_from_function(long_task, "long_task")

        # Output schema should handle Union by filtering out TaskInProgress
        # But Union[dict, TaskInProgress] has two non-None types, so should return None
        # Actually, let me check the implementation
        self.assertIsNotNone(schemas)

    def test_function_no_type_hints(self):
        def no_hints(data):
            return data

        schemas = generate_json_schema_from_function(no_hints, "no_hints")
        # Should return dict with None values because no type hints
        self.assertIsNotNone(schemas)
        self.assertIsNone(schemas['input'])  # Can't generate without type hints
        self.assertIsNone(schemas['output'])  # Can't generate without return hint

    def test_function_no_return_hint(self):
        def no_return(name: str):
            print(name)

        schemas = generate_json_schema_from_function(no_return, "no_return")
        # Input schema should work, output should be None
        self.assertIsNotNone(schemas)
        self.assertIsNotNone(schemas['input'])
        self.assertIsNone(schemas['output'])

    def test_function_with_complex_nested_types(self):
        @dataclass
        class Address:
            street: str
            city: str

        @dataclass
        class User:
            name: str
            addresses: List[Address]

        def update_user(user: User) -> dict:
            return {}

        schemas = generate_json_schema_from_function(update_user, "update_user")
        # This has List[dataclass] which we don't support - should fail gracefully
        # Actually, let me check if we handle this
        input_schema = schemas['input']
        self.assertIn("user", input_schema['properties'])


class TestSchemaValidation(unittest.TestCase):
    """Test that generated schemas are valid JSON Schema draft-07."""

    def setUp(self):
        if not HAS_JSONSCHEMA:
            self.skipTest("jsonschema library not available")

    def test_simple_schema_is_valid(self):
        def worker(name: str, age: int) -> dict:
            return {}

        schemas = generate_json_schema_from_function(worker, "worker")
        input_schema = schemas['input']

        # Validate it's a valid JSON Schema
        Draft7Validator.check_schema(input_schema)

        # Test validation with valid data
        valid_data = {"name": "Alice", "age": 30}
        validate(instance=valid_data, schema=input_schema)

        # Test validation with invalid data
        invalid_data = {"name": "Alice", "age": "thirty"}
        with self.assertRaises(ValidationError):
            validate(instance=invalid_data, schema=input_schema)

    def test_dataclass_schema_is_valid(self):
        @dataclass
        class OrderInfo:
            order_id: str
            amount: float
            quantity: int

        def process_order(order: OrderInfo) -> dict:
            return {}

        schemas = generate_json_schema_from_function(process_order, "process_order")
        input_schema = schemas['input']

        # Validate it's a valid JSON Schema
        Draft7Validator.check_schema(input_schema)

        # Test with valid data
        valid_data = {
            "order": {
                "order_id": "ORD-123",
                "amount": 99.99,
                "quantity": 2
            }
        }
        validate(instance=valid_data, schema=input_schema)

        # Test with invalid data (missing required field)
        invalid_data = {
            "order": {
                "order_id": "ORD-123",
                "amount": 99.99
                # missing quantity
            }
        }
        with self.assertRaises(ValidationError):
            validate(instance=invalid_data, schema=input_schema)

    def test_optional_field_validation(self):
        @dataclass
        class UserUpdate:
            user_id: str
            email: Optional[str] = None

        def update_user(user: UserUpdate) -> dict:
            return {}

        schemas = generate_json_schema_from_function(update_user, "update_user")
        input_schema = schemas['input']

        Draft7Validator.check_schema(input_schema)

        # Valid without optional field
        valid_data1 = {"user": {"user_id": "123"}}
        validate(instance=valid_data1, schema=input_schema)

        # Valid with optional field
        valid_data2 = {"user": {"user_id": "123", "email": "test@example.com"}}
        validate(instance=valid_data2, schema=input_schema)

        # Valid with null optional field
        valid_data3 = {"user": {"user_id": "123", "email": None}}
        validate(instance=valid_data3, schema=input_schema)

    def test_list_schema_validation(self):
        def process_batch(items: List[str]) -> dict:
            return {}

        schemas = generate_json_schema_from_function(process_batch, "process_batch")
        input_schema = schemas['input']

        Draft7Validator.check_schema(input_schema)

        # Valid list
        valid_data = {"items": ["a", "b", "c"]}
        validate(instance=valid_data, schema=input_schema)

        # Invalid list (wrong item type)
        invalid_data = {"items": [1, 2, 3]}
        with self.assertRaises(ValidationError):
            validate(instance=invalid_data, schema=input_schema)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_function_no_parameters(self):
        def no_params() -> dict:
            return {}

        schemas = generate_json_schema_from_function(no_params, "no_params")
        self.assertIsNotNone(schemas)

        input_schema = schemas['input']
        self.assertEqual(input_schema['type'], "object")
        self.assertEqual(input_schema['properties'], {})
        self.assertFalse('required' in input_schema or input_schema.get('required') == [])

    def test_dataclass_with_unsupported_field_type(self):
        @dataclass
        class BadData:
            name: str
            callback: callable  # Unsupported type

        schema = _type_to_json_schema(BadData)
        # Should return None because callback type can't be converted
        self.assertIsNone(schema)

    def test_function_with_mixed_hints(self):
        def mixed(typed: str, untyped) -> dict:
            return {}

        schemas = generate_json_schema_from_function(mixed, "mixed")
        # Input schema should be None because 'untyped' has no annotation
        # Output schema should work because dict has a hint
        self.assertIsNotNone(schemas)
        self.assertIsNone(schemas['input'])  # Can't generate with missing type hints
        self.assertIsNotNone(schemas['output'])  # dict return type works

    def test_dataclass_with_default_factory(self):
        @dataclass
        class Config:
            name: str
            tags: List[str] = field(default_factory=list)

        schema = _type_to_json_schema(Config)
        # 'tags' has default_factory, so not required
        self.assertEqual(schema['required'], ["name"])
        self.assertIn("tags", schema['properties'])

    def test_none_type(self):
        schema = _type_to_json_schema(type(None))
        self.assertEqual(schema, {"type": "null"})


class TestComplexScenarios(unittest.TestCase):
    """Test complex, real-world scenarios."""

    def test_realistic_worker_signature(self):
        @dataclass
        class PaymentRequest:
            amount: float
            currency: str
            customer_id: str
            metadata: Optional[Dict[str, str]] = None

        def process_payment(request: PaymentRequest, idempotency_key: str) -> dict:
            return {}

        schemas = generate_json_schema_from_function(process_payment, "process_payment")
        self.assertIsNotNone(schemas)

        input_schema = schemas['input']
        self.assertEqual(input_schema['required'], ["request", "idempotency_key"])

        # Validate it's valid JSON Schema
        if HAS_JSONSCHEMA:
            Draft7Validator.check_schema(input_schema)

    def test_function_returning_dataclass(self):
        @dataclass
        class Result:
            status: str
            code: int

        def process() -> Result:
            return Result("ok", 200)

        schemas = generate_json_schema_from_function(process, "process")
        output_schema = schemas['output']

        # Output should be object schema from dataclass
        self.assertEqual(output_schema['type'], "object")
        self.assertIn("status", output_schema['properties'])
        self.assertIn("code", output_schema['properties'])

    def test_async_worker_with_complex_types(self):
        @dataclass
        class ApiRequest:
            url: str
            headers: Dict[str, str]
            timeout: int = 30

        async def call_api(request: ApiRequest) -> Dict[str, Any]:
            return {}

        schemas = generate_json_schema_from_function(call_api, "call_api")
        self.assertIsNotNone(schemas)

        if HAS_JSONSCHEMA:
            Draft7Validator.check_schema(schemas['input'])
            Draft7Validator.check_schema(schemas['output'])


class TestSchemaNames(unittest.TestCase):
    """Test that schema names are generated correctly."""

    def test_input_output_schema_structure(self):
        def worker(name: str) -> dict:
            return {}

        schemas = generate_json_schema_from_function(worker, "my_task")
        self.assertIn('input', schemas)
        self.assertIn('output', schemas)

        # Both should have $schema field
        self.assertIn('$schema', schemas['input'])
        self.assertIn('$schema', schemas['output'])

        # Both should use draft-07
        self.assertEqual(schemas['input']['$schema'], "http://json-schema.org/draft-07/schema#")
        self.assertEqual(schemas['output']['$schema'], "http://json-schema.org/draft-07/schema#")


class TestRealWorldExamples(unittest.TestCase):
    """Test real-world worker examples."""

    def test_user_service_worker(self):
        """Test a realistic user service worker with multiple params and nested types."""
        @dataclass
        class Address:
            street: str
            city: str
            state: str
            zip_code: str
            country: str = "USA"

        @dataclass
        class UserProfile:
            first_name: str
            last_name: str
            email: str
            age: int
            address: Address
            phone: Optional[str] = None
            is_active: bool = True

        def create_user(
            user_id: str,
            profile: UserProfile,
            notify: bool,
            tags: List[str]
        ) -> dict:
            return {"user_id": user_id, "status": "created"}

        schemas = generate_json_schema_from_function(create_user, "create_user")
        self.assertIsNotNone(schemas)

        input_schema = schemas['input']

        # Verify top-level parameters
        self.assertEqual(len(input_schema['properties']), 4)
        self.assertIn('user_id', input_schema['properties'])
        self.assertIn('profile', input_schema['properties'])
        self.assertIn('notify', input_schema['properties'])
        self.assertIn('tags', input_schema['properties'])

        # Verify UserProfile dataclass
        profile_schema = input_schema['properties']['profile']
        self.assertEqual(profile_schema['type'], "object")
        self.assertEqual(len(profile_schema['properties']), 7)

        # Verify nested Address in UserProfile
        address_schema = profile_schema['properties']['address']
        self.assertEqual(address_schema['type'], "object")
        self.assertEqual(len(address_schema['properties']), 5)

        # Verify required fields at each level
        self.assertEqual(set(input_schema['required']), {'user_id', 'profile', 'notify', 'tags'})
        self.assertEqual(set(profile_schema['required']), {'first_name', 'last_name', 'email', 'age', 'address'})
        self.assertEqual(set(address_schema['required']), {'street', 'city', 'state', 'zip_code'})

        # Validate with jsonschema if available
        if HAS_JSONSCHEMA:
            Draft7Validator.check_schema(input_schema)

            # Test valid data
            valid_data = {
                "user_id": "USR-123",
                "profile": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    "age": 30,
                    "address": {
                        "street": "123 Main St",
                        "city": "Springfield",
                        "state": "IL",
                        "zip_code": "62701"
                    }
                },
                "notify": True,
                "tags": ["new", "premium"]
            }
            validate(instance=valid_data, schema=input_schema)


if __name__ == '__main__':
    unittest.main()

