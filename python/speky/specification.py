"""Core Specification class for loading and managing requirements, tests, and comments."""

import csv
import logging
import os
import tomllib
from collections import defaultdict
from pathlib import Path

import yaml

from .models import Comment, Requirement, SourceLinkConfig, Test
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
        self.root_dir = Path()
        self.loaded_files: set[str] = set()
        self.scan_configs: list[tuple[str, Path, list[str], SourceLinkConfig | None]] = []
        self.code_refs_by_id: dict[str, list] = defaultdict(list)
        self.spec_file_urls: dict[str, str] = {}

    def load_requirement(self, requirement: Requirement, category: str):
        """
        Add a requirement to the specification.

        Raises:
            KeyError: If requirement ID is already defined
        """
        if requirement.id in self.by_id:
            existing = self.by_id[requirement.id]
            message = f'Multiple definitions of {requirement.id}: already defined in "{existing.source_file}", redefined in "{requirement.source_file}"'
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

    def read_file(self, file_name: str):
        """
        speky:speky#SF001
        speky:speky#SN001
        speky:speky#SF014

        Load a YAML or TOML file containing requirements, tests, or comments.

        Args:
            file_name: Path to YAML or TOML file

        Raises:
            RuntimeError: If file is empty
            KeyError: If required fields are missing
        """
        resolved = str(Path(file_name).resolve())
        if resolved in self.loaded_files:
            return
        self.loaded_files.add(resolved)
        display_name = os.path.relpath(file_name, start=self.root_dir)
        logger.info('Loading %s', display_name)
        if file_name.endswith('.toml'):
            with open(file_name, 'rb') as f:
                data = tomllib.load(f)
        else:
            with open(file_name, encoding='utf8') as f:
                data = yaml.safe_load(f)
        if not data:
            message = f'Empty file "{file_name}"'
            raise RuntimeError(message)
        ensure_fields(f'Top-level of "{display_name}"', data, ['kind'])
        match data['kind']:
            case 'requirements':
                ensure_fields(
                    f'Top-level of requirements file "{display_name}"',
                    data,
                    ['requirements', 'category'],
                )
                for req in data['requirements']:
                    self.load_requirement(Requirement.from_dict(req, display_name), data['category'])
            case 'tests':
                ensure_fields(f'Top-level of tests file "{display_name}"', data, ['tests', 'category'])
                for test in data['tests']:
                    self.load_test(Test.from_dict(test, display_name), data['category'])
            case 'comments':
                ensure_fields(f'Top-level of comments file "{display_name}"', data, ['comments'])
                default = {'external': False}
                if 'default' in data:
                    default |= data['default']
                for comment in data['comments']:
                    self.load_comment(Comment.from_dict(default | comment, display_name))
            case 'project':
                ensure_fields(f'Manifest "{file_name}"', data, ['name', 'files'])
                manifest_dir = Path(file_name).parent
                self.root_dir = (manifest_dir / data.get('root_directory', '.')).resolve()
                logger.debug('Now loading from %s', self.root_dir)
                link_config = (
                    SourceLinkConfig.from_dict(data['source_links'], manifest_dir)
                    if 'source_links' in data
                    else None
                )
                if sources := data.get('code_sources'):
                    self.scan_configs.append((data['name'], self.root_dir, sources, link_config))
                for pattern in data['files']:
                    for path in sorted(self.root_dir.glob(pattern)):
                        if link_config:
                            display_name = os.path.relpath(str(path), start=self.root_dir)
                            url = link_config.url_for(path)
                            if url:
                                self.spec_file_urls[display_name] = url
                        self.read_file(str(path))
                for pattern in data.get('comments_csvs', []):
                    for path in sorted(self.root_dir.glob(pattern)):
                        self.read_comment_csv(str(path))

    def read_comment_csv(self, file_name: str):
        """
        Load comments from a CSV file.

        speky:speky#SF010

        Args:
            file_name: Path to CSV file
        """
        display_name = os.path.relpath(file_name, start=self.root_dir)
        logger.info('Loading %s as comments', display_name)
        with open(file_name, encoding='utf8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.load_comment(Comment.from_dict(row, display_name))

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
                    message = f'Requirement {referred}, referred from {req.id} in "{req.source_file}", does not exist'
                    raise KeyError(message)
        for referred, comment_list in self.comments.items():
            if referred not in self.by_id:
                source_file = comment_list[0].source_file
                message = f'Requirement or Test {referred}, referred from a comment in "{source_file}", does not exist'
                raise KeyError(message)

    def scan_code_sources(self):
        """
        speky:speky#SF016

        Scan declared code sources for speky reference tags.
        """
        if not self.scan_configs:
            return
        from .scanner import scan_sources

        for project_name, root_dir, patterns, link_config in self.scan_configs:
            files = []
            for pattern in patterns:
                files.extend(sorted(root_dir.glob(pattern)))
            logger.info('Scanning %d source file(s) for project %r', len(files), project_name)
            for ref in scan_sources(files, project_name, root_dir):
                if link_config:
                    abs_path = (root_dir / ref.file).resolve()
                    base_url = link_config.url_for(abs_path)
                    if base_url:
                        ref.url = f'{base_url}#L{ref.line}'
                self.code_refs_by_id[ref.target_id].append(ref)
        unknown = sorted(ref_id for ref_id in self.code_refs_by_id if ref_id not in self.by_id)
        if unknown:
            logger.warning('Code references to unknown IDs: %s', ', '.join(unknown))
