"""
JSON Schema Generator from Python Type Hints

Generates JSON Schema (draft-07) from Python function signatures and type hints.
Used for automatic task definition registration with input/output schemas.
"""

import inspect
import logging
from dataclasses import fields, is_dataclass
from typing import get_origin, get_args, Any, Optional, Dict, List, Union
import typing

logger = logging.getLogger(__name__)


def _is_optional_type(type_hint) -> bool:
    """
    Check if a type hint is Optional[T] (which is Union[T, None]).

    Returns True if the type is Optional, False otherwise.
    """
    origin = get_origin(type_hint)
    if origin is Union:
        args = get_args(type_hint)
        # Optional[T] is Union[T, None], so check if None is in the args
        return type(None) in args
    return False


def generate_json_schema_from_function(func, schema_name: str) -> Optional[Dict[str, Any]]:
    """
    Generate JSON Schema draft-07 from function signature.

    Args:
        func: The function to analyze (can be sync or async)
        schema_name: Name for the schema

    Returns:
        Dict containing JSON Schema, or None if schema cannot be generated

    Example:
        >>> def my_worker(user_id: str, age: int) -> dict:
        ...     pass
        >>> schema = generate_json_schema_from_function(my_worker, "my_worker_input")
        >>> # Returns: {"$schema": "http://json-schema.org/draft-07/schema#", ...}
    """
    try:
        sig = inspect.signature(func)
        return_annotation = sig.return_annotation

        # Generate input schema from parameters
        input_schema = _generate_input_schema(sig, schema_name)

        # Generate output schema from return type
        output_schema = _generate_output_schema(return_annotation, schema_name)

        return {
            'input': input_schema,
            'output': output_schema
        }
    except Exception as e:
        logger.debug(f"Could not generate JSON schema for {func.__name__}: {e}")
        return None


def _generate_input_schema(sig: inspect.Signature, schema_name: str) -> Optional[Dict[str, Any]]:
    """Generate JSON schema for function input parameters."""
    try:
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param.annotation == inspect.Parameter.empty:
                # No type hint - can't generate schema
                return None

            param_schema = _type_to_json_schema(param.annotation)
            if param_schema is None:
                # Can't convert this type - abort schema generation
                return None

            properties[param_name] = param_schema

            # Parameter is required if:
            # 1. No default value AND
            # 2. Not Optional[T] type
            has_default = param.default != inspect.Parameter.empty
            is_optional = _is_optional_type(param.annotation)

            if not has_default and not is_optional:
                required.append(param_name)

        if not properties:
            # No parameters - empty schema
            return {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }

        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": properties,
            "additionalProperties": False
        }

        if required:
            schema["required"] = required

        return schema

    except Exception as e:
        logger.debug(f"Could not generate input schema: {e}")
        return None


def _generate_output_schema(return_annotation, schema_name: str) -> Optional[Dict[str, Any]]:
    """Generate JSON schema for function return type."""
    try:
        if return_annotation == inspect.Signature.empty:
            # No return type hint
            return None

        # Handle Union types (like Union[dict, TaskInProgress])
        # For task return types, we want the dict part
        origin = get_origin(return_annotation)
        if origin is Union:
            args = get_args(return_annotation)
            # Filter out TaskInProgress and None
            dict_types = [arg for arg in args if arg not in (type(None),)]
            # Try to find dict type
            for arg in dict_types:
                if arg == dict or get_origin(arg) == dict:
                    return_annotation = arg
                    break
                # Also check for dataclasses
                if is_dataclass(arg):
                    return_annotation = arg
                    break

        output_schema = _type_to_json_schema(return_annotation)
        if output_schema is None:
            return None

        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            **output_schema
        }

    except Exception as e:
        logger.debug(f"Could not generate output schema: {e}")
        return None


def _type_to_json_schema(type_hint) -> Optional[Dict[str, Any]]:
    """
    Convert Python type hint to JSON Schema.

    Supports:
    - Basic types: str, int, float, bool
    - Optional[T]
    - List[T], Dict[str, T]
    - Dataclasses
    - dict (generic)
    """
    # Handle None type
    if type_hint is type(None):
        return {"type": "null"}

    # Get origin for generic types (List, Dict, Optional, etc.)
    origin = get_origin(type_hint)

    # Handle Optional[T] (which is Union[T, None])
    if origin is Union:
        args = get_args(type_hint)
        # Filter out NoneType
        non_none_args = [arg for arg in args if arg is not type(None)]

        if len(non_none_args) == 1:
            # Optional[T] case
            inner_schema = _type_to_json_schema(non_none_args[0])
            if inner_schema:
                # For optional, we could use oneOf or just mark as nullable
                # Using nullable for simplicity
                inner_schema['nullable'] = True
                return inner_schema
        # Multiple non-None types in Union - too complex
        return None

    # Handle List[T]
    if origin is list:
        args = get_args(type_hint)
        if args:
            item_schema = _type_to_json_schema(args[0])
            if item_schema:
                return {
                    "type": "array",
                    "items": item_schema
                }
        # List without type argument
        return {"type": "array"}

    # Handle Dict[K, V]
    if origin is dict:
        args = get_args(type_hint)
        if len(args) >= 2:
            # Dict[str, T] - we can only support string keys in JSON
            if args[0] == str:
                value_schema = _type_to_json_schema(args[1])
                if value_schema:
                    return {
                        "type": "object",
                        "additionalProperties": value_schema
                    }
        # Generic dict
        return {"type": "object"}

    # Handle basic types
    if type_hint == str:
        return {"type": "string"}
    if type_hint == int:
        return {"type": "integer"}
    if type_hint == float:
        return {"type": "number"}
    if type_hint == bool:
        return {"type": "boolean"}
    if type_hint == dict:
        return {"type": "object"}
    if type_hint == list:
        return {"type": "array"}

    # Handle dataclasses
    if is_dataclass(type_hint):
        try:
            properties = {}
            required = []

            for field in fields(type_hint):
                field_schema = _type_to_json_schema(field.type)
                if field_schema is None:
                    # Can't convert a field - abort dataclass schema
                    return None

                properties[field.name] = field_schema

                # Check if field has default value
                # Field is required if it has no default AND no default_factory
                from dataclasses import MISSING
                has_default = field.default is not MISSING
                has_default_factory = field.default_factory is not MISSING

                if not has_default and not has_default_factory:
                    # No default - required field
                    required.append(field.name)

            schema = {
                "type": "object",
                "properties": properties,
                "additionalProperties": False
            }

            if required:
                schema["required"] = required

            return schema

        except Exception as e:
            logger.debug(f"Could not convert dataclass {type_hint}: {e}")
            return None

    # Handle Any type
    if type_hint == Any:
        return {}  # Empty schema means any type allowed

    # Unknown type
    return None
