import importlib
import importlib.util
import json
import logging
import os
import pkgutil
import sys
from importlib.machinery import ModuleSpec
from typing import Any, Tuple, cast

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


def import_object_from_module(import_name):
    mod, oname = (
        ".".join(import_name.split(".")[:-1]),
        import_name.split(".")[-1],
    )
    try:
        module = importlib.import_module(mod)
    except ImportError as e:
        raise
    return getattr(module, oname)


def int_to_method_name(id: int):
    return METHOD_CODES[id]


def to_bytes(value):
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return str.encode(value)
    elif isinstance(value, (int, float)):
        return str.encode(str(value))
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


class cached_property(object):
    """
    Descriptor (non-data) for building an attribute on-demand on first use.
    """

    def __init__(self, factory):
        """
        <factory> is called such: factory(instance) to build the attribute.
        """
        self._attr_name = factory.__name__
        self._factory = factory

    def __get__(self, instance, owner):
        # Build the attribute.
        attr = self._factory(instance)

        # Cache the value; hide ourselves.
        setattr(instance, self._attr_name, attr)

        return attr


def parse_return_value(value) -> Tuple[int, bytes, Any]:
    status = None
    value_bytes = value
    original = None
    exception = None

    if isinstance(value, tuple) and len(value) == 2:
        try:
            status = int(value[0])
            value_bytes = to_bytes(value[1])
            original = type(value[1])
        except Exception as e:
            logging.error(e)
            exception = e
    else:
        try:
            status = 200
            value_bytes = to_bytes(value)
            original = type(value)
        except Exception as e:
            logging.error(e)
            exception = e
    if exception is None:
        return status, value_bytes, original
    raise Exception("can't parse value. ") from (exception)


def get_path(import_name) -> str:
    """Find the root path of a package, or the path that contains a
    module. If it cannot be found, returns the current working
    directory.

    Not to be confused with the value returned by :func:`find_package`.

    Copied from `flask.helpers`
    """
    # Module already imported and has a file attribute. Use that first.
    mod = sys.modules.get(import_name)

    if (
        mod is not None
        and hasattr(mod, "__file__")
        and mod.__file__ is not None
    ):
        return os.path.dirname(os.path.abspath(mod.__file__))

    # Next attempt: check the loader.
    loader = pkgutil.get_loader(import_name)

    # Loader does not exist or we're referring to an unloaded main
    # module or a main module without path (interactive sessions), go
    # with the current working directory.
    if loader is None or import_name == "__main__":
        return os.getcwd()

    if hasattr(loader, "get_filename"):
        filepath = loader.get_filename(import_name)
    else:
        # Fall back to imports.
        __import__(import_name)
        mod = sys.modules[import_name]
        filepath = getattr(mod, "__file__", None)

        # If we don't have a file path it might be because it is a
        # namespace package. In this case pick the root path from the
        # first module that is contained in the package.
        if filepath is None:
            raise RuntimeError(
                "No root path can be found for the provided module"
                f" {import_name!r}. This can happen because the module"
                " came from an import hook that does not provide file"
                " name information or because it's a namespace package."
                " In this case the root path needs to be explicitly"
                " provided."
            )

    # filepath is import_name.py for a module, or __init__.py for a package.
    return os.path.dirname(os.path.abspath(filepath))
