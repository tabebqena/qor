from qor import Route, Router
from qor.router import END, SLASH, START, find_between, path_converters


def verify(req):
    return True


def test_route():
    r = Route()
    assert r.path is None
    assert r.handler is None
    assert r.method is None
    assert r.domain is None
    assert r.params == {}
    assert r.key == ""
    assert r.has_auth == False
    assert r.auth_name is None
    assert r.auth_type is None
    assert r.auth_value is None
    assert r.auth_redirect is None
    assert r.auth_verify is None
    assert r.auth == {}
    assert r.class_args == ()
    assert r.class_kwargs == {}

    assert not r.has_auth


def test_route_set_auth_dict():
    _auth = {
        "auth_type": "header",
        "auth_value": "x-header",
        "auth_redirect": "/login",
        "auth_verify": verify,
    }
    r = Route(auth=_auth)
    assert r.path is None
    assert r.handler is None
    assert r.method is None
    assert r.domain is None
    assert r.params == {}
    assert r.key == ""
    assert r.auth_type == _auth.get("auth_type")
    assert r.auth_value == _auth.get("auth_value")
    assert r.auth_redirect == _auth.get("auth_redirect")
    assert r.auth_verify == _auth.get("auth_verify")
    assert r.has_auth == True
    assert r.auth == {
        "type": "header",
        "value": "x-header",
        "redirect": "/login",
        "verify": verify,
    }
    assert r.class_args == ()
    assert r.class_kwargs == {}


def test_route_set_auth_name():
    _auth_name = "is_user"
    r = Route(auth_name=_auth_name)
    assert r.path is None
    assert r.handler is None
    assert r.method is None
    assert r.domain is None
    assert r.params == {}
    assert r.key == ""
    assert r.auth_name == _auth_name
    assert r.auth_type is None
    assert r.auth_value is None
    assert r.auth_redirect is None
    assert r.auth_verify is None
    assert r.has_auth

    assert r.class_args == ()
    assert r.class_kwargs == {}


def test_route_get_auth():
    r = Route()
    _type = "header"
    _value = "x-header"

    r["auth_type"] = _type
    r["auth_value"] = _value
    r["auth_verify"] = verify
    r["auth_redirect"] = "/"

    assert r.has_auth
    assert r.auth["type"] == _type
    assert r.auth["value"] == _value
    assert r.auth["verify"] == verify
    assert r.auth["redirect"] == "/"


def test_route_get_auth_no_redirect():
    r = Route()
    _type = "header"
    _value = "x-header"

    r["auth_type"] = _type
    r["auth_value"] = _value
    r["auth_verify"] = verify

    assert r.has_auth
    assert r.auth["type"] == _type
    assert r.auth["value"] == _value
    assert r.auth["verify"] == verify
    assert not "redirect" in r.auth
