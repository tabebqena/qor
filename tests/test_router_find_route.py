from qor.router import Router
import re


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
    )

    r.add_route(
        "/about",
        about,
        "about",
        domain="*",
        methods=["get"],
        auth_name=None,
    )
    r.build_routes()
    route = r.find_route_by_name("index")
    assert route
    assert route.raw_path == "/"
    assert re.compile(route.path).match("/")

    route = r.find_route_by_name("about")
    assert route
    assert route.raw_path == "/about"
    assert re.compile(route.path).match("/about")
