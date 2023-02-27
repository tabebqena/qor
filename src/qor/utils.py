import importlib
import importlib.util
import json
import logging
from importlib.machinery import ModuleSpec
from typing import Tuple, cast

from qor.constants import METHOD_CODES


def import_module_by_path(path: str, module_name: str):
    spec: ModuleSpec = cast(
        ModuleSpec, importlib.util.spec_from_file_location(module_name, path)
    )
    module = importlib.util.module_from_spec(spec)
    return spec, module


def import_object_by_path(path: str, module_name: str, object_name: str):
    spec, module = import_module_by_path(path, module_name)

    spec.loader.exec_module(module)
    return module.__getattribute__(object_name)


def int_to_method_name(id: int):
    return METHOD_CODES[id]


def to_bytes(value):
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return str.encode(value)
    if isinstance(value, (dict, list, tuple)):
        return str.encode(json.dumps(value))
    return value


def to_string(value):
    if isinstance(value, bytes):
        return bytes.decode(value)
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value)
    return value


def parse_return_value(value) -> Tuple[int, bytes]:
    status = None
    value_bytes = value
    exception = None

    if isinstance(value, tuple) and len(value) == 2:
            try:
                status = int(value[0])
                value_bytes = to_bytes(value[1])
            except Exception as e:
                logging.error(e)
                exception = e
    else:
        try:
            status = 200
            value_bytes = to_bytes(value)
        except Exception as e:
            logging.error(e)
            exception = e
    if exception is None:
        return status, value_bytes
    raise Exception("can't parse value. ") from (exception)
