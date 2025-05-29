import argparse
from collections import defaultdict
import logging
from types import SimpleNamespace
import yaml
import sys
from generators import specification_to_myst

# your_package/__init__.py
import importlib.metadata

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"  # Fallback for development mode

if __name__ == "__main__":
    main()

def main():
    cli_parser = argparse.ArgumentParser(
        prog = 'Speky',
        description = "Write your project's specification in YAML, display it as a static website",
        epilog = 'Copyright (c) 2025 Antoine  GAGNIERE')
    cli_parser.add_argument('paths',
                            type = str,
                            metavar = 'FILE',
                            nargs = '+',
                            help = 'The path of a file to parse as ublox stream')
    cli_args = cli_parser.parse_args()

    print(cli_args.paths)
    specs = Specification()
    for filename in cli_args.paths:
        print(f'Loading {filename}')
        specs.read_yaml(filename)
    specification_to_myst(specs, 'Speky 0.0.5', 'generated')

def import_fields(destination, source: dict[str], fields: list[str]):
    """
    Creates members to the destination objects, that have the name and values of the desired fields from the source dictionnary.
    Also prints a warning about remaining fields that were not imported
    """
    for field in fields:
        setattr(destination, field, source.get(field, None))
    extras = source.keys() - set(fields)
    if extras:
        logging.warning(f'Ignored extra fields: {extras}')

def ensure_fields(location: str, obj: dict[str], fields: list[str]):
    """
    Raise an exception if one of the expected fields is missing
    """
    for field in fields:
        if not field in obj:
            raise Exception(f'Missing the "{field}" from {location}')

class Requirement(SimpleNamespace):
    FIELDS = ['id', 'short', 'long', 'tags', 'ref', 'client_statement']

    @classmethod
    def from_yaml(cls, data: dict, location: str):
        result = SimpleNamespace()
        ensure_fields(f'Definition of a requirement in "{location}"', data, ['id'])
        ensure_fields(f"Definition of requirement {data['id']} in '{location}'", data, ['long'])
        import_fields(result, data, cls.FIELDS)
        return cls(**result.__dict__)

    @property
    def title(self):
        return f'`{self.id}` {self.short}' if self.short else f'`{self.id}`'

class Specification:
    def __init__(self):
        self.requirements = defaultdict(list)
        self.tests = defaultdict(list)
        self.references = defaultdict(list)
        self.testers_of = defaultdict(list)
        self.comments = defaultdict(list)
        self.by_id = dict()
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

    def read_yaml(self, file_name: str):
        with open(file_name, encoding='utf8') as f:
            data = yaml.safe_load(f)
            ensure_fields(f'Top-level of "{file_name}"', data, ['kind'])
            print('Found a file of kind', data['kind'])
            match data['kind']:
                case 'requirements':
                    ensure_fields(f'Top-level of requirements file "{file_name}"',
                                  data, ['requirements', 'category'])
                    for req in data['requirements']:
                        self.load_requirement(Requirement.from_yaml(req, file_name), data['category'])
