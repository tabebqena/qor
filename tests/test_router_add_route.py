import pprint
import pytest

from qor.router import Route, Router


def verify(req):
    return True


#####################


def index(req):
    pass


def about(req):
    pass


def test_router_add_route():
    r = Router()
    r.add_route(
        "/",
        index,
        "index",
        domain="*",
        methods=["get", "put", "post"],
        params={"p": ".*"},
        auth_name=None,
    )
    r.build_routes()
    assert r.routes
    assert len(r.routes) == 3
    route: Route = r.routes[0]
    assert route.raw_path == "/"
    assert route.handler == index
    assert route.name == "index"
    assert route.domain == "*"
    assert route.methods == ["get"]
    assert route.method == "get"

    assert route.params == {"p": ".*"}

    assert route.auth_name is None
    assert route.auth_type is None
    assert route.auth_value is None
    assert route.auth_redirect == "/"
    assert route.auth_verify is None
    assert not route.has_auth

    assert r.routes[1].method == "put"
    assert r.routes[1].methods == ["put"]
    assert r.routes[2].method == "post"
    assert r.routes[2].methods == ["post"]


def test_router_route_decorator():
    r = Router()

    @r.route("/", name="_")
    def _():
        ...

    r.build_routes()
    assert r.routes
    assert len(r.routes) == 1
    route: Route = r.routes[0]
    assert route.raw_path == "/"
    assert route.handler == _
    assert route.name == "_"
    assert route.methods == ["get"]
    assert route.method == "get"
    assert route.auth_name is None
    assert route.auth_type is None
    assert route.auth_value is None
    assert route.auth_redirect == "/"
    assert route.auth_verify is None
    assert not route.has_auth


def test_router_add_route_override():
    r = Router(allow_override=True)
    r.add_route(
        "/",
        index,
        "index",
        domain="*",
        methods=["get", "put", "post"],
        params={"p": ".*"},
        auth_name=None,
    )
    r.build_routes()
    assert r.routes
    assert len(r.routes) == 3
    r.add_route(
        "/",
        index,
        "index",
        domain="*",
        methods=["get", "put", "post"],
        params={"p": ".*"},
        auth_name=None,
    )
    r.build_routes()
    assert r.routes
    assert len(r.routes) == 6


def test_router_add_route_no_override():
    r = Router(allow_override=False)
    r.add_route(
        "/",
        index,
        "index",
        domain="*",
        methods=["get", "put", "post"],
        params={"p": ".*"},
        auth_name=None,
    )
    with pytest.raises(Exception) as e:
        r.add_route(
            "/",
            index,
            "index",
            domain="*",
            methods=["get", "put", "post"],
            params={"p": ".*"},
            auth_name=None,
        )


def test_unallowed_method():
    r = Router(allow_override=False)

    with pytest.raises(Exception) as e:
        r.add_route(
            "/",
            index,
            "index",
            domain="*",
            methods=["click"],
            params={"p": ".*"},
            auth_name=None,
        )
