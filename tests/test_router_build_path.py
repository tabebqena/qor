import pytest

from qor.router import Route, Router, build_path, path_converters


def test_valid_empty():
    r = Route(
        parts=[
            {"isreg": False, "value": ""},
        ]
    )
    assert build_path(r, id=5) == ""


def test_valid_no_rejex():
    r = Route(
        parts=[
            {"isreg": False, "value": ""},
            {"isreg": False, "value": "user"},
        ]
    )
    assert build_path(r, id=5) == "/user"


def test_valid_no_rejex2():
    r = Route(
        parts=[
            {"isreg": False, "value": ""},
            {"isreg": False, "value": "user"},
            {"isreg": False, "value": "info"},
        ]
    )
    assert build_path(r, id=5) == "/user/info"


def test_valid_int():
    r = Route(
        parts=[
            {"isreg": False, "value": ""},
            {"isreg": False, "value": "user"},
            {"isreg": True, "name": "id", "re": path_converters["int"]},
        ]
    )
    assert build_path(r, id=5) == "/user/5"


def test_valid_string():
    r = Route(
        parts=[
            {"isreg": False, "value": ""},
            {"isreg": False, "value": "user"},
            {"isreg": True, "name": "name", "re": path_converters["string"]},
        ]
    )
    assert build_path(r, name="ahmad") == "/user/ahmad"


def test_valid_float():
    r = Route(
        parts=[
            {"isreg": False, "value": ""},
            {"isreg": False, "value": "user"},
            {"isreg": True, "name": "age", "re": path_converters["float"]},
        ]
    )
    assert build_path(r, age="10.5") == "/user/10.5"


def test_valid_all():
    r = Route(
        parts=[
            {"isreg": False, "value": ""},
            {"isreg": False, "value": "user"},
            {"isreg": True, "name": "id", "re": path_converters["int"]},
            {"isreg": True, "name": "name", "re": path_converters["string"]},
            {"isreg": True, "name": "age", "re": path_converters["float"]},
        ]
    )
    assert build_path(r, id=5, age="10.5", name="ahmad") == "/user/5/ahmad/10.5"


def test_inadequate_kwargs():
    r1 = Route(
        parts=[
            {"isreg": False, "value": ""},
            {"isreg": False, "value": "user"},
            {"isreg": True, "name": "id", "re": path_converters["int"]},
        ]
    )
    r2 = Route(
        parts=[
            {"isreg": False, "value": ""},
            {"isreg": False, "value": "user"},
            {"isreg": True, "name": "age", "re": path_converters["float"]},
        ]
    )
    r3 = Route(
        parts=[
            {"isreg": False, "value": ""},
            {"isreg": False, "value": "user"},
            {"isreg": True, "name": "name", "re": path_converters["string"]},
        ]
    )
    with pytest.raises(Exception) as e:
        build_path(r1)
    with pytest.raises(Exception) as e:
        build_path(r2)
    with pytest.raises(Exception) as e:
        build_path(r3)


def test_part_none_name():
    r1 = Route(
        parts=[
            {"isreg": False, "value": ""},
            {"isreg": False, "value": "user"},
            {"isreg": True, "re": path_converters["int"]},
        ]
    )
    with pytest.raises(Exception) as e:
        build_path(r1)


def test_part_not_matched():
    r1 = Route(
        parts=[
            {"isreg": False, "value": ""},
            {"isreg": False, "value": "user"},
            {"isreg": True, "name": "id", "re": path_converters["int"]},
        ]
    )
    assert build_path(r1, id=5) == "/user/5"
    assert build_path(r1, id="5") == "/user/5"
    with pytest.raises(Exception) as e:
        build_path(r1, id="string_id")
        build_path(r1, id=1.1)


def test_router_build():
    router = Router()
    def handle():
        ...
    router.add_route(
        "user/<id:int>",
        handle,
        "user_page",
    )
    
    router.add_route(
        "user/<name>",
        handle,
        "user_name",
    )
    
    router.add_route(
        "user/<age:float>",
        handle,
        "user_age",
    )
    router.build_routes()
    
    assert router.reverse("user_page", id=5) == "/user/5"
    assert router.reverse("user_page", id="5") == "/user/5"
    
    with pytest.raises(Exception) as e:
        router.reverse("user_page", id="p")
    with pytest.raises(Exception) as e:
        router.reverse("user_page", id=1.5)
    
    
    assert router.reverse("user_name", name="ahmad") == "/user/ahmad"
    with pytest.raises(Exception) as e:
        router.reverse("user_name", id=8)
    with pytest.raises(Exception) as e:
        router.reverse("user_name")
        
    with pytest.raises(Exception) as e:
        router.reverse("user_delete")
        
    
    