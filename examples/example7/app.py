"""
What you will learn?
- using the before & after handler callbacks

How to run this app?

- cd the_dir_of_the_app
- qor run
- usually the app will be served on: 127.0.0.1:8888
- use any client to test the endpoints.

"""


import time

from qor import Context, Qor, Request

# the app name should be `koreapp` (rquired by kore)
koreapp = Qor()


@koreapp.callback("before_handler")
def log_request_start(request, *args, context: Context, **kwargs):
    context.app.log(f"request started {request.path}")


@koreapp.callback("before_handler")
def set_request_time(request, *args, context: Context, **kwargs):
    context.g["start_time"] = time.time()


@koreapp.callback("before_handler")
def catch_dividing(request, *args, context: Context, **kwargs):
    if context.route.name == "divide":
        return "No dividing"


@koreapp.callback("after_handler")
def set_request_time(request, *args, context: Context, **kwargs):
    t = time.time() - context.g["start_time"]
    context.app.log(f"request time: {t}")


@koreapp.callback("error_handler", error=ZeroDivisionError)
def catch_exc(request, *args, context: Context, **kwargs):
    return "division on zero, I catch it"


@koreapp.callback("error_handler", error=500)
def catch_exc(request, *args, context: Context, **kwargs):
    print(request, args, context, kwargs)
    return "division on zero, I catch it"


# Callbacks End
# Routes
@koreapp.route("/a/<first:int>/<second:int>")
def add(request, first, second, **kwargs):
    return first + second


@koreapp.route("/m/<first:int>/<second:int>")
def mult(request, first, second, **kwargs):
    return first * second


@koreapp.route("/d/<first:int>/<second:int>", name="divide")
def d(request, first, second, **kwargs):
    """This handler will never execute, because of the before handler callback"""
    return first / second


@koreapp.route("/e")
def make_error(request, **kwargs):
    """This handler will make error, to show the behavior of error handlers"""

    return 10 / 0
