"""Example 2
You will learn:
- reverse url 

"""
from db import posts_database

from qor import Qor, Request

app = Qor()


@app.get("/posts")
@app.post("/posts")
def posts_view(request: "Request", **kwargs):
    if request.method == "get":
        return posts_database
    elif request.method == "post":
        post = request.json
        if post:
            post_id = str(len(posts_database) + 1)
            posts_database[post_id] = dict(
                title=post.get("title"),
                content=post.get("content"),
            )

            return {
                "message": "success",
                "url": request.app.router.reverse("post", id=post_id),
            }
        else:
            return 400, "request error"
    else:
        # This shouldn't be executed.
        return 405, ""


@app.route("/posts/<id:int>", methods=["get", "post", "delete"], name="post")
def single_post(request: Request, post_id, **kwargs):
    if post_id not in posts_database:
        return 404, {"message": "Not Found"}
    if request.method == "get":
        return posts_database[post_id]

    if request.method == "post":
        new_post_data = request.json
        original_data = posts_database.get(post_id)
        if new_post_data:
            posts_database[post_id] = dict(
                title=new_post_data.get("title") or original_data.get("title"),
                content=new_post_data.get("content")
                or original_data.get("title"),
            )
            return {
                "message": "updated successfully",
                "url": request.app.router.reverse("post", id=post_id),
            }
        return 400, "request error"

    elif request.method == "delete":
        del posts_database[post_id]
        return 200, {"message": "success"}


# the app name should be `koreapp` (rquired by kore)
koreapp = app
