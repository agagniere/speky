"""JSON-RPC 2.0 protocol utilities."""

from enum import IntEnum


class ToolError(Exception):
    """Raised by tool handlers to signal a domain-level error (invalid ID, wrong type, etc.)."""


class JsonRpcError(IntEnum):
    """JSON-RPC 2.0 standard error codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_NOT_INITIALIZED = -32002


def protocol_error(request_id: int | None, code: int, message: str, data: dict | None = None) -> dict:
    error = {
        'code': code,
        'message': message,
    }
    if data is not None:
        error['data'] = data

    return {
        'jsonrpc': '2.0',
        'id': request_id,
        'error': error,
    }


def tool_error(request_id: int, message: str) -> dict:
    """MCP tool errors are reported as a successful result with isError=True, not as a JSON-RPC error."""
    return {
        'jsonrpc': '2.0',
        'id': request_id,
        'result': {
            'isError': True,
            'structuredContent': {
                'error': message,
            },
        },
    }


def tool_result(request_id: int, content: dict) -> dict:
    return {
        'jsonrpc': '2.0',
        'id': request_id,
        'result': {
            'structuredContent': content,
        },
    }
