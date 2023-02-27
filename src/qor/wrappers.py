import functools
import socket
import traceback
from inspect import isclass
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
)

import qor.constants as constants
from qor.config import BaseConfig
from qor.router import Route, Router
from qor.utils import parse_return_value

if TYPE_CHECKING:
    from qor.app import BaseApp, Qor
    from qor.templates import BaseTemplateAdapter


class default_handler_wrapper:
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

    def __init__(self, func, app, **kwargs) -> None:
        self.func = func
        self.app: "Qor" = app
        self.kwargs = kwargs

    def __run_before_request(self, context, app, *args, **kwargs):
        before_request_callbacks = app._before_request_callbacks
        for cb in before_request_callbacks:
            rv = cb(context, *args, **kwargs)
            if rv is not None:
                return rv

    def __run_after_request(self, context: "Context", app, *args, **kwargs):
        after_request_callbacks = app._after_request_callbacks
        for cb in after_request_callbacks:
            context.return_value = cb(context, *args, **kwargs)

    def __run_error_callbacks(
        self,
        context: "Context",
        app: "Qor",
        status_or_exc: Union[int, Exception],
        *args,
        **kwargs,
    ):
        _error_handlers = app._error_handlers
        is_int = isinstance(status_or_exc, int)
        is_exc = isinstance(status_or_exc, Exception)

        if is_int:
            for _status_or_exc, cb in _error_handlers:
                if isinstance(_status_or_exc, int) and _status_or_exc == status_or_exc:
                    error_cb_rv = cb(context, *args, **kwargs)
                    if error_cb_rv is not None:
                        context.return_value = error_cb_rv
                        return
        elif is_exc:
            for _status_or_exc, cb in _error_handlers:
                if isclass(_status_or_exc) and issubclass(
                    status_or_exc, _status_or_exc
                ):
                    error_cb_rv = cb(context, *args, **kwargs)
                    if error_cb_rv is not None:
                        context.return_value = error_cb_rv
                        return

    def send_response(self, context: "Context", *args, **kwargs):
        status, data = parse_return_value(context.return_value)
        context.request.response(status, data)

    def __call__(self, request, *args: Any, **kwargs: Any) -> Any:
        app = self.app

        context = app.make_context(request, app.request_class)
        try:
            rv = self.__run_before_request(context, app, *args, **kwargs)
            if rv is not None:
                context.return_value = rv
                self.__run_after_request(context, app, *args, **kwargs)
                self.send_response(context, *args, **kwargs)
                return

            # call the handler function
            rv = self.func(context, *args, **kwargs)
            # quick update context by the rv
            context.return_value = rv
            # try to parse the return value
            status, data = parse_return_value(rv)
            # update context
            context.response_status = status
            context.response_data = data

            if status == 200:
                # run th eafter_request callbacks if there is no error
                self.__run_after_request(context, *args, **kwargs)
                self.send_response(context, *args, **kwargs)
                return

            else:
                self.__run_error_callbacks(context, app, status, *args, **kwargs)
                self.send_response(context, *args, **kwargs)
                return

        except Exception as e:
            self.__run_error_callbacks(context, app, e, *args, **kwargs)
            if context.return_value:
                self.send_response(context, *args, **kwargs)

            else:
                raise


class simple_wrapper:
    def __init__(self, func, app, **kwargs) -> None:
        self.func = func
        self.app: "Qor" = app
        self.kwargs = kwargs

    def __call__(self, _request, *args: Any, **kwds: Any) -> Any:
        request = Request(_request, self.app)
        return self.func(request, *args, **kwds)

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


class Request:
    HTTP_METHOD_GET = constants.HTTP_METHOD_GET  # 1
    HTTP_METHOD_PUT = constants.HTTP_METHOD_PUT  # 4
    HTTP_METHOD_HEAD = constants.HTTP_METHOD_HEAD  # 32
    HTTP_METHOD_POST = constants.HTTP_METHOD_POST  # 2
    HTTP_METHOD_DELETE = constants.HTTP_METHOD_DELETE  # 16
    HTTP_METHOD_OPTIONS = constants.HTTP_METHOD_OPTIONS  # 64
    HTTP_METHOD_PATCH = constants.HTTP_METHOD_PATCH  # 128

    def __init__(self, kore_request, app: "Qor") -> None:
        self.request = kore_request
        self.app = app

    @property
    def method(self) -> str:
        return constants.METHOD_CODES[self.request.method]

    @property
    def host(self) -> str:
        """The domain as a unicode string."""
        return self.request.host

    @property
    def agent(self) -> str:
        """The user agent as a unicode string."""
        return self.request.agent

    @property
    def path(self) -> str:
        """The requested path as a unicode string."""
        return self.request.path

    @property
    def body(self) -> bytes:  # PyBuffer
        """The entire incoming HTTP body as a PyBuffer."""
        return self.request.body

    @property
    def headers(self) -> dict:
        """the request headers as dictionary"""
        return self.request.headers

    @property
    def _method_int(self) -> int:
        """The requested method as a PyLong. (kore.HTTP_METHOD_GET, etc)."""
        return self.request.method

    @property
    def body_path(self) -> str:
        """The path to the HTTP body on disk (if enabled)."""
        return self.request.body_path

    @property
    def connection(self) -> "Connection":
        """The underlying client connection as a kore.connection object."""
        return self.request.connection

    @property
    def client_Address(self) -> str:
        return self.connection.addr

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
        self.request.populate_post()

    def populate_multipart(self) -> None:
        """Synopsis
        req.populate_multipart()
        Description
        Instructs Kore to go ahead and parse the incoming body as content-type multipart/form-data and validate parameters according to the configured params {} blocks in the configuration.

        Returns
        Nothing"""
        self.request.populate_multipart()

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
        return self.request.response_header(name)

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
        self.request.response_header(name, value)

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


class Context:
    def __init__(self, app: "Qor", request: "Request") -> None:
        self.app = app
        self.request = request
        self.g = {}
        self.response_status = None
        self.response_data = None
        self.return_value = None
