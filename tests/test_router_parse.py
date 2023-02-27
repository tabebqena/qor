from qor.router import Router


def test_parse_path():
    router = Router()

    router.add_route(path="user/<id:int>", handler=None)
    router.build_routes()

    r = router.routes[0]

    assert r.parts
    assert not r.parts[0]["isreg"]
    assert  r.parts[0]["value"] == ""
    
    
    assert not r.parts[1]["isreg"]
    assert  r.parts[1]["value"] == "user"
    
    assert r.parts[2]["isreg"]
    assert  r.parts[2]["name"] == "id"
