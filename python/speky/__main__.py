import argparse
import csv
import datetime
import logging
from collections import defaultdict
from importlib.metadata import version
from types import SimpleNamespace

import yaml

from .generators import specification_to_myst

logger = logging.getLogger(__name__)


def main():
    cli_parser = argparse.ArgumentParser(
        prog='Speky',
        description="Write your project's specification in YAML, display it as a static website",
        epilog='Copyright (c) 2025 Antoine  GAGNIERE',
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
    cli_args = cli_parser.parse_args()

    specs = Specification()
    for filename in cli_args.paths:
        print(f'Loading {filename}')
        specs.read_yaml(filename)
    if cli_args.comment_csvs:
        for filename in cli_args.comment_csvs:
            print(f'Loading {filename} as comments')
            specs.read_comment_csv(filename)
    specification_to_myst(specs, cli_args.project_name, cli_args.output_folder)


if __name__ == '__main__':
    main()


def import_fields(destination, source: dict[str], fields: list[str]):
    """
    Creates members to the destination objects, that have the name and values of the desired fields from the source dictionnary.
    Also prints a warning about remaining fields that were not imported
    """
    for field in fields:
        setattr(destination, field, source.get(field, None))
    extras = source.keys() - set(fields)
    if extras:
        logger.warning('Ignored extra fields: %s', extras)


def ensure_fields(location: str, obj: dict[str], fields: list[str]):
    """
    Raise an exception if one of the expected fields is missing
    """
    for field in fields:
        if field not in obj:
            message = f'Missing the field "{field}" from {location}'
            raise Exception(message)


class SpecItem(SimpleNamespace):
    folder = 'misc'
    id_field = 'id'
    mandatory_fields = ['long']
    fields = [id_field] + mandatory_fields + ['short', 'ref']

    @classmethod
    def from_yaml(cls, data: dict, location: str):
        result = SimpleNamespace()
        ensure_fields(f'Definition of a {cls.__name__} in "{location}"', data, [cls.id_field])
        ensure_fields(
            f"Definition of {cls.__name__} {data[cls.id_field]} in '{location}'",
            data,
            cls.mandatory_fields,
        )
        import_fields(result, data, cls.fields)
        return cls(**result.__dict__)

    @property
    def title(self):
        return f'`{self.id}` {self.short}' if self.short else f'`{self.id}`'

    def __lt__(self, other):
        return self.id < other.id


class Requirement(SpecItem):
    folder = 'requirements'
    fields = SpecItem.fields + ['tags', 'client_statement', 'properties']


class Test(SpecItem):
    folder = 'tests'
    fields = SpecItem.fields + ['initial', 'prereq', 'steps']


class Comment(SimpleNamespace):
    fields = ['about', 'from', 'date', 'text', 'external']

    @classmethod
    def from_yaml(cls, data: dict, location: str):
        result = SimpleNamespace()
        ensure_fields(f'Definition of a {cls.__name__} in "{location}"', data, cls.fields)
        import_fields(result, data, cls.fields)
        result.external = result.external in ['True', 'true', True, 1, '1']
        result.time = datetime.datetime.strptime(result.date, '%d/%m/%Y').astimezone(datetime.UTC)
        return cls(**result.__dict__)

    def __lt__(self, other):
        return self.time < other.time


class Specification:
    def __init__(self):
        self.requirements = defaultdict(list)
        self.tests = defaultdict(list)
        self.references = defaultdict(list)
        self.testers_of = defaultdict(list)
        self.comments = defaultdict(list)
        self.by_id = {}
        self.tags = defaultdict(list)

    def load_requirement(self, requirement: Requirement, category: str):
        self.by_id[requirement.id] = requirement
        self.requirements[category].append(requirement)
        if requirement.ref:
            for referred in requirement.ref:
                self.references[referred].append(requirement)
        if requirement.tags:
            for tag in requirement.tags:
                self.tags[tag].append(requirement)

    def load_test(self, test: Test, category: str):
        self.by_id[test.id] = test
        self.tests[category].append(test)
        for req in test.ref:
            self.testers_of[req].append(test)

    def load_comment(self, comment: Comment):
        self.comments[comment.about].append(comment)

    def read_yaml(self, file_name: str):
        with open(file_name, encoding='utf8') as f:
            data = yaml.safe_load(f)
            ensure_fields(f'Top-level of "{file_name}"', data, ['kind'])
            match data['kind']:
                case 'requirements':
                    ensure_fields(
                        f'Top-level of requirements file "{file_name}"',
                        data,
                        ['requirements', 'category'],
                    )
                    for req in data['requirements']:
                        self.load_requirement(Requirement.from_yaml(req, file_name), data['category'])
                case 'tests':
                    ensure_fields(f'Top-level of tests file "{file_name}"', data, ['tests', 'category'])
                    for test in data['tests']:
                        self.load_test(Test.from_yaml(test, file_name), data['category'])
                case 'comments':
                    ensure_fields(f'Top-level of comments file "{file_name}"', data, ['comments'])
                    default = {'external': False}
                    if 'default' in data:
                        default |= data['default']
                    for comment in data['comments']:
                        self.load_comment(Comment.from_yaml(default | comment, file_name))

    def read_comment_csv(self, file_name: str):
        with open(file_name, encoding='utf8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.load_comment(Comment.from_yaml(row, file_name))
