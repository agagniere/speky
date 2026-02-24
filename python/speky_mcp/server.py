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
from importlib.metadata import version
from pathlib import Path

import yaml
from speky.specification import Specification

from .protocol import JsonRpcError, ToolError, protocol_error, tool_error, tool_result
from .tools import TOOLS

assets = importlib.resources.files('speky').joinpath('assets')
default_logging_file = assets.joinpath('logging.yaml')
logger = logging.getLogger(__package__)


def main():
    """Wraps run() to catch top-level errors and exit with a non-zero status."""
    try:
        run(None)
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


def run(argv: list[str] | None = None):
    """
    speky:speky_mcp#TMCP001

    When argv is None, sys.argv is used instead
    """
    parser = argparse.ArgumentParser(
        prog='speky-mcp',
        description='MCP server for querying Speky specifications',
        epilog='Copyright (c) 2025-2026 Antoine GAGNIERE',
    )
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + version(__package__))
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

    args = parser.parse_args(argv)

    logging_config_file = Path(args.logging_config)
    with logging_config_file.open() as f:
        logging.config.dictConfig(yaml.safe_load(f))

    # speky:speky_mcp#MCP001
    specs = Specification()
    for filename in args.paths:
        logger.info('Loading %s', filename)
        specs.read_yaml(filename)
    if args.comment_csvs:
        for filename in args.comment_csvs:
            logger.info('Loading %s as comments', filename)
            specs.read_comment_csv(filename)

    # speky:speky_mcp#TMCP002
    specs.check_references()

    logger.info('Specifications loaded successfully')

    # speky:speky_mcp#MCP002
    run_server(specs)


def run_server(specs: Specification):
    """
    speky:speky_mcp#MCP002
    """
    logger.info('MCP server ready, waiting for requests')

    initialized = False

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = handle_request(request, specs, initialized)

            if request.get('method') == 'initialize' and 'error' not in response:
                initialized = True
            elif request.get('method') == 'notifications/initialized':
                logger.info('Client initialization complete')
                continue  # Notifications don't get responses

            json.dump(response, sys.stdout, sort_keys=True)
            sys.stdout.write('\n')
            sys.stdout.flush()

        except json.JSONDecodeError as e:
            logger.error('Invalid JSON: %s', e)
            error_response = protocol_error(None, JsonRpcError.PARSE_ERROR, 'Parse error')
            json.dump(error_response, sys.stdout, sort_keys=True)
            sys.stdout.write('\n')
            sys.stdout.flush()


def handle_request(request: dict, specs: Specification, initialized: bool) -> dict:
    method = request.get('method')
    request_id = request.get('id')

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

    if not initialized and method != 'notifications/initialized':
        return protocol_error(request_id, JsonRpcError.SERVER_NOT_INITIALIZED, 'Server not initialized')

    if method == 'tools/call':
        tool_name = request.get('params', {}).get('name')
        arguments = request.get('params', {}).get('arguments', {})

        handler = TOOLS.get(tool_name)
        if handler:
            try:
                return tool_result(request_id, handler(arguments, specs))
            except ToolError as e:
                return tool_error(request_id, str(e))

        return protocol_error(request_id, JsonRpcError.METHOD_NOT_FOUND, f'Tool not found: {tool_name}')

    return protocol_error(request_id, JsonRpcError.METHOD_NOT_FOUND, f'Method not found: {method}')
