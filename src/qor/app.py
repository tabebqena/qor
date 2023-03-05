import functools
import os
import socket
import traceback
from importlib import import_module
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    Iterable,
    Literal,
    Optional,
    Type,
    Union,
)

import click

import qor.constants as constants
from qor.config import BaseConfig
from qor.router import Route, Router
from qor.templates import JinjaAdapter
from qor.utils import get_path, import_object_from_module
from qor.wrappers import (
    Context,
    Request,
    default_handler_wrapper,
    simple_wrapper,
)

if TYPE_CHECKING:
    from qor.templates import BaseTemplateAdapter, KoreDomain


def dev_tracer(etype, value, tb):
    traceback.print_exception(etype, value, tb)


class BaseApp:
    LOG_INFO = constants.LOG_INFO  # 6
    LOG_NOTICE = constants.LOG_NOTICE  # 5
    LOG_ERR = constants.LOG_ERR  # 3
    RESULT_OK = constants.RESULT_OK  # 1
    RESULT_RETRY = constants.RESULT_RETRY  # 2
    RESULT_ERROR = constants.RESULT_ERROR  # 0
    MODULE_LOAD = constants.MODULE_LOAD  # 1
    MODULE_UNLOAD = constants.MODULE_UNLOAD  # 2
    TIMER_ONESHOT = constants.TIMER_ONESHOT  # 1
    CONN_PROTO_HTTP = constants.CONN_PROTO_HTTP  # 1
    CONN_PROTO_UNKNOWN = constants.CONN_PROTO_UNKNOWN  # 0
    CONN_PROTO_WEBSOCKET = constants.CONN_PROTO_WEBSOCKET  # 2
    CONN_STATE_ESTABLISHED = constants.CONN_STATE_ESTABLISHED  # 2

    config_keys = list(BaseConfig.kore_defaults.keys())

    def configure(self, args={}) -> None:
        """called by `kore` server to configure itself.
        Basically this method will:
        - call the `pre_configure` method.
        - check if `kore` package available or not (by importing it).
        - call the `setup` method.
        - call the `post_configure` method.
        """
        self.pre_configure()
        try:
            import kore  # ignore:

            self.kore = kore
        except ImportError as e:
            raise e
        self.setup()
        self.post_configure()
        self.ready()

    def pre_configure(self):
        """"""

    def setup(self):
        pass

    def post_configure(self):
        pass

    def ready(self):
        pass

    def kore_config(self):
        """proxy for the kore.config method, this name is to avoid conflict withh possible subclass instance `config` property"""
        return self.kore.config

    def server(
        self, name, ip: str, port: str, path: str, tls: bool = False
    ) -> None:
        """Setup a new server with the given name.

        The ip and path keywords are mutually exclusive.

        Parameter	Description
        name	The name of this listener.
        Keyword	Description
        ip	This keyword specifies the IP address to bind to.
        port	This keyword specifies the port to bind to.
        path	This keyword specifies the UNIX path to bind to.
        tls	This keyword specifies if TLS is enabled or not (True by default).
        Returns
            Nothing
        """
        try:
            self.kore.server(name, ip=ip, port=port, path=path, tls=tls)
        except RuntimeError as e:
            click.secho("Can't create server", fg="red")
            traceback.print_exc()
            click.secho("shutdown to prevent further errors, `Qor`", fg="red")
            self.kore.shutdown()

    def domain(
        self,
        host: str,
        attach: str,
        key: str = None,
        cert: str = None,
        acme: bool = None,
        client_verify: str = None,
        verify_depth: int = 1,
    ):
        """Setup a new domain for host attached to the given server.

        Parameter	Description
        host	The hostname of this domain (eg: kore.io).
        The cert and key keywords should not be specified if acme is True.

        attach	Attach this domain to the given server name.
        cert	The path to the certificate for this domain.
        key	The path to the private key for this domain.
        acme	If true will use the configured ACME provider (let's encrypt by default) to automatically obtain an X509 for this domain.
        client_verify	If present points to a PEM file containing a Certificate Authority for which the client should present a certificate for.
        verify_depth	Maximum depth for the certificate chain.
        Returns
        A domain handle on which you can install routes.

        Example
        dom = kore.domain("kore.io", attach="server", acme=True)
        dom.route("/", self.index, methods=["get"])"""
        return self.kore.domain(
            host,
            attach=attach,
            cert=cert,
            key=key,
            acme=acme,
            client_verify=client_verify,
            verify_depth=verify_depth,
        )

    def log(self, text: str, priority: Optional[Literal[6, 5, 6]] = 6):
        # default priority is 6= INFO
        self.kore.log(priority, text)

    def timer(self, callback, after: int, flags: Literal[0, 1]):
        # after in milliseconds
        # flags 0 means run in interval,
        # flag 1 means run oneshot
        self.kore.timer(callback, after, flags)

    def fatal(self, reason: str):
        # Terminates the worker process with the given reason as the error message.
        self.kore.fatal(reason)

    def tracer(self, callback: callable):
        """Sets the callback Kore will call for any uncaught exceptions.

        The callback will get 3 parameters:

        The exception type
        The exception value
        The traceback"""
        self.kore.tracer(callback)

    def proc(self, comm):
        # Spawns a new process with the given command and optional timeout in milliseconds.
        raise (NotImplementedError)

    def task_create(self, callback: Callable) -> int:
        # in our implementation, callback takes no arguments
        return self.kore.task_create(callback)

    def task_kill(self, id: int):
        self.kore.task_kill(id)

    async def gather(self, *coroutines):
        """
        Awaits all given coroutines and returns their result in a list.

        If a coroutine throws an exception that exception is returned as the result for that coroutine.
        """
        # in our implementation, each couroutine method takes no argument
        return await self.kore.gather(*coroutines)

    async def suspend(self, milliseconds: int):
        """Suspends the current coroutine for the specified amount of milliseconds."""
        return await self.kore.suspend(milliseconds)

    def websocket_broadcast(self, c, op, data):
        """Broadcasts a websocket message to all other connected websocket clients.

        Parameter	Description
        src	The source kore.connection object.
        op	The websocket op type.
        data	The data to be broadcasted.
        scope	Whether or not this is broadcasted to all workers or just this one.
        """
        self.kore.websocket_broadcast(
            c, op, data, self.kore.WEBSOCKET_BROADCAST_GLOBAL
        )

    def worker(self) -> int:
        """Returns the worker ID the code is currently running under."""
        return self.kore.worker()

    def set_progname(self, name: str):
        """Sets the kore_progname variable which is used when constructing proctitle."""
        self.kore.setname(name)

    def set_coroname(self, name: str):
        """Sets the current coroutine its friendly name. This name is used when coroutine tracing is enabled in its output."""
        self.kore.coroname(name)

    def set_corotrace(self, enabled: bool):
        """Enables or disable coroutine tracing.

        If enabled the application will print out all coroutines their suspend / resume activities and where in the Python code this is happening.
        """
        self.kore.corotrace(enabled)

    def privsep(
        self, name: str, root: str = "/var/chroot/kore", runas: str = "_kore"
    ):
        """Configuration privilege separation for Kore processes.

        This allows you to set the root directory of each process and what user it will run as.
        """
        self.kore.privsep(name, root, runas)

    def socket_wrap(self, sock: socket.socket):
        return self.kore.wrap(sock)


class Qor(BaseApp):
    handler_wrapper = default_handler_wrapper
    # designates whether the app is the root app that called by `kore` or it is middleware.
    _root_app = False
    # The context class, its instances will be the first parameter of all routes and callbacks
    context_class = Context
    # THe request class, It is used to wrap the kore requests.
    request_class = Request
    default_template_paths = ["templates"]

    def __init__(
        self,
        name="",
        import_name=None,
        config: dict = {},
        router: Union[Router, str] = None,
        template_adapter=None,
        template_adapter_class=None,
        context_processors=[],
        **kwargs,
    ) -> None:
        self.name = name
        self.import_name = import_name
        self.config = BaseConfig(**config)
        if import_name and not self.config.get("root_path", None):
            self.config["root_path"] = os.path.abspath(get_path(import_name))
        self._domains: Dict[str, "KoreDomain"] = {}
        self._default_domain = None
        if not router:
            self.router = Router(name=name)
        elif isinstance(router, str):
            try:
                router = import_object_from_module(router)
            except ImportError as e:
                raise Exception(f"Can't import router from {router}") from e
            except AttributeError as e:
                raise Exception(f"Can't import router from {router}") from e
            except:
                raise

        elif isinstance(router, Router):
            self.router: Router = router
        else:
            raise Exception(
                "The provided router is wrong type, accepted types are: str,"
                f" <qor.Router>, You set {type(router)}"
            )

        self._auths = {}
        self._post_configure_callbacks = []
        self._pre_configure_callbacks = []
        self._before_handler_callbacks = []
        self._after_handler_callbacks = []
        self._app_ready_callbacks = []
        self._error_handlers = []
        self._setup_finished = False
        self._template_adapter: Optional[BaseTemplateAdapter] = template_adapter
        self._template_adapter_class: Optional[Type] = (
            template_adapter_class or JinjaAdapter
        )

        self.callbacks_map = {
            "pre_config": self._pre_configure_callbacks,
            "post_config": self._post_configure_callbacks,
            "app_ready": self._app_ready_callbacks,
            "before_handler": self._before_handler_callbacks,
            "after_handler": self._after_handler_callbacks,
            "error_handler": self._error_handlers,
        }

        self._context_processors = context_processors
        self._extra_kwargs = kwargs

    def configure(self, args) -> None:
        """called by `kore` server to configure itself.

        Basically this method will check if `kore` package available or not.
        If `kore` is available, the `init_app` will be called. So, put all of your configurations in that method.
        """
        super().configure(args)
        self._root_app = True
        if "print-routes-exit" in args:
            # if not self._setup_finished:
            #     self.start()
            print("\n")
            for route in self.router.routes:
                print(route.name, route.handler, route.raw_path, route.methods)
            print("\n")
            self.kore.shutdown()

    def _pre_configure(self):
        for cb in self._pre_configure_callbacks:
            cb(self)

    def setup(self):
        """First call of this method is invoked by `configure` which should be called by the `kore` server.
        This method will:
        - configure  the `kore` server by the `config` instnce variable.
        - register the servers defined in the `configs`.
        - register the domains defined in the `configs`.
        - register the routes defined in the `routes`.
        extend it to add more functionalities.
        """
        if self.config.is_development:
            self._apply_dev_patches()
        for key, value in self.config.items():
            if key in self.config_keys:
                setattr(self.kore.config, key, value)

        for server_name, server_data in self.config.get("servers", {}).items():
            self.server(server_name, **server_data)
            click.secho(
                (
                    f"{server_name} {server_data.get('ip')}:{server_data.get('port')}"
                ),
                fg="blue",
            )
        for domain_name, domain_data in self.config.get("domains", {}).items():
            domain = self.domain(domain_name, **domain_data)
            self._domains[domain_name] = domain

        default_domain_name = self.config.get("default_domain_name", None)

        if default_domain_name:
            self._default_domain = self._domains.get(default_domain_name)
        else:
            self._default_domain = list(self._domains.values())[0]

    def post_configure(self):
        for cb in self._post_configure_callbacks:
            cb(self)

        return super().post_configure()

    def ready(self):
        for cb in self._app_ready_callbacks:
            cb(self)

        super().ready()
        click.secho("qor ready ...", fg="blue")

    def _setup_method(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if self._setup_finished:
                raise Exception(
                    f"can't call method {func} after finishing the application"
                    " setup."
                )
            return func(self, *args, **kwargs)

        return wrapper

    @_setup_method
    def _apply_dev_patches(self):
        self.tracer(dev_tracer)
        if not self.config.get("servers", {}) and not self.config.get(
            "domains", {}
        ):
            server_name = self.config.get("default_server_name", "default")
            ip = self.config.get("default_server_ip", "127.0.0.1")
            port = self.config.get("default_server_port", "8888")
            tls = self.config.get("default_server_tls", False)
            self.config.add_server(server_name, ip, port, tls)
            click.secho(
                (
                    f"Development Server: {server_name} {ip}:{port} added!,"
                    " make sure you add your own in production"
                ),
                fg="blue",
            )

            doamin_name = self.config.get("default_domain_name") or "*"
            self.config.add_domain(doamin_name, server=server_name)
            click.secho(
                (
                    f"Development Domain: {doamin_name} added!, make sure you"
                    " add your own in production"
                ),
                fg="blue",
            )
        if not self.config.get("disable_auto_run", False):
            self.callback(
                "app_ready",
            )(self.start)

    @_setup_method
    def auth(
        self,
        name: str,
        type: Literal["header", "cookie"],
        value: str,
        redirect_url: str = None,
    ):
        """register function as auth route using the provided name

        Args:
            name (str): The auth name
            type (Literal[&quot;header&quot;, &quot;cookie&quot;]): auth type, headers or cookie
            value (str): The name of the header or the cookie to search for the auth data
            redirect_url (str, optional): The url to redirect to if unauthenticated. Defaults to "/".
        """

        def decorator(func):
            if redirect_url:
                auth = {
                    "type": type,
                    "value": value,
                    "redirect": redirect_url,
                    "verify": simple_wrapper(func, self),
                }
            else:
                auth = {
                    "type": type,
                    "value": value,
                    "verify": simple_wrapper(func, self),
                }

            self._auths[name] = auth

            return func

        return decorator

    @_setup_method
    def header_auth(self, name, value, redirect_url: Optional[str] = None):
        return self.auth(name, "header", value=value, redirect_url=redirect_url)

    @_setup_method
    def cookie_auth(self, name, value, redirect_url: str = None):
        return self.auth(name, "cookie", value=value, redirect_url=redirect_url)

    def start(self, *args):
        self._before_handler_callbacks = tuple(self._before_handler_callbacks)
        self._after_handler_callbacks = tuple(
            reversed(self._after_handler_callbacks)
        )
        self._register_routes()

    def make_context(self, qor_request: "Request", *args, **kwargs):
        return Context(self, qor_request, *args, **kwargs)

    def wrap_request(self, kore_request, *args, **kwargs):
        return self.request_class(kore_request, self, *args, **kwargs)

    def _register_routes(self):
        """
        register the app `_routes` to theier domain or the default domain.

        N.B:.
        Domain selction:
        - if the route has a `domain` key, it will be registered to the corresponding domain.
        - else the default domain will be used.
        - else, raise error.
        """
        if self._setup_finished:
            raise Exception("routes already registered!")

        _default_domain = self._default_domain
        self.router.build_routes()
        _routes = self.router.routes

        for route in _routes:
            route_domain_name = route.get("domain", None)
            if route_domain_name:
                route_domain = self._domains.get(route_domain_name, None)
                if not route_domain:
                    raise Exception(
                        f"No domain found with name {route_domain_name} for"
                        f" route {route}"
                    )
                del route["domain"]
                self.__register_route(route_domain, route)
            else:
                if not _default_domain:
                    raise Exception(
                        f"No domain could be detected for the route {route}.\n-"
                        " The route doesn't specify one \n- And, the default"
                        " domain is None."
                    )
                self.__register_route(_default_domain, route)
        self._setup_finished = True

    def __register_route(self, domain, route: Route):
        """
        register single route to domain handle.

        parameters:
        - domain : thae domain handle that returned from `kore.domain` method. all domains are stored in `self.domain`
        - route is a dict of route data.
        for more info about the route data:
        # https://docs.kore.io/4.2.0/api/python.html#domainroute
        for your convinence, you can use `kore_lib.router.Route`
        """
        path = route.get("path")
        handler = self.handler_wrapper(route.get("handler"), self, route=route)

        params = {}
        if "params" in route:
            params = route.pop("params")
        methods = route.methods  # methods is proprty not key

        auth = {}

        if route.has_auth:
            auth_name = route.get("auth_name")

            auth = self._auths.get(auth_name)
            if not auth:
                auth = route.auth
        for method in methods:
            kwargs = {}
            key = route.get("key")
            if key:
                kwargs["key"] = key
            if params:
                kwargs[method] = params
            if auth:
                kwargs["auth"] = auth
            domain.route(path, handler, methods=[method], **kwargs)

    @_setup_method
    def add_route(
        self,
        path: str,
        handler=Callable,
        name="",
        methods=["get"],
        params={},
        auth_name=None,
        key: str = None,
        domain: str = None,
        **kwargs,
    ):
        return self.router.add_route(
            path=path,
            handler=handler,
            name=name,
            methods=methods,
            params=params,
            auth_name=auth_name,
            key=key,
            domain=domain,
            **kwargs,
        )

    @_setup_method
    def route(
        self,
        path: str,
        methods: Iterable[str] = ["get"],
        name=None,
        key=None,
        params={},
        auth_name=None,
        domain=None,
        **kwargs,
    ):
        return self.router.route(
            path=path,
            methods=methods,
            name=name,
            key=key,
            params=params,
            auth_name=auth_name,
            domain=domain,
            **kwargs,
        )

    def get(
        self,
        path: str,
        name="",
        key=None,
        params={},
        auth_name=None,
        domain=None,
        **kwargs,
    ):
        return self.router.get(
            path=path,
            name=name,
            key=key,
            params=params,
            auth_name=auth_name,
            domain=domain,
            **kwargs,
        )

    def post(
        self,
        path: str,
        name="",
        key=None,
        params={},
        auth_name=None,
        domain=None,
        **kwargs,
    ):
        return self.router.post(
            path=path,
            name=name,
            key=key,
            params=params,
            auth_name=auth_name,
            domain=domain,
            **kwargs,
        )

    def put(
        self,
        path: str,
        name="",
        key=None,
        params={},
        auth_name=None,
        domain=None,
        **kwargs,
    ):
        return self.router.put(
            path=path,
            name=name,
            key=key,
            params=params,
            auth_name=auth_name,
            domain=domain,
            **kwargs,
        )

    def patch(
        self,
        path: str,
        name="",
        key=None,
        params={},
        auth_name=None,
        domain=None,
        **kwargs,
    ):
        return self.router.patch(
            path=path,
            name=name,
            key=key,
            params=params,
            auth_name=auth_name,
            domain=domain,
            **kwargs,
        )

    def delete(
        self,
        path: str,
        name="",
        key=None,
        params={},
        auth_name=None,
        domain=None,
        **kwargs,
    ):
        return self.router.delete(
            path=path,
            name=name,
            key=key,
            params=params,
            auth_name=auth_name,
            domain=domain,
            **kwargs,
        )

    def mount_router(self, path: str, router: Router):
        return self.router.mount_router(path=path, router=router)

    def callback(self, type: str, **kwargs):
        """a decorator to register callback.

        Args:
            type (str): The callback type. it should be a key in `qor.callbacks_map`.
        """

        def wrapper(func):
            callbacks = self.callbacks_map.get(type, None)
            if callbacks is None:
                raise Exception(
                    f"No callback list for this type: {type}, avaialable:"
                    f" {', '.join(self.callbacks_map.keys())}"
                )
            if kwargs:
                callbacks.append({"func": func, "kwargs": kwargs})
            else:
                callbacks.append(func)
            return func

        return wrapper

    def before_handler(self, func):
        self.callback("before_handler")(func)
        return func

    def after_handler(self):
        def wrapper(func):
            self.callback("after_handler")(func)
            return func

        return wrapper

    def error_handler(self, error):
        def wrapper(func):
            self.callback("error_handler")(func, error=error)
            return func

        return wrapper

    def on_ready(self):
        def wrapper(func):
            self.callback("app_ready")(func)
            return func

        return wrapper

    def context_processor(self, func):
        def wrapper(func):
            self._context_processors.append(func)
            return func

        return wrapper

    @property
    def template_adapter(self) -> "BaseTemplateAdapter":
        if self._template_adapter:
            return self._template_adapter
        self._template_adapter = self._template_adapter_class(self)
        return self._template_adapter

    def _render_template(self, template_name, *args, **kwargs):
        for pro in self._context_processors:
            kwargs.update(pro())
        return self.template_adapter.render(template_name, *args, **kwargs)

    def reverse(self, name: str, **kwargs) -> Optional[str]:
        """return the url for route name using the provided kwargs

        Args:
            name (str): The route name

        Returns:
            _type_: The built url or `None`
        """
        return self.router.reverse(name, **kwargs)
