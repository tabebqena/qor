"""
What you will learn?
- initialze app.
- adding routes.
- returning different types from the handler.
- setting the response status exclusively.

How to run this app?

- cd the_dir_of_the_app
- qor run
- usually the app will be served on: 127.0.0.1:8888
- use any client to test the endpoints

"""


from qor import Qor

# the app name should be `koreapp` (rquired by kore)
koreapp = Qor()


@koreapp.route("/string")
def string(request, **kwargs):
    """This is a handler that returns string"""
    return "Hello World"


@koreapp.route("/int")
def _int(request, **kwargs):
    """This is a handler that returns integer"""
    return 10


@koreapp.route("/float")
def _float(request, **kwargs):
    """This is a handler that returns float"""
    return 10.5


@koreapp.route("/bytes")
def _bytes(request, *args, **kwargs):
    """This is a handler that returns bytes"""
    return b"Hello World"


@koreapp.route("/status")
def _status(request, *args, **kwargs):
    """This is a handler that sets the status code exclussively"""
    return 200, "Hello World"


@koreapp.route("/dict")
def _dict(request, *args, **kwargs):
    """This is a handler that returns dictionary. check the content type of the response"""
    return {"msg": "This is a dictionary & converted automagically to json"}


@koreapp.route("/list")
def _list(request, *args, **kwargs):
    """This is a handler that returns dictionary. check the content type of the response"""
    return ["item", "item", "item"]


@koreapp.route("/tuple2")
def _list(request, *args, **kwargs):
    """This is a handler that returns dictionary. check the content type of the response"""
    # If the tuple length is 2 , You should explicity set the status code
    # If you forget this, The first tuple item will be used as the status code
    return 200, ("item", "item")


@koreapp.route("/tuple")
def _list(request, *args, **kwargs):
    """This is a handler that returns dictionary. check the content type of the response"""
    # If the tuple length is 2 , You should explicity set the status code
    # If you forget this, The first tuple item will be used as the status code
    return 200, ("item",)


@koreapp.route("/tuple3")
def _list(request, *args, **kwargs):
    """This is a handler that returns dictionary. check the content type of the response"""
    # If the tuple length is 2 , You should explicity set the status code
    # If you forget this, The first tuple item will be used as the status code
    return 200, ("item", "item", "item")


@koreapp.route("/error")
def _error(request, *args, **kwargs):
    """This is a handler that sets a status error code"""
    return 400, {"msg": "BAD REQUEST"}
