"""
What you will learn?
- various methods for adding routes

How to run this app?

- cd the_dir_of_the_app
- qor run
- usually the app will be served on: 127.0.0.1:8888
- use any client to test the endpoints.

"""


from qor import Qor, Router

# the app name should be `koreapp` (rquired by kore)
koreapp = Qor()


@koreapp.route("/r")
def r(request, **kwargs):
    """usual route, The `get` method is the default"""
    return "route endpoint"


@koreapp.route("/rm", methods=["put", "post", "delete"])
def rm(request, **kwargs):
    """route with explicit method declaration, Note that it doesn't accept `get`"""
    return "route with explicit method declaration"


@koreapp.route("/comp1", methods=["put", "post", "delete"])
@koreapp.route("/comp2", methods=["get"])
def comp12(request, **kwargs):
    """composite route"""
    return "The same handler added two times with different options"


@koreapp.get("/g")
def g(request, **kwargs):
    """get route"""
    return "get route"


@koreapp.post("/po")
def po(request, **kwargs):
    """post route"""
    return "post route"


@koreapp.put("/pu")
def pu(request, **kwargs):
    """put route"""
    return "put route"


@koreapp.patch("/pa")
def pa(request, **kwargs):
    """patch route"""
    return "patch route"


@koreapp.delete("/d")
def d(request, **kwargs):
    """delete route"""
    return "delete route"


@koreapp.get("/comp3")
@koreapp.post("/comp4")
def comp34(request, **kwargs):
    """composite route"""
    return "'get', 'post' etc. can be chained also"


def my_handler(request, **kwargs):
    return "my handler"


# Adding routes to the app router by add_route
koreapp.add_route("/hg", my_handler)
koreapp.add_route("/hp", my_handler, methods=["post"])
# Adding routes from the app.router itself
koreapp.router.add_route("/hd", my_handler, methods=["delete"])

# creating router and mounting it to the application
user_router = Router()


@user_router.route("/")
def list_users(req, **kwargs):
    return "users list"


@user_router.get("/1")
def get_user(req, **kwargs):
    return "get user 1"


@user_router.delete("/d/1")
def del_users(req, **kwargs):
    return "delete user 1"


koreapp.mount_router("/u", user_router)
