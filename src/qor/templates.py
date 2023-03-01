try:
    from jinja2 import Environment, PackageLoader, select_autoescape, Template
except:
    pass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qor import Qor


class BaseTemplateAdapter:
    def __init__(self, app: "Qor"):
        pass

    def get_template(self, template_name) -> "Template":
        raise NotImplementedError()

    def render(self, tempalte_name, *args, **kwargs) -> str:
        return self.get_template(tempalte_name).render(*args, **kwargs)


class JinjaAdapter:
    def __init__(self, app: "Qor") -> None:
        self.app = app
        package_name = app.config.get("root_path", None)
        package_path = app.config.get("template_path", "templates")
        encoding = app.config.get("template_encoding", "utf-8")
        self.env = Environment(
            loader=PackageLoader(package_name, package_path, encoding=encoding),
            autoescape=select_autoescape(),
        )

    def get_template(self, template_name):
        return self.env.get_template(template_name)

    def render(self, tempalte_name, *args, **kwargs):
        template = self.get_template(tempalte_name)
        return template.render(*args, **kwargs)
