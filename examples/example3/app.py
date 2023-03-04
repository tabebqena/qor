"""
What you will learn?
- adding parametrized url
- accessing the args.
- accessing the request object.

How to run this app?

- cd the_dir_of_the_app
- qor run
- usually the app will be served on: 127.0.0.1:8888
- use any client to test the endpoints.

"""


from qor import Qor, Request

# the app name should be `koreapp` (rquired by kore)
koreapp = Qor()


@koreapp.route("/a/<first:int>/<second:int>")
def add(request, first, second, **kwargs):
    return first + second


@koreapp.route("/m/<first:int>/<second:int>")
def mult(request, first, second, **kwargs):
    return first * second


@koreapp.route("/info", methods=["get", "post"])
def info(request: Request, **kwargs):
    return {
        "address": request.client_address,
        "host": request.host,
        "agent": request.agent,
        "headers": request.headers,
        "body": request.body.decode(),
        "path": request.path,
        "method": request.method,
        "content_type": request.content_type,
        "is_form": request.is_form,
        "is_multipart": request.is_multipart,
        "is_json": request.is_json,
        "json": request.json,
    }
