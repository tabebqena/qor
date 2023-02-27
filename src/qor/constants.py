HTTP_METHOD_GET = 1
HTTP_METHOD_PUT = 4
HTTP_METHOD_HEAD = 32
HTTP_METHOD_POST = 2
HTTP_METHOD_DELETE = 16
HTTP_METHOD_OPTIONS = 64
HTTP_METHOD_PATCH = 128


LOG_INFO = 6
LOG_NOTICE = 5
LOG_ERR = 3
RESULT_OK = 1
RESULT_RETRY = 2
RESULT_ERROR = 0
MODULE_LOAD = 1
MODULE_UNLOAD = 2
TIMER_ONESHOT = 1
CONN_PROTO_HTTP = 1
CONN_PROTO_UNKNOWN = 0
CONN_PROTO_WEBSOCKET = 2
CONN_STATE_ESTABLISHED = 2


METHOD_CODES = {
    1: "get",
    2: "post",
    4: "put",
    128: "patch",
    32: "head",
    16: "delete",
    64: "options",
}

ALLOWED_METHODS = (
    "head",  # when used, fatal error is raises "duplicate path", may be it is considered internally as get
    # When route accessed from it, without defining `head` in methods, it returns empty response. The route itself not called
    # "connect",  # unknown to `kore`
    "get",
    "put",
    "patch",
    "post",
    "delete",
    "options",  # needs debugging, sometimes works when defined alone in the handler, failed if there is other methods
)
