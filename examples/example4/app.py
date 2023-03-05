"""Example 3
You will learn:
- using route auth

"""
from qor import Qor, Request

app = Qor()

users = [
    {"name": "admin 1", "is_admin": True, "token": "123"},
    {"name": "user 1", "is_admin": False, "token": "456"},
]


def got_it(*args, **kwargs):
    print(args, kwargs)


@app.auth("user", "header", "X-AuthToken", redirect_url=got_it)
def is_user(request, auth_value, **kwargs):
    for user in users:
        if user.get("token") == auth_value:
            request.g["user"] = user
            return True
    return False


@app.cookie_auth("admin", "X-AuthToken")
def is_admin(request, auth_value, **kwargs):
    for user in users:
        if user.get("token") == auth_value and user.get("is_admin"):
            request.g["user"] = user
            return True
    return False


@app.route("/u", auth_name="user")
def user_only(request, **kwargs):
    return f"Welcome {request.g.get('user', {}).get('name')}"


@app.route("/a", auth_name="admin")
def admin_only(request, **kwargs):
    return f"Welcome {request.g.get('user', {}).get('name')}"


# the app name should be `koreapp` (rquired by kore)
koreapp = app
