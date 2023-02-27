from qor import Route, Router
from qor.router import END, SLASH, START, find_between, path_converters

#####################


def test_router_init1():
    r = Router()
    assert r.name == ""


def test_router_init2():
    r = Router(name="A")
    assert r.name == "A"
    assert "A" in str(r)


def test_router_init3():
    r = Router()
    assert r.name == ""


def test_router_init4():
    r = Router(allow_override=True)
    assert r.allow_override


def test_router_init5():
    r = Router(path_conveters={"any": ".*"})
    assert r._path_converters["any"]

