from http import HTTPStatus

from ddf.application.exceptions import ApplicationError


class ModelProtocolNotSupportedError(ApplicationError):
    status_code = HTTPStatus
    error_code = "model_protocol_not_supported"


class EdgeExecutionNotConfiguredError(ApplicationError):
    status_code = HTTPStatus
    error_code = "edge_execution_not_configured"


class ModelStreamFailedError(ApplicationError):
    status_code = HTTPStatus
    error_code = "model_stream_failed"
