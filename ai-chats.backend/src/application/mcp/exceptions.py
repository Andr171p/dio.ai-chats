from http import HTTPStatus

from ddf.application.exceptions import ApplicationError


class McpServerUnavailableError(ApplicationError):
    status_code = HTTPStatus.BAD_GATEWAY
    error_code = "mcp_server_unavailable"


class McpConnectionNotSupportedError(ApplicationError):
    status_code = HTTPStatus.NOT_IMPLEMENTED
    error_code = "mcp_connection_not_supported"
