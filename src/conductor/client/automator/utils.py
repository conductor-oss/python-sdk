from __future__ import annotations
import dataclasses
import datetime
import inspect
import logging
import typing
from typing import List

from dacite import from_dict, Config
from dacite.exceptions import MissingValueError, WrongTypeError
from requests.structures import CaseInsensitiveDict

from conductor.client.configuration.configuration import Configuration

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(
        __name__
    )
)

simple_types = {
    int, float, str, bool, datetime.date, datetime.datetime, object
}
dict_types = {
    dict, typing.Dict, CaseInsensitiveDict
}
collection_types = {
    list, List, typing.Set
}


def convert_from_dict_or_list(cls: type, data: typing.Union[dict, list]) -> object:
    is_list = type(data) in collection_types
    if is_list:
        val_list = []
        for val in data:
            generic_types = typing.get_args(cls)[0]
            converted = convert_from_dict(generic_types, val)
            val_list.append(converted)
        return val_list
    return convert_from_dict(cls, data)


def convert_from_dict(cls: type, data: dict) -> object:
    if data is None:
        return data

    if isinstance(data, cls):
        return data

    if dataclasses.is_dataclass(cls):
        try:
            # First try with strict conversion
            return from_dict(data_class=cls, data=data)
        except MissingValueError as e:
            # Lenient mode: Create partial object with only available fields
            # Use manual construction to bypass dacite's strict validation
            missing_field = str(e).replace('missing value for field ', '').strip('"')

            logger.debug(
                f"Missing fields in task input for {cls.__name__}. "
                f"Creating partial object with available fields only. "
                f"Available: {list(data.keys()) if isinstance(data, dict) else []}, "
                f"Missing: {missing_field}"
            )

            # Build kwargs with available fields only, set missing to None
            kwargs = {}
            type_hints = typing.get_type_hints(cls)

            for field in dataclasses.fields(cls):
                if field.name in data:
                    # Field is present - convert it properly
                    field_type = type_hints.get(field.name, field.type)
                    value = data[field.name]

                    # Handle nested dataclasses
                    if dataclasses.is_dataclass(field_type) and isinstance(value, dict):
                        try:
                            kwargs[field.name] = convert_from_dict(field_type, value)
                        except Exception:
                            # If nested conversion fails, use None
                            kwargs[field.name] = None
                    else:
                        kwargs[field.name] = value
                else:
                    # Field is missing - set to None regardless of type
                    kwargs[field.name] = None

            # Construct object directly, bypassing dacite
            try:
                return cls(**kwargs)
            except TypeError as te:
                # Some fields may not accept None - try with empty defaults
                logger.warning(f"Failed to create {cls.__name__} with None values, trying empty defaults: {te}")

                for field in dataclasses.fields(cls):
                    if field.name not in data and kwargs.get(field.name) is None:
                        field_type = type_hints.get(field.name, field.type)

                        # Provide type-appropriate empty defaults
                        if field_type == str or field_type == 'str':
                            kwargs[field.name] = ''
                        elif field_type in (int, float):
                            kwargs[field.name] = 0
                        elif field_type == bool:
                            kwargs[field.name] = False
                        elif field_type == list or typing.get_origin(field_type) == list:
                            kwargs[field.name] = []
                        elif field_type == dict or typing.get_origin(field_type) == dict:
                            kwargs[field.name] = {}
                        # else: keep None

                try:
                    return cls(**kwargs)
                except Exception as final_e:
                    # Last resort: log error but don't crash
                    logger.error(
                        f"Cannot create {cls.__name__} even with defaults. "
                        f"Available fields: {list(data.keys()) if isinstance(data, dict) else []}. "
                        f"Error: {final_e}. Returning None."
                    )
                    return None

    typ = type(data)
    if not ((str(typ).startswith("dict[") or
             str(typ).startswith("typing.Dict[") or
             str(typ).startswith("requests.structures.CaseInsensitiveDict[") or
             typ is dict or str(typ).startswith("OrderedDict["))):
        data = {}

    members = inspect.signature(cls.__init__).parameters
    kwargs = {}

    for member in members:
        if "self" == member:
            continue
        typ = members[member].annotation
        generic_types = typing.get_args(members[member].annotation)

        if typ in simple_types:
            if member in data:
                kwargs[member] = data[member]
            else:
                kwargs[member] = members[member].default
        elif str(typ).startswith("typing.List[") or str(typ).startswith("typing.Set[") or str(typ).startswith("list["):
            values = []

            generic_type = object
            if len(generic_types) > 0:
                generic_type = generic_types[0]
            values = [get_value(generic_type, item) for item in data[member]]
            kwargs[member] = values
        elif (str(typ).startswith("dict[") or
              str(typ).startswith("typing.Dict[") or
              str(typ).startswith("requests.structures.CaseInsensitiveDict[") or
              typ is dict or str(typ).startswith("OrderedDict[")):

            values = {}
            generic_type = object
            if len(generic_types) > 1:
                generic_type = generic_types[1]
            for k in data[member]:
                v = data[member][k]
                values[k] = get_value(generic_type, v)
            kwargs[member] = values
        elif typ is inspect.Parameter.empty:
            if inspect.Parameter.VAR_KEYWORD == members[member].kind:
                if type(data) in dict_types:
                    kwargs.update(data)
                else:
                    kwargs.update(data[member])
            else:
                # kwargs[member] = data[member]
                kwargs.update(data)
        else:
            kwargs[member] = convert_from_dict(typ, data[member])

    return cls(**kwargs)


def get_value(typ: type, val: object) -> object:
    if typ in simple_types:
        return val
    elif str(typ).startswith("typing.List[") or str(typ).startswith("typing.Set[") or str(typ).startswith("list["):
        values = [get_value(type(item), item) for item in val]
        return values
    elif str(typ).startswith("dict[") or str(typ).startswith(
            "typing.Dict[") or str(typ).startswith("requests.structures.CaseInsensitiveDict[") or typ is dict:
        values = {}
        for k in val:
            v = val[k]
            values[k] = get_value(object, v)
        return values
    else:
        return convert_from_dict(typ, val)
