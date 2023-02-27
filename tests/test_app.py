from qor import Qor, Router


def test_app_name():
    app = Qor()
    assert app.name == ""
    app = Qor("App")
    assert app.name == "App"


def test_no_config():
    app = Qor()
    assert app.config
    assert isinstance(app.config, dict)
    assert app.config["workers"]


def test_config():
    app = Qor(config={"workers": 5})
    assert app.config["workers"] == 5


def test_router():
    router = Router("app")

    app = Qor(router=router)
    assert app.router == router
