"""Example 2
You will learn:
- using templates

"""
import datetime
import os

from db import BlogDatabase

from qor import Qor, Request

app = Qor(import_name=__name__)
database = BlogDatabase(os.path.join(os.path.dirname(__file__), "db.json"))


@app.get("/")
@app.get("/posts", name="posts")
def posts_view(request: "Request", **kwargs):
    return request.render_template("index.html", posts=database.posts)


@app.get("/post_detail/<id>", name="post_detail")
def post_detail(request: "Request", post_id, **kwargs):
    if post_id in database.posts:
        database.increment_post_seen(post_id)
        return request.render_template(
            "post_detail.html", post=database.posts.get(post_id)
        )
    return 404, "Post not found"


# TODO bug-fix: content doesn't accept muli line text
@app.get("/create", name="post_create")
@app.post(
    "/create",
    name="post_create",
    params={
        "title": ".*",
        "content": ".*",
    },
)
def post_create(request: "Request", **kwargs):
    if request.method == "get":
        return request.render_template("create_post.html")

    title = request.argument("title")
    content = request.argument("content")

    if title and content:
        post_id = str(len(database) + 1)
        database.add_post(
            post_id,
            title=title,
            content=content,
            date=str(datetime.datetime.now().date()),
        )
        return request.redirect(request.app.reverse("post_detail", id=post_id))

        # return f"<a href='{url}'>{title}</a>"
    elif not title:
        return 400, "request error, missed title "
    elif not content:
        return 400, "request error, missed content "


@app.post("/delete/<id:int>", name="post_delete")
def delete_post(request: "Request", id, **kwargs):
    database.delete_post(id)
    return request.redirect(request.app.reverse("posts"))


# the app name should be `koreapp` (rquired by kore)
koreapp = app
