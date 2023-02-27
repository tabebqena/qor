import sys
import time
from io import BufferedReader, BytesIO, StringIO
from socketserver import BaseServer
from typing import Any, Callable, List, Optional, Tuple, Union
from wsgiref.handlers import SimpleHandler
from wsgiref.headers import Headers
from wsgiref.simple_server import ServerHandler
from wsgiref.simple_server import WSGIRequestHandler as _WSGIRequestHandler
from wsgiref.simple_server import WSGIServer

from qor.utils import int_to_method_name

__version__ = "1.0.0"

# class KoreRequestHeaders(Headers):
#     def __init__(self, kore_request) -> None:
#         self.kore_request = kore_request
#         super().__init__(headers=[])  # Till I know how to enumerate the headers

#     def __getitem__(self, name: str):
#         return self.get(name)

#     def get(self, name, default=""):
#         return self.kore_request.request_header(name) or default


class KoreWSGIInput(BufferedReader):
    def __init__(self, request, buffer_size=1024) -> None:
        self.request = request
        self.read_length = 0
        self.buffer_size = buffer_size
        self._closed = False
        self._buffered_bytes = b""

    def __read(self, __size: int = 1024) -> Tuple[int, bytes]:
        length, val = self.request.body_read(__size)
        self.read_length += length
        if length == 0:
            self._closed = True
        return length, val

    # def _read(self, __size) -> Tuple[int, bytes]:
    #     buf_length = len(self._buffered_bytes)
    #     if buf_length > 0:
    #         if buf_length < __size:
    #             val = self._buffered_bytes  # got all, as it is smaller already
    #             self._buffered_bytes = b""
    #             remain = __size - buf_length
    #             from_rquest = self.__read(remain)
    #             return from_rquest[0] + buf_length, val + from_rquest[1]

    #         elif buf_length == __size:
    #             val = self._buffered_bytes  # got all, as they are eqals
    #             self._buffered_bytes = b""
    #             return __size, val
    #         else:
    #             val = self._buffered_bytes[:__size]
    #             self._buffered_bytes = self._buffered_bytes[__size:]
    #             return __size, val

    #     else:
    #         return self.__read(__size)

    def read(self, __size: int = 1024) -> bytes:
        return self.__read(__size)[1]

    def read1(self, __size: int = -1) -> bytes:
        return self.read(__size)

    def peek(self, __size: int = ...) -> bytes:
        raise NotImplementedError()

    def mode(self) -> str:
        return "rb"

    @property
    def name(self) -> str:
        pass

    def close(self) -> None:
        pass

    @property
    def closed(self) -> bool:
        return self._closed

    def fileno(self) -> int:
        pass

    def flush(self) -> None:
        pass

    def isatty(self) -> bool:
        pass

    def readable(self) -> bool:
        return True

    def readline(self, limit: int = -1):
        raise NotImplementedError()

    def readlines(self, hint: int = -1) -> List:
        raise NotImplementedError()

    def seek(self, offset: int, whence: int = 0) -> int:
        raise Exception("not seekable")

    def seekable(self) -> bool:
        return False

    def tell(self) -> int:
        return self.read_length

    def truncate(self, size: int = None) -> int:
        # donothing
        pass

    def writable(self) -> bool:
        return False

    def write(self, s) -> int:
        raise Exception("wsgi.input is not writable")

    def writelines(self, lines: List) -> None:
        raise Exception("wsgi.input is not writable")


class StandAloneWSGIHandler(ServerHandler):
    default_request_version = "HTTP/0.9"
    error_message = "Internal Server Error"
    server_name = ""  # fully qualified domain name
    server_port = ""  # port number as string

    # from WsgiRequestHandler
    server_version = "WSGIServer/" + __version__
    default_request_version = "HTTP/0.9"

    status = "500 Internal Server Error"
    status_integer = 500
    origin_server = False  # # We are NOT transmitting direct to client
    headers_class = Headers  # response headers
    # request_headers_class = KoreRequestHeaders

    def __init__(
        self,
        stdin,
        stdout,
        stderr,
        environ,
        multithread=True,
        multiprocess=True,
        kore_request=None,
    ) -> None:
        super().__init__(stdin, stdout, stderr, environ, multithread, multiprocess)
        self.kore_request = kore_request
        self.setup_server_environ()
        self.setup_handler_environ()
        self.setup_environ()
        self.request_version = self.default_request_version

    def get_client_address(self):
        return (self.kore_request.connection.addr or "", "")

    def set_kore_request(self, kore_request):
        self.kore_request = kore_request

    def setup_server_environ(self):
        # Set up base environment
        env = self.base_environ = {}
        env["SERVER_NAME"] = self.server_name
        env["GATEWAY_INTERFACE"] = "CGI/1.1"
        env["SERVER_PORT"] = str(self.server_port)
        env["REMOTE_HOST"] = ""
        env["CONTENT_LENGTH"] = ""
        env["SCRIPT_NAME"] = ""

    def setup_handler_environ(self):
        host = self.kore_request.host
        agent = self.kore_request.agent
        path = self.kore_request.path
        method = self.kore_request.method
        self.request_version = "HTTP/1.1"  # get it from the request
        self.path = path
        self.command = int_to_method_name(method).upper()
        self.requestline = f"[{host}] [{agent}] [{self.command}] {host}{self.path}"

    def run(self, application):
        try:
            self.setup_server_environ()
            self.setup_handler_environ()
            self.setup_environ()
            self.client_Address = self.get_client_address()
            self.result = application(self.environ, self.start_response)
            self.finish_response()
            self.send_to_kore()
            self.real_close()
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError) as e:
            # We expect the client to close the connection abruptly from time
            # to time.
            # TODO: send something to kore
            raise (e)
        except Exception as e:
            try:
                self.handle_error()
                self.send_to_kore()
                self.real_close()
            except:
                # If we get an error handling an error, just give up already!
                self.real_close()
                raise (e)  # ...and let the actual server figure it out.

    def start_response(
        self,
        status: str,
        headers: List[Tuple[str, str]],
        exc_info=None,
    ) -> Callable[[bytes], None]:
        super().start_response(status, headers, exc_info)
        if self.status:
            splitted = self.status.split(" ")
            if len(splitted) > 0:
                self.status_integer = int(splitted[0])
        return self.write

    def _write(self, data: bytes) -> None:
        # invoked by self.write
        result = self.stdout.write(data)
        if result is None or result == len(data):
            return

        from warnings import warn

        warn(
            "SimpleHandler.stdout.write() should not do partial writes",
            DeprecationWarning,
        )
        while True:
            data = data[result:]
            if not data:
                break
            result = self.stdout.write(data)

    def _flush(self) -> None:
        pass

    def finish_content(self) -> None:
        # return super().finish_content()
        # In WSGI, it will send Content-Length header
        # Here we will do nothing
        pass

    def close(self) -> None:
        pass

    def real_close(self):
        # Because the super method calls the request handler which is None in our use case
        try:
            self.log_request(self.status.split(" ", 1)[0], self.bytes_sent)
        finally:
            SimpleHandler.close(self)

    def send_to_kore(self):
        self.stdout.seek(0)
        rv = self.stdout.getvalue()
        self.kore_request.response(self.status_integer, rv)
        self.stdout.truncate(0)
        self._flush = self.stdout.flush

    def handle_error(self) -> None:
        # return super().handle_error()
        """Log current error, and send error output to client if possible"""
        self.log_exception(sys.exc_info())
        if not self.headers_sent:
            self.result = self.error_output(self.environ, self.start_response)
            self.finish_response()
        # XXX else: attempt advanced recovery techniques for HTML or text?

    def send_headers(self) -> None:
        """
        Alter this,
        Transmit headers to the client, via self._write()"""
        self.cleanup_headers()
        self.headers_sent = True
        for header_name, header_value in self.headers.items():
            self.kore_request.response_header(header_name, header_value)

    def cleanup_headers(self) -> None:
        """
        Don't create conten-length header, kore will do
        """
        pass

    def log_request(self, code="-", size="-"):
        """Log an accepted request.

        This is called by send_response().

        """
        self.log_message('"%s" %s %s', self.requestline, str(code), str(size))

    def log_error(self, format, *args):
        """Log an error.

        This is called when a request cannot be fulfilled.  By
        default it passes the message on to log_message().

        Arguments are the same as for log_message().

        XXX This should go to the separate error log.

        """

        self.log_message(format, *args)

    def log_message(self, format, *args):
        sys.stderr.write(
            "%s - - [%s] %s\n"
            % (self.address_string(), self.log_date_time_string(), format % args)
        )

    def address_string(self):
        return "ADDRESS STRING"

    weekdayname = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    monthname = [
        None,
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    def log_date_time_string(self):
        """Return the current time formatted for logging."""
        now = time.time()
        year, month, day, hh, mm, ss, x, y, z = time.localtime(now)
        s = "%02d/%3s/%04d %02d:%02d:%02d" % (
            day,
            self.monthname[month],
            year,
            hh,
            mm,
            ss,
        )
        return s


class KoreServerHandler(ServerHandler):
    status = "500 Internal Server Error"
    status_integer = 500
    origin_server = False  # # We are NOT transmitting direct to client
    headers_class = Headers  # response headers

    def __init__(
        self,
        stdin=None,
        stdout=None,
        stderr=None,
        environ={},
        multithread: bool = True,
        multiprocess: bool = False,
    ) -> None:
        super().__init__(
            stdin,
            stdout,
            stderr,
            environ,
            multithread,
            multiprocess,
        )

    def set_kore_request(self, kore_request):
        self.kore_request = kore_request

    def run(self, application):
        """Invoke the application"""
        # Note to self: don't move the close()!  Asynchronous servers shouldn't
        # call close() from finish_response(), so if you close() anywhere but
        # the double-error branch here, you'll break asynchronous servers by
        # prematurely closing.  Async servers must return from 'run()' without
        # closing if there might still be output to iterate over.
        try:
            self.setup_environ()
            self.result = application(self.environ, self.start_response)
            #  TODO finsih resonse is alse writing data
            self.finish_response()
            # her only we can send to kore
            self.send_to_kore()
            # We didn't finish before
            self.close()

        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError) as e:
            # We expect the client to close the connection abruptly from time
            # to time.
            # TODO: send something to kore
            raise (e)
        except Exception as e:
            try:
                self.handle_error()
                self.send_to_kore()
                self.close()
            except:
                # If we get an error handling an error, just give up already!
                self.close()
                raise (e)  # ...and let the actual server figure it out.

    def send_to_kore(self):
        self.stdout.seek(0)
        rv = self.stdout.getvalue()
        self.kore_request.response(self.status_integer, rv)
        self.stdout.truncate(0)
        self._flush = self.stdout.flush

    def start_response(
        self,
        status: str,
        headers: List[Tuple[str, str]],
        exc_info=None,
    ) -> Callable[[bytes], None]:
        super().start_response(status, headers, exc_info)
        if self.status:
            splitted = self.status.split(" ")
            if len(splitted) > 0:
                self.status_integer = int(splitted[0])
        return self.write

    def finish_response(self) -> None:
        """
        Alter this behavior : Send any iterable data, then close self and the iterable
        TO: send data, close object, but don't call close

        Subclasses intended for use in asynchronous servers will
        want to redefine this method, such that it sets up callbacks
        in the event loop to iterate over the data, and to call
        'self.close()' once the response is finished.
        """
        try:
            if not self.result_is_file() or not self.sendfile():
                for data in self.result:
                    # call write here
                    self.write(data)
                self.finish_content()
        except Exception as e:
            # Call close() on the iterable returned by the WSGI application
            # in case of an exception.
            if hasattr(self.result, "close"):
                self.result.close()
            raise
        else:
            # We only call close() when no exception is raised, because it
            # will set status, result, headers, and environ fields to None.
            # See bpo-29183 for more details.
            # self.close()
            pass

    def write(self, data: bytes) -> None:
        # wuper() will make assertions & set headers then call _write, _flush
        return super().write(data)

    def finish_content(self) -> None:
        # return super().finish_content()
        # In WSGI, it will send Content-Length header
        # Do nothing
        pass

    def _write(self, data: bytes) -> None:
        result = self.stdout.write(data)
        if result is None or result == len(data):
            return

        from warnings import warn

        warn(
            "SimpleHandler.stdout.write() should not do partial writes",
            DeprecationWarning,
        )
        while True:
            data = data[result:]
            if not data:
                break
            result = self.stdout.write(data)

    def _flush(self) -> None:
        # print("_flush")
        pass

    def send_headers(self) -> None:
        """
        Alter this,
        Transmit headers to the client, via self._write()"""
        self.cleanup_headers()
        self.headers_sent = True
        for header_name, header_value in self.headers.items():
            self.kore_request.response_header(header_name, header_value)

    def cleanup_headers(self) -> None:
        """
        Don't create conten-length header, kore will do
        """
        pass

    def close(self) -> None:
        super().close()

    def handle_error(self) -> None:
        # return super().handle_error()
        """Log current error, and send error output to client if possible"""
        self.log_exception(sys.exc_info())
        if not self.headers_sent:
            self.result = self.error_output(self.environ, self.start_response)
            self.finish_response()
        # XXX else: attempt advanced recovery techniques for HTML or text?


class KoreWSGIRequestHandler(_WSGIRequestHandler):
    """ """

    server_version = "WSGIServer/" + __version__

    default_request_version = "HTTP/0.9"

    def __init__(self, kore_request, client_address, server: BaseServer) -> None:
        self.headers = kore_request.headers()
        self.stderr = StringIO()
        super().__init__(kore_request, client_address, server)

    def setup(self) -> None:
        self.request_version = self.default_request_version

    def get_environ(self):  # -> "WSGIEnvironment":
        # Set up base environment
        return super().get_environ()

    def get_stderr(self):
        return self.stderr

    def handle(self):
        """Handle a single HTTP request"""
        self.raw_requestline = self.request.path
        #: I think `kore` c is handling the 414 error (URI TOO Long)
        # set important instance properties & possible call self.send_error
        if not self.parse_request():  # An error code has been sent, just exit
            self.server.handle_error(self.request, self.client_address)
            return

        # stdin, stdout, stderr, environ, muthrea, multi_process
        stdout = BytesIO()
        handler = KoreServerHandler(
            KoreWSGIInput(self.request),  # self.rfile,
            stdout=stdout,  # self.wfile,
            stderr=self.get_stderr(),
            environ=self.get_environ(),
            multithread=False,
            multiprocess=False,
        )
        handler.set_kore_request(self.request)
        handler.request_handler = self  # backpointer for logging
        handler.run(self.server.get_app())

    def address_string(self) -> str:
        return super().address_string()

    def parse_request(self):
        """Parse a request (internal).

        The request should be stored in self.raw_requestline; the results
        are in self.command, self.path, self.request_version and
        self.headers.

        Return True for success, False for failure; on failure, any relevant
        error response has already been sent back.

        """

        self.command = None  # set in case of error on the first line
        self.request_version = version = self.default_request_version
        self.close_connection = True
        host = self.request.host
        agent = self.request.agent
        path = self.request.path
        body = self.request.body
        method = self.request.method
        body_path = self.request.body_path
        conn = self.request.connection
        self.request_version = "HTTP/1.1"  # get it from the request
        self.path = path
        self.command = int_to_method_name(method).upper()
        self.requestline = f"[{self.command}] {host}{self.path}"

        conntype = self.headers.get("Connection")
        if conntype.lower() == "close":
            self.close_connection = True
        elif conntype.lower() == "keep-alive" and self.protocol_version >= "HTTP/1.1":
            self.close_connection = False
        # Examine the headers and look for an Expect directive
        expect = self.headers.get("Expect")
        if (
            expect.lower() == "100-continue"
            and self.protocol_version >= "HTTP/1.1"
            and self.request_version >= "HTTP/1.1"
        ):
            if not self.handle_expect_100():
                return False
        return True

    def handle_expect_100(self) -> bool:
        raise (NotImplementedError)

    def handle_one_request(self) -> None:
        return super().handle_one_request()

    def send_response(self, code: int, message: Optional[str] = None) -> None:
        return super().send_response(code, message)

    def send_response_only(self, code: int, message: Optional[str] = None) -> None:
        """Send the response header only."""
        if self.request_version != "HTTP/0.9":
            if message is None:
                if code in self.responses:
                    message = self.responses[code][0]
                else:
                    message = ""

            if not hasattr(self, "_headers_buffer"):
                self._headers_buffer = []
            self._headers_buffer.append(
                ("%s %d %s\r\n" % (self.protocol_version, code, message)).encode(
                    "latin-1", "strict"
                )
            )

    def send_error(
        self, code: int, message: Optional[str] = None, explain: Optional[str] = None
    ) -> None:
        return super().send_error(code, message, explain)

    def send_header(self, keyword: str, value: str) -> None:
        return super().send_header(keyword, value)

    def end_headers(self) -> None:
        pass

    def flush_headers(self) -> None:
        pass

    def log_request(
        self, code: Union[int, str] = "-", size: Union[int, str] = "-"
    ) -> None:
        return super().log_request(code, size)

    def log_error(self, format: str, *args: Any) -> None:
        return super().log_error(format, *args)

    def log_date_time_string(self) -> str:
        return super().log_date_time_string()

    def log_message(self, format: str, *args: Any) -> None:
        return super().log_message(format, *args)

    def finish(self):
        pass


class KoreWSGIServer(WSGIServer):
    default_request_version = "HTTP/0.9"
    error_message = "Internal Server Error"
    server_name = ""  # fully qualified domain name
    server_port = ""  # port number as string

    def __init__(self, server_address, RequestHandlerClass) -> None:
        super().__init__(server_address, RequestHandlerClass)
        self.setup_environ()

    def set_kore_request(self, kore_request):
        self.kore_request = kore_request

    def set_server_name(self, name: str):
        """Set server domain name"""
        self.server_name = name

    def set_server_port(self, port: str):
        """Set server domain name"""
        self.server_port = port

    def serve_forever(self, poll_interval: float = ...) -> None:
        # I can't figure out how to implement this
        raise NotImplementedError()

    def service_actions(self) -> None:
        pass

    def server_bind(self) -> None:
        """Called by constructor to bind the socket.

        I can't figure out it in our use case

        """
        pass

    def server_activate(self) -> None:
        """Called by constructor to activate the server.

        May be overridden.

        """
        pass

    # The distinction between handling, getting, processing and finishing a
    # request is fairly arbitrary.  Remember:
    #
    # - handle_request() is the top-level call.  It calls selector.select(),
    #   get_request(), verify_request() and process_request()
    # - get_request() is different for stream or datagram sockets
    # - process_request() is the place that may fork a new process or create a
    #   new thread to finish the request
    # - finish_request() instantiates the request handler class; this
    #   constructor will handle the request all by itself
    def handle_request(self) -> None:
        kore_request = self.get_request()
        client_address = self.get_client_address()

        if self.verify_request(kore_request, client_address):
            try:
                self.process_request(kore_request, client_address)

            except Exception:
                self.handle_error(kore_request, client_address)
                self.shutdown_request(kore_request)
            except:
                self.shutdown_request(kore_request)
                raise
        else:
            self.shutdown_request(kore_request)

    def get_request(self) -> Tuple[Any, Any]:
        return self.kore_request

    def get_client_address(self):
        return (self.kore_request.connection.addr or "", "")

    def process_request(self, kore_request, client_address) -> None:
        """Call finish_request, then shutdown request

        Overridden by ForkingMixIn and ThreadingMixIn.

        """
        return super().process_request(kore_request, client_address)

    def finish_request(self, kore_request, client_address):
        """Finish one request by instantiating RequestHandlerClass."""
        self.RequestHandlerClass(kore_request, client_address, self)

    def handle_error(self, request, client_address) -> None:
        """Handle an error gracefully.  May be overridden.

        The default is to print a traceback and continue.
        But we alse send 500 response to `kore`

        """
        self.kore_request.response(500, self.error_message)
        super().handle_error(request, client_address)

    def close_request(self, request) -> None:
        """Called to clean up an individual request."""
        pass

    def shutdown_request(self, request) -> None:
        print(" kore wsgi server shutdown request ")

    def verify_request(self, request, client_address) -> bool:
        """Verify the request.  May be overridden.

        Return True if we should proceed with this request.

        """
        return True

    def shutdown(self) -> None:
        # I can't figure out it
        pass

    def handle_timeout(self) -> None:
        """
        NB:. It has no role in kore implementation.
        Called if no new request arrives within self.timeout.

        Overridden by ForkingMixIn.
        """
        pass

    def server_close(self) -> None:
        """Called to clean-up the server.

        May be overridden.

        """
        pass

    def get_app(self):
        return self.app

    def set_app(self, app):
        self.app = app
