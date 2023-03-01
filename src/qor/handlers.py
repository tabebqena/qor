from typing import Any, Type

from qor.utils import int_to_method_name, parse_return_value
from qor.wrappers import Request


class raw_handler:
    """a decorator that convert any method to raw ``kore`` handler
    func:
       should recieve  at least  one argument `req`
       should return tuple of `int` status & `bytes` data.
    """

    def __init__(self, func) -> None:
        self.func = func

    def __call__(self, req, *args: Any, **kwds: Any) -> Any:
        status, data = self.func(req)
        req.response(status, data)


class rawp_handler:
    """a decorator that convert any method to raw ``kore`` handler, that can return any of the following:
    - Tuple[int, bytes]
    - Tuple[int, syting]
    - Tuple[int, dict]
    - Tuple[int, list]
    func:
       should recieve at least one argument `req`
    """

    def __init__(self, func) -> None:
        self.func = func

    def __call__(self, req, *args: Any, **kwds: Any) -> Any:
        status, data = parse_return_value(self.func(req))

        req.response(status, data)


class HandlerMixin:
    """
    valid `pyKore` handler
    """

    route_to_methods = False

    def __init__(self, route_to_methods=False) -> None:
        self.route_to_methods = route_to_methods

    def dispatch_request(self, req):
        """override this method to handle the comming request, or leave it & override `get`, `put` etc"""
        if self.route_to_methods:
            method_name = int_to_method_name(req.method)
            return getattr(self, method_name, self.method_not_found)(req)
        else:
            raise (NotImplementedError)

    def after_response(self, req, rv):
        """Override this to run something after sending the response"""
        ...

    def before_handler(self, req):
        """run before handling the request
        its return value not implemented yet"""
        ...

    def method_not_found(self, req):
        return 403, b"Method not allowed"

    @classmethod
    def as_view(cls: "Type[HandlerMixin]", name, *cls_args, **cls_kwargs):
        def view(request: Request):
            instance = cls(*cls_args, **cls_kwargs)
            instance.before_handler(request)
            rv = instance.dispatch_request(request)
            instance.after_response(request, rv)
            return rv

        view.__name__ = name
        view.__doc__ = cls.__doc__
        return view
