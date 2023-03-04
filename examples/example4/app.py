"""Example 3
You will learn:
- using route auth

"""
from qor import Qor, Request

app = Qor()

admin_tokens = {"my-admin-token": "admin1"}
user_tokens = {"token": "user1"}


def got_it(*args, **kwargs):
    print(args, kwargs)


@app.auth("user", "header", "X-AuthToken", redirect_url=got_it)
def is_user(request, auth_value, **kwargs):
    if auth_value in user_tokens:
        print(f"welcome {user_tokens[auth_value]}")
        return True
    return False


@app.cookie_auth("admin", "admin-token")
def is_admin(request, auth_value, **kwargs):
    if auth_value in admin_tokens:
        print(f"welcome {admin_tokens[auth_value]}")
        return True
    return False


@app.route("/u", auth_name="user")
def user_only(request, **kwargs):
    return "I am a user only endpoint"


@app.route("/a", auth_name="admin")
def admin_only(request, **kwargs):
    return "I am a admin only endpoint"


# the app name should be `koreapp` (rquired by kore)
koreapp = app
