"""Core Specification class for loading and managing requirements, tests, and comments."""

import csv
import logging
from collections import defaultdict

import yaml

from .models import Comment, Requirement, Test
from .utils import ensure_fields

logger = logging.getLogger(__name__)


class Specification:
    """
    Container for requirements, tests, and comments with cross-reference tracking.

    speky:speky#SF001
    """

    def __init__(self):
        """Initialize empty specification."""
        self.requirements = defaultdict(list)
        self.tests = defaultdict(list)
        self.references = defaultdict(list)
        self.testers_of = defaultdict(list)
        self.comments = defaultdict(list)
        self.by_id = {}
        self.tags = defaultdict(list)

    def load_requirement(self, requirement: Requirement, category: str):
        """
        Add a requirement to the specification.

        Args:
            requirement: Requirement instance
            category: Category name (e.g., "functional", "non-functional")

        Raises:
            KeyError: If requirement ID is already defined
        """
        if requirement.id in self.by_id:
            message = f'Multiple definitions of requirement "{requirement.id}". ID must be unique'
            raise KeyError(message)
        requirement.category = category
        requirement.kind = 'requirement'
        self.by_id[requirement.id] = requirement
        self.requirements[category].append(requirement)
        if requirement.ref:
            for referred in requirement.ref:
                self.references[referred].append(requirement)
        if requirement.tags:
            for tag in requirement.tags:
                self.tags[tag].append(requirement)

    def load_test(self, test: Test, category: str):
        """
        Add a test to the specification.

        Args:
            test: Test instance
            category: Category name
        """
        test.category = category
        test.kind = 'test'
        self.by_id[test.id] = test
        self.tests[category].append(test)
        for req in test.ref:
            self.testers_of[req].append(test)

    def load_comment(self, comment: Comment):
        """
        Add a comment to the specification.

        Args:
            comment: Comment instance
        """
        self.comments[comment.about].append(comment)

    def read_yaml(self, file_name: str):
        """
        Load a YAML file containing requirements, tests, or comments.

        speky:speky#SF001

        Args:
            file_name: Path to YAML file

        Raises:
            RuntimeError: If file is empty
            KeyError: If required fields are missing
        """
        with open(file_name, encoding='utf8') as f:
            data = yaml.safe_load(f)
            if data is None:
                message = f'Empty file "{file_name}"'
                raise RuntimeError(message)
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
        """
        Load comments from a CSV file.

        speky:speky#SF010

        Args:
            file_name: Path to CSV file
        """
        with open(file_name, encoding='utf8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.load_comment(Comment.from_yaml(row, file_name))

    def check_references(self):
        """
        Validate that all referenced IDs exist.

        Raises:
            KeyError: If a referenced ID does not exist
        """
        for req in self.by_id.values():
            if req.ref is None:
                continue
            for referred in req.ref:
                if referred not in self.by_id:
                    message = f'Requirement {referred}, referred from {req.id}, does not exist'
                    raise KeyError(message)
        for referred in self.comments.keys():
            if referred not in self.by_id:
                message = f'Requirement or Test {referred}, referred from a comment, does not exist'
                raise KeyError(message)
