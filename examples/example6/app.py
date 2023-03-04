"""Example 2
You will learn:
- using templates

"""
import datetime
import os

from db import BlogDatabase

from qor import Context, Qor, Request

app = Qor(import_name=__name__)
database = BlogDatabase(os.path.join(os.path.dirname(__file__), "db.json"))


# @app.context_processor
# def popular_posts():
#     _sorted = [
#         v for v in sorted(database.items(), key=lambda post: post["seen"])
#     ]
#     return {"popular_posts": _sorted[:3]}


@app.get("/posts", name="posts")
def posts_view(request: "Request", context: "Context", **kwargs):
    return context.render_template("index.html", posts=database.posts)


@app.get("/post_detail/<id>", name="post_detail")
def post_detail(request: "Request", post_id, context: "Context", **kwargs):
    if post_id in database.posts:
        database.increment_post_seen(post_id)
        return context.render_template(
            "post_detail.html", post=database.posts.get(post_id)
        )
    return 404, "Post not found"


@app.get("/create", name="post_create")
@app.post(
    "/create", name="post_create", params={"title": ".*", "content": ".*"}
)
def post_create(request: "Request", context: "Context", **kwargs):
    if request.method == "get":
        return context.render_template("create_post.html")
    request.populate()

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
        request.redirect(context.app.reverse("post_detail", id=post_id))

        # return f"<a href='{url}'>{title}</a>"
    elif not title:
        return 400, "request error, missed error "
    elif not content:
        return 400, "request error, missed content "


@app.post("/delete/<id:int>", name="post_delete")
def delete_post(request: "Request", id, context, **kwargs):
    database.delete_post(id)
    return request.redirect(context.app.reverse("posts"))


# the app name should be `koreapp` (rquired by kore)
koreapp = app
