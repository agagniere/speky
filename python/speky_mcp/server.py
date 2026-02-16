"""
MCP server implementation for Speky specifications.

speky:speky_mcp#MCP001
speky:speky_mcp#MCP002
"""

import argparse
import importlib.resources
import json
import logging
import logging.config
import sys
from enum import IntEnum
from importlib.metadata import version
from pathlib import Path

import yaml
from speky.specification import Specification


class JsonRpcError(IntEnum):
    """JSON-RPC 2.0 standard error codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_NOT_INITIALIZED = -32002


assets = importlib.resources.files('speky').joinpath('assets')
default_logging_file = assets.joinpath('logging.yaml')
logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for the MCP server.

    speky:speky_mcp#TMCP001
    """
    parser = argparse.ArgumentParser(
        prog='speky-mcp',
        description='MCP server for querying Speky specifications',
        epilog='Copyright (c) 2025,2026 Antoine GAGNIERE',
    )
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + version('speky'))
    parser.add_argument(
        'paths',
        type=str,
        metavar='FILE',
        nargs='+',
        help='Path(s) to YAML files containing requirements, tests, or comments',
    )
    parser.add_argument(
        '-C',
        '--comment-csv',
        dest='comment_csvs',
        metavar='FILE',
        type=str,
        action='append',
        help='Path to CSV file(s) containing comments',
    )
    parser.add_argument(
        '-l',
        '--logging-config',
        type=str,
        default=default_logging_file,
        help='Specify a custom config file of the logging library',
    )

    args = parser.parse_args()

    logging_config_file = Path(args.logging_config)
    with logging_config_file.open() as f:
        logging.config.dictConfig(yaml.safe_load(f))

    try:
        # Load specifications
        # speky:speky_mcp#MCP001
        specs = Specification()
        for filename in args.paths:
            logger.info('Loading %s', filename)
            specs.read_yaml(filename)
        if args.comment_csvs:
            for filename in args.comment_csvs:
                logger.info('Loading %s as comments', filename)
                specs.read_comment_csv(filename)

        # Validate cross-references
        # speky:speky_mcp#TMCP002
        specs.check_references()

        logger.info('Specifications loaded successfully')

        # Run JSON-RPC server
        # speky:speky_mcp#MCP002
        run_server(specs)

    except (
        KeyError,
        FileNotFoundError,
        PermissionError,
        NotADirectoryError,
        OSError,
        yaml.reader.ReaderError,
        RuntimeError,
    ) as err:
        logger.critical(err)
        sys.exit(1)


def run_server(specs: Specification):
    """
    Run the JSON-RPC server loop over stdin/stdout.

    speky:speky_mcp#MCP002
    speky:speky_mcp#TMCP003

    Args:
        specs: Loaded specification
    """
    logger.info('MCP server ready, waiting for requests')

    # Server state
    initialized = False

    # Process requests from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = handle_request(request, specs, initialized)

            # Update state based on method
            if request.get('method') == 'initialize' and 'error' not in response:
                initialized = True
            elif request.get('method') == 'notifications/initialized':
                logger.info('Client initialization complete')
                continue  # Notifications don't get responses

            # Send response
            json.dump(response, sys.stdout, sort_keys=True)
            sys.stdout.write('\n')
            sys.stdout.flush()

        except json.JSONDecodeError as e:
            logger.error('Invalid JSON: %s', e)
            error_response = protocol_error(None, JsonRpcError.PARSE_ERROR, 'Parse error')
            json.dump(error_response, sys.stdout, sort_keys=True)
            sys.stdout.write('\n')
            sys.stdout.flush()


def protocol_error(request_id: int | None, code: int, message: str, data: dict | None = None) -> dict:
    """
    Return a JSON-RPC protocol error response.

    Args:
        request_id: JSON-RPC request ID (None for parse errors)
        code: Error code (e.g., -32700 for parse error, -32601 for method not found)
        message: Error message
        data: Optional additional error data

    Returns:
        JSON-RPC error response
    """
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


def handle_get_requirement(request_id: int, arguments: dict, specs: Specification) -> dict:
    """
    Handle get_requirement tool call.

    speky:speky_mcp#MCP003
    speky:speky_mcp#TMCP004

    Args:
        request_id: JSON-RPC request ID
        arguments: Tool arguments containing 'id'
        specs: Loaded specification

    Returns:
        JSON-RPC response
    """
    requirement_id = arguments['id']

    # Check if ID exists
    # speky:speky_mcp#TMCP006
    if requirement_id not in specs.by_id:
        return tool_error(request_id, f'Requirement {requirement_id} not found')

    requirement = specs.by_id[requirement_id]

    # Check if it's a requirement (not a test)
    # speky:speky_mcp#TMCP006
    if requirement.kind != 'requirement':
        return tool_error(request_id, f'{requirement_id} is a {requirement.kind}, not a requirement')

    content = {
        'category': requirement.category,
        'id': requirement.id,
        'long': requirement.long,
    }

    # Add optional fields if present
    # speky:speky_mcp#TMCP005
    if requirement.short:
        content['short'] = requirement.short
    if requirement.tags:
        content['tags'] = requirement.tags
    if requirement.client_statement:
        content['client_statement'] = requirement.client_statement
    if requirement.properties:
        content['properties'] = requirement.properties
    if requirement.ref:
        content['ref'] = [referred.json_oneliner(False) for referred in map(specs.by_id.__getitem__, requirement.ref)]
    if requirement_id in specs.references:
        content['referenced_by'] = [ref.json_oneliner(False) for ref in specs.references[requirement_id]]
    if requirement_id in specs.testers_of:
        content['tested_by'] = [test.json_oneliner(False) for test in specs.testers_of[requirement_id]]
    if requirement_id in specs.comments:
        content['comments'] = [
            {k: v for k, v in comment.__dict__.items() if k in ('date', 'external', 'from', 'text')}
            for comment in specs.comments[requirement_id]
        ]

    return tool_result(request_id, content)


def handle_request(request: dict, specs: Specification, initialized: bool) -> dict:
    """
    Handle a single JSON-RPC request.

    Args:
        request: JSON-RPC request
        specs: Loaded specification
        initialized: Whether server is initialized

    Returns:
        JSON-RPC response
    """
    method = request.get('method')
    request_id = request.get('id')

    # Handle initialization
    # speky:speky_mcp#TMCP003
    if method == 'initialize':
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'protocolVersion': '2025-11-25',
                'capabilities': {
                    'tools': {},
                },
                'serverInfo': {
                    'name': 'speky-mcp',
                    'version': version('speky'),
                },
            },
        }

    # Check if initialized for other methods
    if not initialized and method != 'notifications/initialized':
        return protocol_error(request_id, JsonRpcError.SERVER_NOT_INITIALIZED, 'Server not initialized')

    # Handle tool calls
    # speky:speky_mcp#MCP003
    if method == 'tools/call':
        tool_name = request.get('params', {}).get('name')
        arguments = request.get('params', {}).get('arguments', {})

        if tool_name == 'get_requirement':
            # speky:speky_mcp#TMCP004
            return handle_get_requirement(request_id, arguments, specs)

        return protocol_error(request_id, JsonRpcError.METHOD_NOT_FOUND, f'Tool not found: {tool_name}')

    # Handle other methods
    return protocol_error(request_id, JsonRpcError.METHOD_NOT_FOUND, f'Method not found: {method}')
