# validate
# serialize
# Deserialize
import inspect
import re
from copy import copy
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, Union

from qor.utils import cached_property

if TYPE_CHECKING:
    from qor import Request


class Field:
    _default_length = "*"
    _re = "{prefix}(.{length})"

    def __init__(
        self,
        name=None,
        required=False,
        default=None,
        prefix=None,
        min=None,
        max=None,
        **kwargs,
    ) -> None:
        self._name = name
        self.prefix = prefix or ""
        self.min = min
        self.max = max
        self._required = required
        self._default = default
        if self.min is not None or self.max is not None:
            if self.min is None:
                self.min = 0
            if self.max is None:
                self.max = 0
        self.kwargs = kwargs

    @property
    def required(self):
        return self._required

    @property
    def name(self):
        return self._name

    @property
    def default(self):
        return self._default

    @cached_property
    def re(self, _re=None, **kwargs):
        return self.regex(_re, **kwargs)

    def regex(self, _re=None, **kwargs):
        _re = _re or self._re
        length = self._default_length
        if self.min is not None or self.max is not None:
            if self.max == 0:
                length = f"{{{self.min},}}"
            else:
                length = f"{{{self.min},{self.max}}}"
        return f"^{_re.format(prefix=self.prefix, length=length)}$"

    def python(self, value):
        return value

    def _oneof(self, items):
        return f"^({'|'.join(items)})$"

    def _or(self, field: "Field", python=None):
        if python is None:

            def _p(val, **kwargs):
                if re.fullmatch(self.re, val):
                    return self.python
                else:
                    return field.python

            python = _p
        return type(
            "Field",
            (Field,),
            {"_re": f"({self.re}|{field.re})", "python": python},
        )


class String(Field):
    _default_length = "+"
    _re = "{prefix}([^\s]{length})"

    def python(self, value):
        return str(value)


class Text(Field):
    _default_length = "+"
    _re = "{prefix}^([a-zA-Z?><;,{{}}[\]\-_+=!@#$%\^&*|'\s)]{length})$"


class Int(Field):
    _default_length = "*"
    _re = "{prefix}([+]?[0-9]{length})"

    def python(self, value):
        return int(value)


class Float(Field):
    _re = "{prefix}(0$|^[+|-]?[1-9][0-9]*$|^[+|-]?\.[0-9]+$|^[+|-]?0\.[0-9]*$|^[+|-]?[1-9][0-9]*\.[0-9]*)$"

    def __init__(self, name=None, prefix=None, min=None, max=None) -> None:
        # override user input as it is not accessible
        super().__init__(name=name, prefix=prefix, min=None, max=None)

    def python(self, value):
        return float(value)


class Decimal(Float):
    def python(self, value):
        return Decimal(value)


class Enum(Field):
    _default_length = ""

    def __init__(
        self,
        values: Union[list, tuple],
        name=None,
        prefix=None,
        min=None,
        max=None,
    ) -> None:
        self.values = values
        super().__init__(name=None, prefix=prefix, min=None, max=None)

    @cached_property
    def re(self):
        enums = f"\\b({'|'.join(self.values)})\\b"
        _re = f"{{prefix}}{enums}{{length}}"
        return super(Enum, self).regex(_re=_re)

    def python(self, values, name=None):
        return Enum(name or "Enum", values)


class Bool(Field):
    truthy = [
        # 1,
        "Y",
        "on",
        "Yes",
        "true",
        "T",
        "y",
        "t",
        "True",
        "yes",
        "YES",
        "TRUE",
        "1",
        "ON",
        "On",
    ]
    falsy = [
        # 0,
        "OFF",
        "N",
        "Off",
        "f",
        "no",
        "False",
        "n",
        "NO",
        "FALSE",
        "off",
        "false",
        "No",
        "0",
        "F",
    ]
    _default_length = ""

    def __init__(self, name=None, prefix=None, min=None, max=None) -> None:
        super().__init__(name=None, prefix=prefix, min=None, max=None)

    @cached_property
    def re(self):
        enums = "|".join(self.truthy + self.falsy)
        _re = f"{{prefix}}\\b({enums}){{length}}\\b"
        return super(Bool, self).regex(_re=_re)

    def python(self, value):
        if value in self.truthy:
            return True

        return False


class Constant(Field):
    _default_length = ""

    def __init__(
        self, value, name=None, prefix=None, min=None, max=None
    ) -> None:
        super().__init__(name=name, prefix=prefix, min=None, max=None)
        self.value = value

    @cached_property
    def re(self):
        _re = f"{{prefix}}\\b({self.value})\\b{{length}}"
        return super(Constant, self).regex(_re=_re)


class Email(Field):
    def __init__(self, name=None, prefix=None, min=None, max=None) -> None:
        super().__init__(name=name, prefix=None, min=None, max=None)

    _default_length = ""
    _re = "([a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)"

    @cached_property
    def re(self):
        return self._re


class IPv4(Field):
    _re = "((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}"

    @cached_property
    def re(self):
        return self._re


class IPv6(Field):
    _re = "(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))"

    @cached_property
    def re(self):
        return self._re


class ValidationError(Exception):
    def __init__(self, errors, *args: object) -> None:
        self.errors = errors
        super().__init__(*args)


class Schema:
    def __init__(self) -> None:
        self.fields = self.__get_schema_fields__()

    def __get_schema_fields__(self):
        attributes = inspect.getmembers(
            self,
            lambda a: not (inspect.isroutine(a))
            # and not (a[0].startswith("__") and a[0].endswith("__")),
        )
        fields = {
            val.name or name: val
            for (name, val) in attributes
            if inspect.isclass(val)
            and issubclass(val, Field)
            or issubclass(val.__class__, Field)
        }
        return fields

    def as_params(self):
        return {
            name: val.re
            for (name, val) in self.fields.items()
            if inspect.isclass(val)
            and issubclass(val, Field)
            or issubclass(val.__class__, Field)
        }

    def validate(self, **data: dict):
        errors = {}
        present = []
        for name, value in data.items():
            present.append(name)
            field = self.fields.get(name)
            if not field:
                continue
            if value is None:
                if field.required:
                    errors[name] = f"field `{name}` is required"
                    continue
                else:
                    continue
            if not re.fullmatch(field.re, value):
                errors[name] = f"invalid value for field `{name}`"
        for name, field in self.fields.items():
            if name in present:
                continue
            if field.required:
                errors[name] = f"field `{name}` is required"
        if errors:
            raise ValidationError(errors)
        return True

    def __parse_object(self, obj):
        rv = {}
        for name, field in self.fields.items():
            rv[name] = getattr(obj, name, field.default)
        return rv

    def dump(self, obj):
        data = self.__parse_object(obj)
        try:
            self.validate(**data)
        except ValidationError as e:
            raise (e)
        rv = {}
        for name, field in self.fields.items():
            value = data.get(name, None)
            if value:
                rv[name] = field.python(value)
            # if not value >> this field is optional and the user omit it
        return rv

    def load(self, obj, data):
        try:
            self.validate(**data)
        except ValidationError as e:
            raise (e)
        for name, field in self.fields.items():
            value = data.get(name, None)
            if value:
                setattr(obj, name, field.python(value))
            # if not value >> this field is optional and the user omit it
        return obj


def populate_from_request(request: "Request", schema: Schema):
    rv = {}
    for name, field in schema.fields.items():
        value = request.argument(name)
        rv[name] = field.python(value or field.default)
    return rv
