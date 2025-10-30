"""
Utility functions for converting between generated models and adapters.
"""

from typing import Any, Dict, List, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def convert_list_to_adapter(items: List[Any], adapter_class: Type[T]) -> List[T]:
    """
    Convert a list of generated models to a list of adapters.

    Args:
        items: List of generated model instances
        adapter_class: The adapter class to convert to

    Returns:
        List of adapter instances
    """
    return [adapter_class.model_validate(item.model_dump()) for item in items]


def convert_to_adapter(item: Any, adapter_class: Type[T]) -> T:
    """
    Convert a single generated model to an adapter.

    Args:
        item: Generated model instance
        adapter_class: The adapter class to convert to

    Returns:
        Adapter instance
    """
    return adapter_class.model_validate(item.model_dump())


def convert_dict_to_adapter(
    input_dict: Dict[str, List[Any]], adapter_class: Type[T]
) -> Dict[str, List[T]]:
    """
    Convert a dictionary of model lists to a dictionary of adapter lists.

    Args:
        input_dict: Dictionary mapping string keys to lists of model instances
        adapter_class: The adapter class to convert to

    Returns:
        Dictionary mapping string keys to lists of adapter instances
    """
    return {key: convert_list_to_adapter(items, adapter_class) for key, items in input_dict.items()}
