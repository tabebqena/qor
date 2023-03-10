import json
import traceback
from inspect import isclass
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple, Union

import qor.constants as constants
from qor.utils import cached_property

if TYPE_CHECKING:
    from qor.app import BaseApp, Qor, Route


class BaseRequest:
    """Why this class?
    To let the user use any request class he want, without breaking
    `get_qor_context` method
    """

    ...


class BaseWrapper:
    def __init__(
        self, func: "Callable", app: "Qor", route: "Route", **kwargs
    ) -> None:
        self.func = func
        self.app: "Qor" = app
        self.route = route
        self.kwargs = kwargs

    def __call__(self, request, *args: Any, **kwargs: Any) -> Any:
        pass
        # unknown request type
        #

    def get_qor_request(self, request, *args, **kwargs) -> "Request":
        """this method will make sure to return qor `Request` objects
        possibility of request argument:
        - qor request   >> return it
        - kore request  >>
        check if has _request member or not, if has: return its memeber.

        if all the above failed, we are sure now that this a kore request object, hits
        Qor application for the furst time, So we should create `Request` object
        and create refrence for the for further calling.

        The purpose of this approach is to create the `Request` object one time only for each request & make use of
        `kore` handler that are not aware of our `Request` object.
        """
        if isinstance(request, BaseRequest):
            return request
        _request = getattr(request, "_request", None)
        if _request:
            return _request

        qor_request = self.app.wrap_request(request, *args, **kwargs)
        setattr(request, "_request", qor_request)
        return qor_request


class DefaultHandlerWrapper(BaseWrapper):
    """This is the default wrapper for all handlers.
    By using it the handler will recieve, `Request` object and can return any of:
    - bytes
    - string
    - dict
    - list
    - Tuple[int, bytes]
    - Tuple[int, syting]
    - Tuple[int, dict]
    - Tuple[int, list]
    """

    def __init__(self, func, app, route: "Route", **kwargs) -> None:
        super().__init__(func=func, app=app, route=route, **kwargs)
        self.return_value_parser = app.return_value_parser
        self.re_parts = []
        for part in self.route.parts:
            if part.get("isreg", False):
                self.re_parts.append(part)
        self.re_parts_length = len(self.re_parts)

    def __prepare_args(self, *args):
        rv = []
        parts = self.re_parts
        if len(args) == self.re_parts_length:
            for index, arg in enumerate(args):
                part = parts[index]
                rv.append(part.get("to_python", lambda v: v)(arg))
            return rv
        return args

    def __run_before_handler(
        self,
        request: "Request",
        *args,
        **kwargs,
    ):
        before_handler_callbacks = self.app._before_handler_callbacks
        for cb in before_handler_callbacks:
            rv = cb(request, *args, **kwargs)
            if rv is not None:
                return rv

    def __run_after_handler(
        self,
        request: "Request",
        *args,
        **kwargs,
    ):
        after_handler_callbacks = self.app._after_handler_callbacks
        for cb in after_handler_callbacks:
            rv = cb(request, *args, **kwargs)
            if rv is not None:
                request.return_value = rv
                return

    def __run_error_callbacks(
        self,
        request: "Request",
        status_or_exc: Union[int, Exception],
        *args,
        **kwargs,
    ):
        _error_handlers = self.app._error_handlers
        is_int = isinstance(status_or_exc, int)
        is_exc = isinstance(status_or_exc, Exception)

        if is_int:
            for error_handler in _error_handlers:
                error = error_handler.get("kwargs", {}).get("error")
                cb = error_handler.get("func", None)
                if isinstance(error, int) and error == status_or_exc:
                    error_cb_rv = cb(request, *args, **kwargs)
                    if error_cb_rv is not None:
                        request.return_value = error_cb_rv
                        return
        elif is_exc:
            for error_handler in _error_handlers:
                error = error_handler.get("kwargs", {}).get("error")
                cb = error_handler.get("func", None)
                if isclass(error) and issubclass(
                    status_or_exc.__class__, error
                ):
                    error_cb_rv = cb(request, *args, **kwargs)
                    if error_cb_rv is not None:
                        request.return_value = error_cb_rv
                        return

    def send_response(self, request: "Request", *args, **kwargs):
        status, data, original_type = self.return_value_parser(
            request.return_value, self, self.app, request, *args, **kwargs
        )
        if not request.get_response_header("Content-Type"):
            if original_type in (dict, tuple, list):
                request.response_header("Content-Type", "application/json")
            else:
                request.response_header("Content-Type", "text/html")

        request.response(status, data)

    def __call__(self, kore_request, *args: Any, **kwargs: Any) -> Any:
        args = self.__prepare_args(*args)

        qor_request = self.get_qor_request(kore_request, *args, **kwargs)
        qor_request.set_route(self.route)

        try:
            rv = self.__run_before_handler(qor_request, *args, **kwargs)
            if rv is not None:
                qor_request.return_value = rv
                self.__run_after_handler(qor_request, *args, **kwargs)
                self.send_response(qor_request, *args, **kwargs)
                return
            # call the handler function
            rv = self.func(qor_request, *args, **kwargs)
            qor_request.return_value = rv
            # try to parse the return value
            status, data, original_type = self.return_value_parser(
                rv, self, self.app, qor_request, *args, **kwargs
            )
            qor_request.response_status = status
            qor_request.response_data = data

            if status >= 400:
                self.__run_error_callbacks(
                    qor_request,
                    status,
                    *args,
                    **kwargs,
                )
                self.send_response(qor_request, *args, **kwargs)
                return

            else:
                # run th eafter_handler callbacks if there is no error
                self.__run_after_handler(qor_request, *args, **kwargs)
                self.send_response(qor_request, *args, **kwargs)
                return

        except Exception as e:
            self.__run_error_callbacks(
                qor_request,
                e,
                *args,
                **kwargs,
            )
            if qor_request.return_value:
                self.send_response(qor_request, *args, **kwargs)
            else:
                raise


class simple_wrapper(BaseWrapper):
    def __init__(
        self, func: "Callable", app: "Qor", route=None, **kwargs
    ) -> None:
        super().__init__(func=func, app=app, route=route, **kwargs)

    def __call__(self, request, *args: Any, **kwargs: Any) -> Any:
        qor_request = self.get_qor_request(request, *args, **kwargs)
        return self.func(qor_request, *args, **kwargs)

    def __repr__(self) -> str:
        return f"<Simple Wrapper {self.func.__repr__}>"


class File:
    def __init__(self, file) -> None:
        self.file = file
        self.size = 0  # the size that read till now
        self.data = None
        self._read = False  # whether it is read to its end or not

    @property
    def filename(self) -> str:
        return self.file.filename

    @property
    def name(self) -> str:
        return self.file.name

    def read(self, size: int = 1024) -> Tuple[int, bytes]:
        if size > 1024:
            raise RuntimeError("Can't read more than 1024 in each time")
        size, data = self.file.read(size)
        self.size += size
        self.data += data
        if size == 0:
            self._read = True
        return size, data

    def bulk_read(self, limit=0) -> bytes:
        """read from the start of the file to limit (approximately), if limit is 0, read till end"""
        if self._read:
            return self.data
        if self.size > limit:
            return self.data
        while True:
            size, _ = self.read(1024)
            if limit > 0 and self.size > limit:
                break
            if size == 0:
                break
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    # TODO use iterator


class Connection:
    """Resemble kore.connection object"""

    @property
    def addr(self) -> str:
        """return the client remote address (ip)"""
        ...

    def disconnect(self):
        ...

    def websocket_send(self, data):
        ...


class Request(BaseRequest):
    HTTP_METHOD_GET = constants.HTTP_METHOD_GET  # 1
    HTTP_METHOD_PUT = constants.HTTP_METHOD_PUT  # 4
    HTTP_METHOD_HEAD = constants.HTTP_METHOD_HEAD  # 32
    HTTP_METHOD_POST = constants.HTTP_METHOD_POST  # 2
    HTTP_METHOD_DELETE = constants.HTTP_METHOD_DELETE  # 16
    HTTP_METHOD_OPTIONS = constants.HTTP_METHOD_OPTIONS  # 64
    HTTP_METHOD_PATCH = constants.HTTP_METHOD_PATCH  # 128

    def __init__(
        self, kore_request, app: "Qor", route=None, *args, **kwargs
    ) -> None:
        self.request = kore_request
        self.app = app
        self.route = route
        self.g = {}

        #
        self.response_status = None
        self._response_headers = {}
        self.response_data = None
        self.return_value = None
        #
        self._populated = False
        self._json = None
        self._form = None
        self.args = args
        self.kwargs = kwargs

    @cached_property
    def method(self) -> str:
        return constants.METHOD_CODES[self.request.method]

    @cached_property
    def host(self) -> str:
        """The domain as a unicode string."""
        return self.request.host

    @cached_property
    def agent(self) -> str:
        """The user agent as a unicode string."""
        return self.request.agent

    @cached_property
    def path(self) -> str:
        """The requested path as a unicode string."""
        return self.request.path

    @cached_property
    def body(self) -> bytes:  # PyBuffer
        """The entire incoming HTTP body as a PyBuffer."""
        return self.request.body

    @cached_property
    def headers(self) -> dict:
        """the request headers as dictionary"""
        return self.request.headers()

    @cached_property
    def _method_int(self) -> int:
        """The requested method as a PyLong. (kore.HTTP_METHOD_GET, etc)."""
        return self.request.method

    @cached_property
    def body_path(self) -> str:
        """The path to the HTTP body on disk (if enabled)."""
        return self.request.body_path

    @cached_property
    def connection(self) -> "Connection":
        """The underlying client connection as a kore.connection object."""
        return self.request.connection

    @cached_property
    def client_address(self) -> str:
        return self.connection.addr

    @cached_property
    def content_type(self) -> str:
        return self.request_header("Content-Type") or ""

    @cached_property
    def mimetype(self):
        return self.content_type.split(";")[0].strip()

    @cached_property
    def is_form(self):
        return self.mimetype in (
            "multipart/form-data",
            "application/x-www-form-urlencoded",
        )

    @cached_property
    def is_multipart(self):
        return self.mimetype == "multipart/form-data"

    @cached_property
    def is_json(self):
        return self.mimetype == "application/json"

    def cookie(self, name) -> Optional[str]:
        """Returns the cookie value for a given name.
        Example
        def handler(req):
            cookie = req.cookie("my_session")
            if cookie != None:
                # use cookie value to do things.
        """
        return self.request.cookie(name)

    def response(self, status: int, body: bytes) -> None:
        """Creates an HTTP response for the given HTTP request.
        status	The HTTP status code to include in the response.

        body The HTTP body to be included in the response, this must be a binary buffer.

        Example
        def handler(req):
            req.response(200, b'ok')
        """
        return self.request.response(status, body)

    def argument(self, name: str) -> Optional[str]:
        """value = req.argument(name)
        Description
        Looks up an HTTP parameter that was previously validated via a Kore params block in the configuration.

        Parameter	Description
        name	The name of the parameter to lookup.
        Returns The parameter as a unicode string or None if it was not found.

        Example
        def handler(req):
            id = req.argument("id")
            if id != None:
                # got an id from somewhere
        """
        self.populate()
        return self.request.argument(name)

    def body_read(self, length: int = 1024) -> Tuple[int, str]:
        """
        length, chunk = req.body_read(length)
        Description
        Reads up to length bytes from the HTTP body and returns the actual bytes read and data in a tuple.

        A returned length of 0 bytes indicates the end of the HTTP body.

        A RuntimeError exception is thrown if the length parameter is greater than 1024.

        Parameter	Description
        length	The number of bytes to read.
        Returns
        The length and data read.

        Example
        def handler(req):
            if req.method == kore.HTTP_METHOD_POST:
                try
                    length, body = req.body_read(1024)
                    # do stuff with the body.
                except:
                    kore.log(kore.LOG_INFO, "some error occurred")
                    req.response(500, b'')
        """
        if length > 1024:
            raise Exception("length can't be more than 1024")
        return self.request.body_read(length)

    def file_lookup(self, name: str) -> File:
        # should call populate_multi before
        """
        file = req.file_lookup(name)
        Description
        Lookup an uploaded file (via multipart/form-data).

        Parameter	Description
        name	The name of the file that was uploaded.
        Returns
            A kore.http_file object that can be used to read data from.

        Example
        def handler(req):
            if req.method == kore.HTTP_METHOD_POST:
                req.populate_multi()
                try
                    file = req.file_lookup("myfile")
                    length, data = file.read(1024)
                    # do stuff with the data .
                except:
                    kore.log(kore.LOG_INFO, "some error occurred")
                    req.response(500, b'')"""
        return self.request.file_lookup(name)

    @cached_property
    def json(self):
        self.populate()
        return self._json

    @cached_property
    def form(self):
        self.populate()
        return self._form

    def populate(self):
        """popultate request according to its mime type"""
        if self._populated:
            return
        self.populate_get()
        if self.is_multipart:
            self.populate_multipart()
            self._form = self.body
        elif self.is_form:
            self.populate_post()
            self._form = self.body
        elif self.is_json:
            self._json = json.loads(self.body)

    def populate_get(self) -> None:
        """
        req.populate_get()
        Description
        Instructs Kore to go ahead and parse the incoming querystring and validate parameters according to the configured params {} blocks in the configuration.

        Returns
        Nothing"""
        self.request.populate_get()

    def populate_post(self) -> None:
        """
        Synopsis
        req.populate_post()
        Description
        Instructs Kore to go ahead and parse the incoming POST data which is of content-type application/x-www-form-urlencoded and validate parameters according to the configured params {} blocks in the configuration.

        Returns
        Nothing"""
        return self.request.populate_post()

    def populate_multipart(self) -> None:
        """Synopsis   req.populate_multipart()
        Description
        Instructs Kore to go ahead and parse the incoming body as content-type multipart/form-data and validate parameters according to the configured params {} blocks in the configuration.

        Returns
        Nothing"""
        return self.request.populate_multi()

    def populate_cookies(self) -> None:
        """Synopsis
        req.populate_cookies()
        Description
        Instructs Kore to go ahead and parse the incoming cookie header (if any).

        Returns
        Nothing"""
        return self.request.populate_cookies()

    def request_header(self, name: str) -> str:
        """request_header
        Synopsis
        value = req.request_header(name)
        Description
        Finds the incoming request header by name and returns it.

        Parameter	Description
        name	The name of the header to lookup.
        Returns
            The value of the header as a unicode string or None if the header was not present.

        Example
        def myhandler(req):
            xrequest = req.request_header("x-request")
            if xrequest != None:
                req.response_header("x-response", xrequest)

            req.response(200, b'hello world')"""
        return self.request.request_header(name)

    def set_cookie(self, name, value):
        return self.response_header("Set-Cookie", f"{name}={value}")

    def response_header(self, name: str, value) -> None:
        """Synopsis
        req.response_header(name, value)
        Description
        Adds the given header to the response that will be sent by req.response().

        Parameter	Description
        name	The name of the header that will be added.
        value	The value of the header that will be added.
        Returns
            Nothing

        Example
        def myhandler(req):
            xrequest = req.request_header("x-request")
            if xrequest != None:
                req.response_header("x-response", xrequest)

            req.response(200, b'hello world')"""
        self._response_headers[name] = value
        self.request.response_header(name, value)

    def get_response_header(self, name):
        return self._response_headers.get(name)

    def websocket_handshake(self, onconnect, onmsg, ondisconnect) -> None:
        """Synopsis
        req.websocket_handshake(onconnect, onmsg, ondisconnect)
        Description
        Adds the given header to the response that will be sent by req.response().

        Parameter	Description
        onconnect	The name of the function to be called when a new websocket client is connected.
        onmsg	The name of the function to be called when a websocket message arrives.
        ondisconnect	The name of the function to be called when a new websocket client is removed.
        Returns
            Nothing

        Example
        def onconnect(c):
            kore.log(kore.LOG_INFO, "%s: connected" % c)
        def onmessage(c, op, data):
            # data from c arrived
            # op is the websocket op, WEBSOCKET_OP_TEXT, WEBSOCKET_OP_BINARY
            # data is the data that arrived

        def ondisconnect(c):
            kore.log(kore.LOG_INFO, "%s: disconnected" % c)

        def ws_connect(req):
            req.websocket_handshake("onconnect", "onmsg", "ondisconnect")
        """
        self.request.websocket_handshake(onconnect, onmsg, ondisconnect)

    def redirect(self, url, perminant=True):
        """return redirect resonse"""
        self.response_header("Location", url)
        return 302 if perminant else 301, b""

    def reverse(self, name, **kwargs):
        return self.app.reverse(name=name, **kwargs)

    def set_route(self, route):
        self.route = route

    def render_template(self, template_name, *args, **kwargs):
        kwargs.update(
            {
                "app": self.app,
                "request": self,
                "g": self.g,
                "context_kwargs": self.kwargs,
                "reverse": self.reverse,
            }
        )
        return self.app._render_template(template_name, *args, **kwargs)

    def log_info(self, message: str):
        self.app.log(message, self.app.LOG_INFO)

    def log_notice(self, message: str):
        self.app.log(message, self.app.LOG_NOTICE)

    def log_error(self, message: str):
        self.app.log(message, self.app.LOG_ERR)

    def log_exception(self, e: Exception):
        self.log_error(
            "".join(traceback.format_exception(None, e, e.__traceback__))
        )

    def log(self, message: str, priority: int):
        self.app.log(message, priority)


class KoreDomain:
    def __init__(
        self, name, attach, cert, key, acme, client_verify, verify_depth
    ) -> None:
        try:
            import kore  # ignore:

            self.kore: BaseApp = kore
        except ImportError as e:
            raise

        self._domain = kore.domain(
            name=name,
            attach=attach,
            cert=cert,
            key=key,
            acme=acme,
            client_verify=client_verify,
            verify_depth=verify_depth,
        )

    def route(
        self,
        url,
        callback: Callable,
        methods: list,
        head: Optional[dict] = {},
        get: Optional[dict] = {},
        put: Optional[dict] = {},
        post: Optional[dict] = {},
        patch: Optional[dict] = {},
        delete: Optional[dict] = {},
        options: Optional[dict] = {},
        auth: Optional[dict] = {},
    ):
        """Description
        Setup a new route in the domain. The route is attached to the given url and will call the callback function when hit.

        Parameter	Description
        url	URL for this route, can contain regex and capture groups. Each capture group is passed as a separate parameter to the callback after the initial request object.
        callback	The callback to call for this route. This callback takes at least one parameter: the request object.
        Keyword	Description
        methods	A list of allowed methods. Any request to this route with an incorrect method will automatically result in a 405.
        key	The path to the private key for this domain.
        methodname	For each supported method a dictionary containing parameters for the route and how they are validated.
        auth	If set should be a dictionary containing the authentication information for the route.
        Returns
        Nothing"""
        self._domain.route(
            url,
            callback,
            methods,
            head,
            get,
            put,
            post,
            patch,
            delete,
            options,
            auth,
        )

    def filemaps(self, _map: Dict[str, str]) -> None:
        """Description
        Add filemaps to the domain.

        Parameter	Description
        maps	A dict containing the filemaps. The key is the URL part, the value is the local part on disk relative to the root of the worker process.

        Returns
            Nothing

        Example
        import kore

        class FileMap:
            def configure(self, args):
                kore.config.workers = 1
                kore.config.deployment = "dev"

                kore.server("default", ip="127.0.0.1", port="8888", tls=False)
                dom = kore.domain("*", attach="default")
                dom.filemaps({ "/": "webroot"})

        koreapp = FileMap()"""
        self._domain.filemaps(_map)
