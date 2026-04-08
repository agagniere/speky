"""Core Specification class for loading and managing requirements, tests, and comments."""

import csv
import logging
import tomllib
from collections import defaultdict
from pathlib import Path

import yaml

from .models import Comment, Manifest, Requirement, SourceLinkConfig, Test
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
        self.loaded_files: set[Path] = set()
        self.manifests: list[Manifest] = []
        self.code_refs_by_id: dict[str, list] = defaultdict(list)

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

    def read_file(self, path: Path, manifest: Manifest | None = None):
        """
        speky:speky#SF001
        speky:speky#SN001
        speky:speky#SF014

        Load a YAML or TOML file containing requirements, tests, or comments.

        Args:
            path: Path to YAML or TOML file
            manifest: The Manifest that caused this file to be loaded, if any

        Raises:
            RuntimeError: If file is empty
            KeyError: If required fields are missing
        """
        absolute = path.resolve()
        if absolute in self.loaded_files:
            return
        self.loaded_files.add(absolute)
        display_name = manifest.relative_path(path) if manifest else str(path)
        logger.info('%sLoading %s', f'[{manifest.name}] ' if manifest else '', display_name)
        if path.suffix == '.toml':
            with open(absolute, 'rb') as f:
                data = tomllib.load(f)
        else:
            with open(absolute, encoding='utf8') as f:
                data = yaml.safe_load(f)
        if not data:
            message = f'Empty file "{display_name}"'
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
                    self.load_requirement(Requirement.from_dict(req, display_name, manifest=manifest), data['category'])
            case 'tests':
                ensure_fields(f'Top-level of tests file "{display_name}"', data, ['tests', 'category'])
                for test in data['tests']:
                    self.load_test(Test.from_dict(test, display_name, manifest=manifest), data['category'])
            case 'comments':
                ensure_fields(f'Top-level of comments file "{display_name}"', data, ['comments'])
                default = {'external': False}
                if 'default' in data:
                    default |= data['default']
                for comment in data['comments']:
                    self.load_comment(Comment.from_dict(default | comment, display_name))
            case 'project':
                ensure_fields(f'Manifest "{display_name}"', data, ['name', 'files'])
                manifest_dir = absolute.parent
                root_dir = (manifest_dir / data.get('root_directory', '.')).resolve()
                logger.debug('%s loads from %s', data['name'], root_dir)
                link_config = SourceLinkConfig.from_dict(data.get('source_links'), manifest_dir)
                current_manifest = Manifest(
                    name=data['name'],
                    root_dir=root_dir,
                    source_file=absolute,
                    code_sources=data.get('code_sources', []),
                    link_config=link_config,
                    parent_manifest=manifest,
                    coverage_categories=data.get('coverage_categories'),
                )
                self.manifests.append(current_manifest)
                for pattern in data['files']:
                    for path in sorted(root_dir.glob(pattern)):
                        self.read_file(path, manifest=current_manifest)
                for pattern in data.get('comments_csvs', []):
                    for path in sorted(root_dir.glob(pattern)):
                        self.read_comment_csv(path, manifest=current_manifest)

    def read_comment_csv(self, path: Path, manifest: Manifest | None = None):
        """
        Load comments from a CSV file.

        speky:speky#SF010

        Args:
            path: Path to CSV file
            manifest: The Manifest that caused this file to be loaded, if any
        """
        display_name = manifest.relative_path(path) if manifest else str(path)
        logger.info('%sLoading %s as comments', f'[{manifest.name}] ' if manifest else '', display_name)
        with open(path, encoding='utf8', newline='') as f:
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
        manifests_with_sources = [m for m in self.manifests if m.code_sources]
        if not manifests_with_sources:
            return
        from .scanner import scan_sources

        for manifest in manifests_with_sources:
            files = []
            for pattern in manifest.code_sources:
                files.extend(sorted(manifest.root_dir.glob(pattern)))
            logger.info('Scanning %d source file(s) for project %r', len(files), manifest.name)
            for ref in scan_sources(files, manifest.name):
                ref.manifest = manifest
                base_url = manifest.link_config.url_for(ref.file)
                if base_url:
                    ref.url = f'{base_url}#L{ref.line}'
                self.code_refs_by_id[ref.target_id].append(ref)
        unknown = sorted(ref_id for ref_id in self.code_refs_by_id if ref_id not in self.by_id)
        if unknown:
            logger.warning('Code references to unknown IDs: %s', ', '.join(unknown))

    def is_test_automated(self, test_id: str) -> bool:
        """True if the test has at least one code reference flagged as a test function."""
        return any(r.is_test for r in self.code_refs_by_id.get(test_id, []))

    def compute_coverage(self):
        """Compute coverage buckets for each manifest that declares coverage_categories."""
        for manifest in self.manifests:
            for category in manifest.coverage_categories:
                requirements = [r for r in self.requirements.get(category, []) if r.manifest is manifest]
                automated, partial, manual, no_plan = [], [], [], []
                for r in sorted(requirements):
                    if r.id not in self.testers_of:
                        no_plan.append(r)
                    else:
                        tests = self.testers_of[r.id]
                        auto_count = sum(1 for t in tests if self.is_test_automated(t.id))
                        if auto_count == len(tests):
                            automated.append(r)
                        elif auto_count == 0:
                            manual.append(r)
                        else:
                            partial.append(r)
                manifest.coverage[category] = (automated, partial, manual, no_plan)
