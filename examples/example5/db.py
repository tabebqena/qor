import json
import os

POSTS_PATH = os.path.join(os.path.dirname(__file__), "db.json")


class PostDatabase(dict):
    # Demo database, Please use a real database in production
    def __init__(self):
        if not os.path.exists(POSTS_PATH):
            self.save()

        self.read()

    def save(self):
        with open(POSTS_PATH, "w") as f:
            f.write(json.dumps(self, indent=4))

    def read(self):
        with open(POSTS_PATH) as f:
            data = f.read()
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


posts_database = PostDatabase()
