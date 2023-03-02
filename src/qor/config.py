import os
import warnings
from importlib import import_module


class BaseConfig(dict):
    config_from_environ = False
    config_module = None
    kore_defaults = {
        # The number of worker processes to use. If not set, the number of CPU cores in the system.
        "workers": 1,
        # The maximum number of active connections a worker process holds before refusing to accept more.
        "worker_max_connections": 1,
        # The maximum number of open file descriptor per worker.
        "worker_rlimit_nofiles": 100,
        # The maximum number of new connections to accept in a single event loop.
        "worker_accept_threshold": 10,
        # The death policy for a worker, "restart" by default. If set to "terminate" will cause the Kore server to
        #  shutdown on abnormal worker termination.
        "worker_death_policy": "restart",  # "terminate"
        # Worker CPU affinity (0 or 1, default 1).
        "worker_set_affinity": 1,
        # The path to a file in which the server will write the PID for the parent process.
        "pidfile": "pidfile",
        # The number of pending connections.
        "socket_backlog": 1,
        # The TLS version to use (default: both, 1.2 for TLSv1.2 only and 1.3 for TLSv1.3 only).
        "tls_version": "1.2",
        # OpenSSL ciphersuite list to use. Defaults to a very sane list with only AEAD ciphers and ephemeral key
        #  exchanges.
        "tls_cipher": "",
        #  # Path to DH parameters for the server to use.
        "tls_dhparam": None,
        # Path to a 2048 byte file containing entropy used to seed the PRNG.
        "rand_file": "",
        # An email address used for account registration.
        # BUG: ignoring unknown setting
        # "acme_email": "",
        # A URL to the directory for an ACME provider. Defaults to Let's Encrypt.
        # BUG: ignoring unknown setting
        # "acme_provider": "",
        # OpenBSD only, pledge categories for the worker processes.
        # BUG: ignoring unknown setting
        # "pledge": False,
        # Linux only, seccomp violations will be logged and not cause the process to terminate. Either "yes" or "no".
        "seccomp_tracing": "yes",
        # # 	The default extension for files in a filemap.
        "filemap_ext": "",
        # 		The root file in a filemap. (eg index.html).
        "filemap_index": "",
        # Add a new HTTP media type (in the form of "mediatype ext1 ext2 ext").
        "http_media_type": None,
        # 	The maximum number of bytes HTTP headers can consist of. If a request comes in with headers larger than this
        #  the connection is closed.
        # Defaults to 4096 bytes.
        "http_header_max": 4096,
        # The number of seconds after which Kore will close a connection if no HTTP headers were received.
        # Defaults to 10.
        "http_header_timeout": 10,
        # 	The maximum number of bytes an HTTP body can consist of. If a request comes in with a body larger than this
        #  the connection is closed with a 413 response.
        # Defaults to 1MB.
        "http_body_max": 1024 * 1024,  # 1 MB
        # 	The number of seconds after which Kore will close a connection if no HTTP body was received in full.
        #  Defaults to 60.
        "http_body_timeout": 60,
        # 	The number in bytes from which point Kore will offload incoming HTTP bodies onto a file on disk instead of
        #  keeping it in memory. Disabled by default.
        "http_body_disk_offload": 1024 * 1024,  # 1 MB TODO optimise this
        # 	A path where the temporary body files are written if the http_body_disk_offload setting is enabled.
        "http_body_disk_path": 1,
        # Allows you to override the Kore server header.
        "http_server_version": "",
        # 	If set to "yes" will display HTML based HTTP error codes. Defaults to "no".
        "http_pretty_error": "no",
        #  # Set the logfile to which Kore will write all worker output.
        "logfile": None,
        # 	The deployment type of the application. Either "production", "development" or "docker". The production
        #  setting will cause Kore to chroot and drop privileges and run in the background. The development setting will
        #  run Kore in the foreground and only chdir into the root setting. The docker setting will cause Kore to run in
        #  the foreground but still apply priviledge sep
        "deployment": "development",
        # relative path to the python file that contains the Kore app.
        "pidfile": "./pidfile",
    }
    qor_defaults = {
        "servers": {},
        "domains": {},
        "default_server_name": "default",
        "default_server_ip": "127.0.0.1",
        "default_server_port": "8888",
        "default_server_tls": False,
        "default_domain_name": None,
        "debug": True,
        # absolute import path for the config module
        "config_module": None,
        # name for the `configure` method that is located in the `config_module`
        "config_configure": "configure",
        # name for the `config` member that is located in the `config_module`
        "config_config": "config",
        # whether configs will wun `correct_self` method or not
        "config_correct_self": True,
        # whether configs will be updated from the enviroment or not
        "config_from_environ": False,
        # keys listed in config_env_exclude_keys will't be loaded from the enviroment
        "config_env_exclude_keys": [],
        # disable auto registeration of routes, effective only in `deployment=development`
        # by default, in development mode, qor will auto register routes, this option will prevent this
        # default is `false`
        "disable_auto_run": False,
    }

    def __init__(self, **kwargs) -> None:
        """initialize configs for qor app, This is a subclass of builtin python dictionary.
        It collects configs from:
        - kore_defaults
        - qor_defaults
        - enviroment: if passed the keyword argument `config_from_environ=True`
        - config_module: an absolute python import path, that points to the config module.
        - the keywords passed to its constructor.

        N.B:. The config module should contains at least one of:
        - function named `configure` that accepts this class as first arument and return dictionary as a return value.
        - member named `config` which should be a dictionary like object.
        The names `configure` and `config` could be customized by `config_configure` and `config_config` respectively.

        Raises:
            Exception: if the config module has no `configure` nor `config` members.
            ImportError: If the passed config module can't be imported
        """
        self.update(self.kore_defaults)
        self.update(self.qor_defaults)
        config_from_environ = (
            kwargs.pop("config_from_environ", False) or self.config_from_environ
        )
        config_module = kwargs.pop("config_module", None) or self.config_module
        if config_from_environ:
            for key in self.keys():
                if key in self.get("config_env_exclude_keys", []):
                    continue
                val = os.environ.get(key)
                if val:
                    self[key] = val
        # TODO: use import configs.configure, reduce options to one
        if config_module or self.get("config_module", None):
            config_module = config_module or self.get("config_module", None)
            try:
                imported_config_module = import_module(config_module)
                configure_name = self.get("config_configure", "configure")
                configure = getattr(
                    imported_config_module, configure_name, None
                )
                config_name = self.get("config_config", "config_config")
                _config = getattr(imported_config_module, config_name, None)

                if configure:
                    self.update(configure(self))
                if _config:
                    self.update(_config)
                if not configure and not _config:
                    raise Exception(
                        f"The config module has no method named `{config_name}`"
                        f" nor member named `{config_name}`"
                    )

            except ImportError as e:
                raise ImportError(
                    f"can't import config module {config_module}"
                ) from e

        super().__init__(kwargs)

        self.absolute_paths()
        if self["config_correct_self"]:
            self.correct_self()

    @property
    def is_development(self):
        return self["deployment"] == "development"

    def absolute_paths(self):
        root_path = self.get("root_path", None)
        if self.get("root_path", None) and self.get("app_path", None):
            self["app_path"] = os.path.join(root_path, self["app_path"])
        if self.get("root_path", None) and dict.get(self, "pidfile", None):
            self["pidfile"] = os.path.join(root_path, self["pidfile"])
        if self.get("root_path", None) and dict.get(self, "logfile", None):
            self["logfile"] = os.path.join(root_path, self["logfile"])
        if self.get("root_path", None) and self.get("dev_log_dir", None):
            self["dev_log_dir"] = os.path.join(
                root_path, self.get("dev_log_dir", None)
            )
        if not self.get("http_body_disk_path") and self.get(
            "http_body_disk_offload"
        ):
            temp_path = os.path.join(self.get("root_path"), "tmp")
            self["http_body_disk_path"] = temp_path

    def correct_self(self):
        default_is_wrong = {
            "tls_dhparam": self.kore_defaults.get("tls_dhparam"),
            "http_media_type": self.kore_defaults.get("http_media_type"),
            "logfile": self.kore_defaults.get("logfile"),
        }
        for key, val in default_is_wrong.items():
            if self.get(key, None) == val:
                del self[key]

    def add_server(self, name: str, ip: str, port: str, path=None, tls=False):
        if self.get("servers", {}).get(name, {}):
            warnings.warn(
                "There is already registered server with the same name."
            )
            return
        servers = self.get("servers", {})
        servers[name] = {
            "ip": ip,
            "port": port,
            "path": path,
            "tls": tls,
        }
        self["servers"] = servers

    def add_domain(
        self,
        name: str,
        server: str = None,
        cert=None,
        key=None,
        acme=False,
        client_verify=None,
        verify_depth=1,
    ):
        if self.get("domains", {}).get(name, {}):
            warnings.warn(
                f"There is already registered domain with this name {name}"
            )
            return
        domains = self.get("domains", {})
        domains[name] = dict(
            attach=server or self.get("default_server_name"),
            cert=cert,
            key=key,
            acme=acme,
            client_verify=client_verify,
            verify_depth=verify_depth,
        )
