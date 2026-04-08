"""Data models for Speky requirements, tests, and comments."""

from __future__ import annotations

import datetime
import logging
import subprocess
from pathlib import Path
from types import SimpleNamespace

from .utils import ensure_fields, import_fields, warn_extra_fields


class SpecItem(SimpleNamespace):
    """Base class for specification items (requirements and tests)."""

    folder = 'misc'
    id_field = 'id'
    mandatory_fields = ['long']
    optional_fields = ['short']

    @classmethod
    def fields(cls):
        """Return all fields (id + mandatory + optional)."""
        return [cls.id_field] + cls.mandatory_fields + cls.optional_fields

    @classmethod
    def from_dict(cls, data: dict, location: str, manifest=None):
        """
        Create a SpecItem from YAML data.

        Args:
            data: Dictionary from YAML
            location: Source file path for error messages
            manifest: The Manifest that loaded this file, if any

        Returns:
            Instance of the class

        Raises:
            KeyError: If required fields are missing
        """
        result = SimpleNamespace(source_file=location, manifest=manifest)
        ensure_fields(f'Definition of a {cls.__name__} in "{location}"', data, [cls.id_field])
        item_location = f'Definition of {cls.__name__} {data[cls.id_field]} in "{location}"'
        ensure_fields(item_location, data, cls.mandatory_fields)
        warn_extra_fields(item_location, data, cls.fields())
        import_fields(result, data, cls.fields())
        return cls(**result.__dict__)

    @property
    def title(self):
        """Return formatted title with ID and optional short description."""
        return f'`{self.id}` {self.short}' if self.short else f'`{self.id}`'

    def json_oneliner(self, full_summary: bool):
        """Equivalent of the title but in JSON format"""
        result = {'id': self.id}
        if self.short:
            result['short'] = self.short
        if full_summary:
            result['category'] = self.category
            if hasattr(self, 'tags') and self.tags:
                result['tags'] = self.tags
        return result

    def __lt__(self, other):
        """Compare by ID field for sorting."""
        return getattr(self, self.id_field) < getattr(other, other.id_field)


class Requirement(SpecItem):
    """speky:speky#SF001 — Requirement specification item."""

    folder = 'requirements'
    optional_fields = SpecItem.optional_fields + ['tags', 'client_statement', 'properties', 'ref']


class Test(SpecItem):
    """speky:speky#SF001 — Test specification item."""

    folder = 'tests'
    mandatory_fields = SpecItem.mandatory_fields + ['ref', 'steps']
    optional_fields = SpecItem.optional_fields + ['initial', 'prereq']

    step_fields = {'action', 'run', 'expected', 'sample', 'sample_lang'}

    @classmethod
    def from_dict(cls, data: dict, location: str, manifest=None):
        """
        Create a Test from YAML data, validating step structure.

        Args:
            data: Dictionary from YAML
            location: Source file path for error messages
            manifest: The Manifest that loaded this file, if any

        Returns:
            Test instance

        Raises:
            KeyError: If required fields are missing
        """
        result = super().from_dict(data, location, manifest=manifest)
        for i, step in enumerate(result.steps, 1):
            name = f'Step {i} of {cls.__name__} {data[cls.id_field]} in "{location}"'
            ensure_fields(name, step, ['action'])
            warn_extra_fields(name, step, cls.step_fields)
        return result


class Comment(SimpleNamespace):
    """speky:speky#SF006 — Comment on a requirement or test."""

    fields = ['about', 'from', 'date', 'text', 'external']

    @classmethod
    def from_dict(cls, data: dict, location: str):
        """
        Create a Comment from YAML data.

        Args:
            data: Dictionary from YAML
            location: Source file path for error messages

        Returns:
            Comment instance

        Raises:
            KeyError: If required fields are missing
        """
        result = SimpleNamespace(source_file=location)
        item_location = f'Definition of a {cls.__name__} in "{location}"'
        ensure_fields(item_location, data, cls.fields)
        warn_extra_fields(item_location, data, cls.fields)
        import_fields(result, data, cls.fields)
        result.external = result.external in ['True', 'true', True, 1, '1']
        result.time = datetime.datetime.strptime(result.date, '%d/%m/%Y').astimezone(datetime.UTC)
        return cls(**result.__dict__)

    def __lt__(self, other):
        """Compare by timestamp for chronological sorting."""
        return self.time < other.time


class NullSourceLinks:
    """A no-op source link config that never generates URLs."""

    def url_for(self, path: Path) -> None:
        return None


class Manifest:
    """A loaded project manifest, holding context for file loading and link generation."""

    def __init__(
        self,
        name: str,
        root_dir: Path,
        source_file: Path,
        code_sources: list[str],
        link_config: SourceLinkConfig | NullSourceLinks,
        parent_manifest: Manifest | None,
        coverage_categories: list[str] | None = None,
    ):
        self.name = name
        self.root_dir = root_dir
        self.source_file = source_file
        self.code_sources = code_sources
        self.link_config = link_config
        self.parent = parent_manifest
        self.coverage_categories = coverage_categories or []

    def relative_path(self, absolute: Path) -> str:
        """Return the display name of a file: path relative to root_dir."""
        return str(absolute.relative_to(self.root_dir))


def normalize_remote_url(url: str) -> str:
    """Normalize a git remote URL to HTTPS without .git suffix."""
    if url.startswith('git@'):
        host, path = url[len('git@') :].split(':', 1)
        url = f'https://{host}/{path}'
    return url.removesuffix('.git')


class SourceLinkConfig:
    """speky:speky#SF017 — Resolved configuration for generating clickable source links."""

    def __init__(self, url: str, branch: str, git_root: Path):
        self.url = url
        self.branch = branch
        self.git_root = git_root

    @classmethod
    def from_dict(cls, data: dict | None, cwd: Path) -> SourceLinkConfig | NullSourceLinks:
        """
        Build a SourceLinkConfig from a `source_links` manifest dict.

        Returns a NullSourceLinks if data is None or any required value cannot be resolved.
        """
        if data is None:
            return NullSourceLinks()
        log = logging.getLogger(__name__)

        url = data.get('url')
        branch = data.get('branch', 'auto')

        if url == 'auto':
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], cwd=cwd, capture_output=True, text=True)
            if result.returncode != 0:
                log.warning('Could not detect git remote URL: %s', result.stderr.strip())
                return NullSourceLinks()
            url = normalize_remote_url(result.stdout.strip())

        if branch == 'auto':
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=cwd, capture_output=True, text=True
            )
            if result.returncode != 0:
                log.warning('Could not detect git branch: %s', result.stderr.strip())
                return NullSourceLinks()
            branch = result.stdout.strip()

        result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            log.warning('Could not find git root: %s', result.stderr.strip())
            return NullSourceLinks()
        git_root = Path(result.stdout.strip())

        return cls(url=url, branch=branch, git_root=git_root)

    def url_for(self, path: Path) -> str | None:
        """Return a URL to the given absolute path, or None if outside the git root."""
        if path.is_relative_to(self.git_root):
            repo_file = path.relative_to(self.git_root).as_posix()
            return f'{self.url}/blob/{self.branch}/{repo_file}'
        return None
