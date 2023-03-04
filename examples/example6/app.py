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


# # @app.route("/posts/<id:int>", methods=["get", "post", "delete"], name="post")
# # def single_post(request: Request, post_id, **kwargs):
# #     if post_id not in posts_database:
# #         return 404, {"message": "Not Found"}
# #     if request.method == "get":
# #         return posts_database[post_id]

# #     if request.method == "post":
# #         new_post_data = request.json
# #         original_data = posts_database.get(post_id)
# #         if new_post_data:
# #             posts_database[post_id] = dict(
# #                 title=new_post_data.get("title") or original_data.get("title"),
# #                 content=new_post_data.get("content")
# #                 or original_data.get("title"),
# #             )
# #             return {
# #                 "message": "updated successfully",
# #                 "url": request.app.router.reverse("post", id=post_id),
# #             }
# #         return 400, "request error"

# #     elif request.method == "delete":
# #         del posts_database[post_id]
# #         return 200, {"message": "success"}


# the app name should be `koreapp` (rquired by kore)
koreapp = app
