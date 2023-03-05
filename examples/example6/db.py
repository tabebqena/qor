import json
import os


class BlogDatabase(dict):
    # Demo database, Please use a real database in production
    def __init__(self, path):
        self.path = path
        if not os.path.exists(path):
            self.save()

        self.read()

    def save(self):
        with open(self.path, "w") as f:
            f.write(json.dumps(self, indent=4))

    def read(self):
        with open(self.path) as f:
            data = f.read()
            data = data or "{}"
            try:
                data = json.loads(data)
                self.update(data)
            except:
                raise

    def __setitem__(self, __key, __value) -> None:
        rv = super().__setitem__(__key, __value)
        self.save()
        return rv

    def __delitem__(self, __key) -> None:
        rv = super().__delitem__(__key)
        self.save()
        return rv

    @property
    def posts(self):
        return self.get("posts", {})

    def add_post(self, id, **kwargs):
        kwargs["id"] = id
        self.setdefault("posts", {}).setdefault(id, kwargs)
        self.save()

    def get_post(self, id):
        post = self.posts.get(id, None)
        if not post:
            raise Exception(f"post not found with id {id}")
        return post

    def update_post(self, id, **kwargs):
        post = self.get("posts", {}).get(id, {})
        if not post:
            raise Exception(f"post not found with id {id}")
        post.update(kwargs)
        self["posts"][id] = post
        self.save()

    def delete_post(self, id):
        post = self.posts.get(str(id), None)
        if not post:
            raise Exception(f"post not found with id {id}")
        del self["posts"][str(id)]
        self.save()

    def increment_post_seen(self, post_id):
        post = self.get_post(post_id)
        post["seen"] = post.get("seen", 0) + 1
        self.update_post(**post)
