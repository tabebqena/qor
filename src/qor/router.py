import copy
import re
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union
from urllib.parse import urljoin

from qor import constants

SLASH = "/"
START = "<"
END = ">"


# Notes on c Kore rejex
# \/[0-9]+      will match /<any_number>
# we should escape the slash
# \d not working !!1
# Named capture groups are not allowed: ?<name>.*


# default path converters to be used in paths,
# user can extend this dict in the `router` and
# can pass pure rejex by using the filter `re`
path_converters = {
    # int is any character from 0-9 repeated one or more times
    "int": "[0-9]+",  # "\d+",  # r"\d+"
    # float is two integers seperated by `.`
    "float": "[0-9]+.[0-9]+",  # r"\d+\.\d+"
    # path is a: string that starts with `/` then any character then optional `/`
    # "path": "(\/.*\/?)",  # "[^/].*?",  # r"[^/].*?",  # "[^/].*?"
    # match any thing except `/`
    "string": "[^\/]+",
    # placeholder for rejex cinverter, the user should provide his own rejex using this converter
    "re": None,
}

# This matches most of the allowed characters in url
# [a-zA-Z0-9_\%\&\=+\$\-\.\!\~\*']+


def find_between(s, start, end):
    rv = ""
    try:
        rv = (s.split(start))[1].split(end)[0]
    except:
        pass
    if rv and f"{start}{rv}{end}" in s:
        return rv
    return ""


def multi_urljoin(*parts):
    _parts = [
        part.replace("/", "", 1) if part.startswith("/") else part for part in parts
    ]
    rv = "/".join(_parts)
    # return urljoin(
    #      parts[0], "/".join(part.strip("/") for part in parts[1:])
    # )
    return rv


def analyze_part(string, path_converters: dict):
    """return variable name & rejex equivalent of string
    Example:

    >> from qor.touter import path_converters
    >> analyze_part("id:int", converters)
    ('id', '\d+' )
    """
    splitted = string.split(":")
    _filter_name = "string"
    _string = string
    if len(splitted) == 1:
        pass
    elif len(splitted) == 2:
        _string = splitted[0]
        _filter_name = splitted[1]
    elif len(splitted) == 3:
        if splitted[1] != "re":
            raise Exception(
                f"the path part {string} has many `:` characters and couldn't be"
                " analyzed."
            )
        else:
            _filter_name = "re"
            _string = splitted[0]

    if _filter_name not in path_converters:
        raise Exception(
            f"the provided converter: `{_filter_name}` is not a registered path"
            " converter. The accepted values are:"
            f" {', '.join(path_converters.keys())}"
        )

    return _string, path_converters[_filter_name] or splitted[2]


def build_path(
    pathPattern: Dict[Literal["parts"], List],
    **kwargs,
) -> Optional[str]:
    """build path from the given path pattern & kwargs

    Args:
        pathPattern Dict[Literal["parts"], List],: the parsed url parts

    Returns:
        str: The path if build process success, else None
    """
    parts = pathPattern.get("parts")
    variables = []
    for p in parts:
        if p.get("isreg", False):
            name = p.get("name")
            if not name:
                raise Exception("Invalid part, part has no name")
            variables.append(name)

    for v in variables:
        if v not in kwargs:
            raise Exception(f"Can't build path, `{v}` is required.")
    outparts = []
    for part in parts:
        if part.get("isreg"):
            # get the value to replace with
            value = str(kwargs.get(part.get("name")))
            # if the given value match the expected pattern, add it. else: return None
            regex = part.get("re")
            compiled = re.compile(regex)
            matched = compiled.match(value)

            if matched and len(matched[0]) == len(value):
                outparts.append(value)
            else:
                raise Exception(
                    f"Can't build path as {value} not matching with {regex}"
                )
        else:
            # append string as it is
            outparts.append(part.get("value"))
    built = "/".join(outparts)
    return built


def kore_re_string(parts, sep="\/"):
    rv = []
    for part in parts:
        if part.get("isreg", True):
            rv.append(f"({part.get('re')})")
        else:
            rv.append(part.get("value"))

    return sep.join(rv)


def python_re_string(parts, sep="\/"):
    rv = []
    for part in parts:
        if part.get("isreg", True):
            rv.append(f"(?P<{part.get('name')}>{part.get('re')})")
        else:
            rv.append(part.get("value"))

    return sep.join(rv)


class Route(dict):
    def __init__(self, **data):
        self.update(
            dict(
                name=None,
                path=None,
                handler=None,
                method=None,
                domain=None,
                params={},
                auth_name=None,
                key="",
                auth_type=None,
                auth_value=None,
                auth_redirect=None,
                auth_verify=None,
                parts=[],
                raw_path=data.get("raw_path", ""),  # or data.get("path", None),
                class_args=(),
                class_kwargs={},
            )
        )
        if data.get("auth", None):
            data.setdefault("auth_type", data.get("auth", {}).get("auth_type"))
            data.setdefault("auth_value", data.get("auth", {}).get("auth_value"))
            data.setdefault("auth_redirect", data.get("auth", {}).get("auth_redirect"))
            data.setdefault("auth_verify", data.get("auth", {}).get("auth_verify"))

        super().__init__(**data)

    @property
    def name(self):
        return self["name"]

    @property
    def path(self):
        return self["path"]

    @property
    def raw_path(self):
        return self["raw_path"]

    @property
    def handler(self):
        return self["handler"]

    @property
    def method(self):
        return self["method"]

    @property
    def methods(self):
        return [self["method"]]

    @property
    def domain(self):
        return self["domain"]

    @property
    def params(self):
        return self["params"]

    @property
    def auth_name(self):
        return self["auth_name"]

    @property
    def auth_type(self):
        return self["auth_type"]

    @property
    def auth_value(self):
        return self["auth_value"]

    @property
    def auth_redirect(self):
        return self["auth_redirect"]

    @property
    def auth_verify(self):
        return self["auth_verify"]

    @property
    def auth(self):
        if not self.has_auth:
            return {}
        if self.auth_redirect:
            return {
                "type": self.auth_type,
                "value": self.auth_value,
                "redirect": self.auth_redirect,
                "verify": self.auth_verify,
            }
        else:
            return {
                "type": self.auth_type,
                "value": self.auth_value,
                "verify": self.auth_verify,
            }

    @property
    def has_auth(self):
        return bool(self.auth_type and self.auth_value and self.auth_verify) or bool(
            self.auth_name
        )

    @property
    def parts(self):
        return self["parts"]

    @property
    def class_args(self):
        return self["class_args"]

    @property
    def class_kwargs(self):
        return self["class_kwargs"]

    @property
    def key(self):
        return self["key"]


class RouterBase:
    def add_route(self, **kwargs):
        raise NotImplementedError()

    def mount_router(self, router):
        raise NotImplementedError()

    def build_routes(self):
        raise NotImplementedError()

    @property
    def routes(self):
        raise NotImplementedError()


class Router(RouterBase):
    _path_converters = path_converters

    def __init__(self, name="", allow_override=False, path_conveters={}) -> None:
        self.name = name
        self._routers: dict[str, "Router"] = {}
        self._raw_routes: list[dict] = []
        self._routes: list[Route] = []
        self.allow_override = allow_override
        if path_conveters:
            self._path_converters = copy.copy(self._path_converters)
            self._path_converters.update(path_conveters)

    def find_raw_route(self, domain: str, path: str, method: str):
        _raw_routes = self._raw_routes
        for route in _raw_routes:
            if (
                "domain" in route
                and "raw_path" in route
                and "method" in route
                and route.get("domain") == domain
                and route.get("raw_path") == path
                and route.get("method") == method
            ):
                return route
        return None

    def find_route(self, domain: str, path: str, method: str):
        _routes = self._routes
        for route in _routes:
            if route.domain == domain and route.path == path and route.method == method:
                return route
        return None

    def find_route_by_name(self, name):
        _routes = self._routes
        for route in _routes:
            if route.name == name:
                return route
        return None

    def add_route(
        self,
        path: str,
        handler: Callable,
        name=None,
        domain: str = None,
        methods=["get"],
        params={},
        auth_name=None,
        key="",
        auth_type=None,  # header or cookie
        auth_value=None,  # header or cookie name
        auth_redirect="/",
        # redirect location upon failure,
        # if not set, 403 is returned.
        auth_verify=None,
    ):
        _methods = []
        for method in methods:
            method = method.lower()
            if method not in constants.ALLOWED_METHODS:
                raise Exception(f"method {method} not allowed")
            _methods.append(method)
        methods = _methods

        if not self.allow_override:
            value = self.find_raw_route(domain, path, method)
            if value:
                raise Exception(
                    "There is already registered handeler for the same domain"
                    f" path, {domain}:{path}"
                )
        # path = (
        #     path.replace("/", "", 1) if path.startswith("/") and len(path) > 1 else path
        # )
        for method in methods:
            self._raw_routes.append(
                dict(
                    name=name,
                    path=None,
                    raw_path=path,
                    handler=handler,
                    method=method,
                    domain=domain,
                    params=params,
                    auth_name=auth_name,
                    key=key,
                    auth_type=auth_type,  # header or cookie
                    auth_value=auth_value,  # header or cookie name
                    auth_redirect=auth_redirect,
                    # redirect location upon failure,
                    # if not set, 403 is returned.
                    auth_verify=auth_verify,
                ),
            )

    def mount_router(self, path: str, router: "Router"):
        """mount child router to this router, this means that the child urls
        will be built as sub urls to this router path.

        example:

        >> child = Router()
        >> child.add_route(path="/child_index", handler="child_index", name="child_index")
        >> main = Router()
        >> main.mount_router("/child", child)
        >> main.build_routes()
        >> for route in main.routes:
              print(route.name, " ", route.path )
        >> child:child_index  /child/child_index

        Args:
            path (str): base bath for all child router paths.
            router (Router): the child router.
        """
        self._routers[path.strip("/")] = router

    @property
    def routes(self):
        return self._routes

    def __join_routes(self, routes, base_names=[], base_paths=[]):
        _routes = []
        for r in routes:
            r["raw_path"] = multi_urljoin(*base_paths, r.get("raw_path"))

            r_name = r.get("name")
            if r_name and base_names:
                _names = copy.copy(base_names)
                _names.append(r_name)
                r["name"] = ":".join(_names).replace(":", "", 1)
            _routes.append(r)
        return _routes

    def __join_self_routes(self, base_names=[], base_paths=[]):
        return self.__join_routes(self._raw_routes, base_names, base_paths)

    def __join_nested_routes(self, base_names=[], base_paths=[]):
        rv = []
        for path, router in self._routers.items():
            rv.extend(
                router.__join_self_routes(
                    base_names + [router.name], base_paths + [path]
                )
            )
            rv.extend(
                router.__join_nested_routes(
                    base_names + [router.name], base_paths + [path]
                )
            )
        return rv

    def __join_all(self, base_names=[], base_paths=[]):
        rv = self.__join_self_routes(base_names + [self.name], base_paths)
        rv.extend(self.__join_nested_routes(base_names + [self.name], base_paths))
        return rv

    # names = all parent names
    # paths = all parent paths
    def build_routes(self, base_name="", base_path="/"):
        self._routes = []
        _routes = self.__join_all([], [base_path])
        for route in _routes:
            if not self.allow_override and self.find_route(
                route.get("domain", None),
                route.get("path", ""),
                route.get("method", []),
            ):
                raise Exception(
                    "Route with the same domain, path & methd is already"
                    f" specified, {route}."
                )
            handler = route.get("handler")
            name = route.get("name", None)

            path_conveters = self._path_converters
            path_conveters.update(route.get("path_conveters", {}))
            raw_path = route.get("raw_path")

            parts = self.parse_route_path(raw_path, path_conveters)
            path = kore_re_string(parts)
            self._routes.append(
                Route(
                    name=name,
                    path=path,
                    raw_path=route.get("raw_path"),
                    handler=handler,
                    method=route.get("method"),
                    domain=route.get("domain"),
                    params=route.get("params"),
                    auth_name=route.get("auth_name"),
                    key=route.get("key"),
                    auth_type=route.get("auth_type"),  # header or cookie
                    auth_value=route.get("auth_value"),  # header or cookie name
                    auth_redirect=route.get("auth_redirect"),
                    # redirect location upon failure,
                    # if not set, 403 is returned.
                    auth_verify=route.get("auth_verify"),
                    parts=parts,
                )
            )

    def route(
        self,
        path: str,
        name=None,
        domain: str = None,
        methods=["get"],
        params={},
        auth_name=None,
        auth_type=None,  # header or cookie
        auth_value=None,  # header or cookie name
        auth_redirect="/",
        # redirect location upon failure,
        # if not set, 403 is returned.
        auth_verify=None,
    ):
        def wrapper(func):
            self.add_route(
                path=path,
                handler=func,
                name=name,
                domain=domain,
                methods=methods,
                params=params,
                auth_name=auth_name,
                auth_type=auth_type,  # header or cookie
                auth_value=auth_value,  # header or cookie name
                auth_redirect=auth_redirect,
                # redirect location upon failure,
                # if not set, 403 is returned.
                auth_verify=auth_verify,
            )
            return func

        return wrapper

    def parse_route_path(self, path: str = "", path_filters={}) -> list:
        """parse path and return its rejex parts & variable names

        Returns:
            None
        """
        if not path:
            return []

        splitted: list[str] = path.split(SLASH)
        parts = []

        for part in splitted:
            if part.startswith(START) and part.endswith(END):
                varname, reg = analyze_part(
                    find_between(part, START, END), path_filters
                )
                parts.append(
                    {
                        "re": reg,
                        "name": varname,
                        "isreg": True,
                    }
                )
            else:
                parts.append(
                    {
                        "name": None,
                        "value": part,
                        "isreg": False,
                    }
                )
        return parts

    def reverse(self, __name, method=None, **kwargs):
        route = self.find_route_by_name(__name)
        if not route:
            raise Exception(f"can't find route for {__name}")
        return build_path(route, **kwargs)

    def __repr__(self) -> str:
        return f"<Router {self.name}>"

    def show_all(self):
        for route in self.routes:
            print(route.name, "    ", route.raw_path)
