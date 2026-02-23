"""CLI entry point for Speky specification tool."""

import argparse
import importlib.resources
import logging
import logging.config
import sys
from importlib.metadata import version
from pathlib import Path

import yaml

from .generators import specification_to_myst
from .specification import Specification

assets = importlib.resources.files(__package__).joinpath('assets')
default_logging_file = assets.joinpath('logging.yaml')
logger = logging.getLogger(__package__)


def main():
    """Main entry point with error handling."""
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
    Run the Speky CLI tool.

    Args:
        argv: Command-line arguments (uses sys.argv if None)
    """
    cli_parser = argparse.ArgumentParser(
        prog='Speky',
        description="Write your project's specification in YAML, display it as a static website",
        epilog='Copyright (c) 2025-2026 Antoine GAGNIERE',
    )
    cli_parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + version(__package__))
    cli_parser.add_argument(
        'paths',
        type=str,
        metavar='FILE',
        nargs='+',
        help='The path to a YAML file containing requirements, tests or comments',
    )
    cli_parser.add_argument(
        '-o',
        '--output-folder',
        type=str,
        metavar='PATH',
        default='markdown',
        help='The folder where to place all generated files',
    )
    cli_parser.add_argument(
        '-C',
        '--comment-csv',
        dest='comment_csvs',
        metavar='FILE',
        type=str,
        action='append',
        help='The path to a CSV file containing comments',
    )
    cli_parser.add_argument(
        '-p',
        '--project-name',
        type=str,
        required=True,
        help='Name of the project used for the title',
    )
    cli_parser.add_argument(
        '-l',
        '--logging-config',
        type=str,
        default=default_logging_file,
        help='Specify a custom config file of the logging library',
    )
    cli_parser.add_argument(
        '-c', '--check-only', action='store_true', help='Validate input files but do not output any markdown'
    )
    cli_parser.add_argument(
        '--sort',
        action=argparse.BooleanOptionalAction,
        default=True,
        help='Sort requirements by ID. If false, the order of files passed as positionals is significant',
    )
    cli_args = cli_parser.parse_args(argv)

    logging_config_file = Path(cli_args.logging_config)
    with logging_config_file.open() as f:
        logging.config.dictConfig(yaml.safe_load(f))

    specs = Specification()
    for filename in cli_args.paths:
        logger.info('Loading %s', filename)
        specs.read_yaml(filename)
    if cli_args.comment_csvs:
        for filename in cli_args.comment_csvs:
            logger.info('Loading %s as comments', filename)
            specs.read_comment_csv(filename)
    specs.check_references()
    if not cli_args.check_only:
        specification_to_myst(specs, cli_args.project_name, cli_args.output_folder, cli_args.sort)
