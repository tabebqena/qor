try:
    from jinja2 import (
        BaseLoader,
        Environment,
        FileSystemLoader,
        PackageLoader,
        Template,
        TemplateNotFound,
        select_autoescape,
    )
except:
    pass
import os
from typing import TYPE_CHECKING, List, Union

if TYPE_CHECKING:
    from qor import Qor


class BaseTemplateAdapter:
    def __init__(self, app: "Qor"):
        self.configure_self(app)
        pass

    def configure_self(self, app):
        pass

    def get_template(self, template_name) -> "Template":
        raise NotImplementedError()

    def render(self, tempalte_name, *args, **kwargs) -> str:
        raise NotImplementedError()


class JinjaAdapter(BaseTemplateAdapter):
    enviroment_cls = Environment
    loader_cls = FileSystemLoader

    def __init__(
        self,
        app: "Qor",
    ) -> None:
        self.app = app
        self.configure_self(app)

    def configure_self(self, app: "Qor"):
        self.search_paths = []
        root = app.config.get("root_path", None)
        templates_dirs = app.config.get("template_dirs", [])
        templates_folder_name = app.config.get(
            "templates_folder_name", "templates"
        )

        if templates_dirs:
            if root:
                dirs = [os.path.join(root, p) for p in templates_dirs]
            self.search_paths.extend(dirs)
        elif root:
            self.search_paths.append(os.path.join(root, templates_folder_name))

        self.env = self.enviroment_cls(
            loader=self.loader_cls(searchpath=self.search_paths),
            autoescape=select_autoescape(),
        )

    def get_template(
        self, template_name: Union[str, Template, List[Union[str, Template]]]
    ):
        try:
            return self.env.get_or_select_template(template_name)
        except TemplateNotFound as e:
            raise Exception(
                f"can't find tempalte {template_name}, serach paths:"
                f" {self.search_paths}"
            )

    def render(
        self,
        template_name: Union[str, Template, List[Union[str, Template]]],
        *args,
        **kwargs,
    ):
        template = self.get_template(template_name)

        return template.render(*args, **kwargs)
