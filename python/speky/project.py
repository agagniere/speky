"""Project manifest resolution and specification loading."""

from __future__ import annotations

import hashlib
import logging
import os
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .code_tests import discover_code_references
from .specification import Specification

logger = logging.getLogger(__name__)


@dataclass
class ProjectSource:
    """Manifest-defined source of YAML specs and code evidence."""

    kind: str
    root: str | None = None
    git_url: str | None = None
    ref: str | None = None
    subdir: str | None = None
    files: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)
    comment_csv: list[str] = field(default_factory=list)
    code_roots: list[str] = field(default_factory=list)


@dataclass
class ProjectConfig:
    """Resolved project configuration."""

    name: str
    display_name: str
    manifest_path: Path
    sources: list[ProjectSource]


def load_specification(
    *,
    paths: list[str] | None,
    comment_csvs: list[str] | None,
    project_name: str | None,
    manifest_path: str | None,
    cwd: Path | None = None,
) -> tuple[Specification, str]:
    """Load a specification either from explicit files or from a project manifest."""
    if paths:
        cwd = cwd or Path.cwd()
        config = _resolve_context_project(project_name=project_name, manifest_path=manifest_path, cwd=cwd)
        if config:
            logger.info('Using project context from %s', config.manifest_path)
        specs = Specification(project_name=config.name if config else project_name)
        for filename in paths:
            logger.info('Loading %s', filename)
            specs.read_yaml(filename)
        for filename in comment_csvs or []:
            logger.info('Loading %s as comments', filename)
            specs.read_comment_csv(filename)
        if config:
            code_roots: list[Path] = []
            for source in config.sources:
                source_root = _materialize_source_root(source, config.manifest_path.parent)
                code_roots.extend(_expand_code_roots(source_root, source.code_roots))
            for ref in discover_code_references(config.name, code_roots, config.manifest_path.parent):
                specs.load_code_reference(ref)
            return specs, config.display_name
        return specs, project_name or 'Speky'

    cwd = cwd or Path.cwd()
    config = resolve_project(project_name=project_name, manifest_path=manifest_path, cwd=cwd)
    specs = Specification(project_name=config.name)

    code_roots: list[Path] = []
    for source in config.sources:
        source_root = _materialize_source_root(source, config.manifest_path.parent)
        for filename in _expand_yaml_files(source_root, source):
            logger.info('Loading %s', filename)
            specs.read_yaml(str(filename))
        for filename in _expand_patterns(source_root, source.comment_csv):
            logger.info('Loading %s as comments', filename)
            specs.read_comment_csv(str(filename))
        code_roots.extend(_expand_code_roots(source_root, source.code_roots))

    for ref in discover_code_references(config.name, code_roots, config.manifest_path.parent):
        specs.load_code_reference(ref)
    return specs, config.display_name


def resolve_project(*, project_name: str | None, manifest_path: str | None, cwd: Path) -> ProjectConfig:
    """Resolve a project configuration from an explicit manifest path or a project name."""
    if manifest_path:
        return _read_manifest(Path(manifest_path))
    if not project_name:
        raise ValueError('Either explicit YAML files or --project/--manifest must be provided')

    local_manifest = _find_local_manifest(project_name, cwd)
    if local_manifest:
        return _read_manifest(local_manifest)

    for root in _manifest_search_paths():
        for manifest in root.rglob('speky.toml'):
            config = _read_manifest(manifest)
            if config.name == project_name:
                return config
    raise FileNotFoundError(f'No speky.toml manifest found for project {project_name!r}')


def _resolve_context_project(*, project_name: str | None, manifest_path: str | None, cwd: Path) -> ProjectConfig | None:
    """Resolve an optional project context for explicit-path workflows."""
    if manifest_path or project_name:
        return resolve_project(project_name=project_name, manifest_path=manifest_path, cwd=cwd)

    manifest = _find_nearest_manifest(cwd)
    if manifest:
        return _read_manifest(manifest)
    return None


def _find_local_manifest(project_name: str, cwd: Path) -> Path | None:
    nearest = _find_nearest_manifest(cwd)
    if nearest:
        config = _read_manifest(nearest)
        if config.name == project_name:
            return nearest
    for directory in cwd.parents:
        candidate = directory / 'speky.toml'
        if candidate.is_file():
            config = _read_manifest(candidate)
            if config.name == project_name:
                return candidate
    return None


def _find_nearest_manifest(cwd: Path) -> Path | None:
    for directory in [cwd, *cwd.parents]:
        candidate = directory / 'speky.toml'
        if candidate.is_file():
            return candidate
    return None


def _manifest_search_paths() -> list[Path]:
    env = os.getenv('SPEKY_PROJECTS_PATH')
    if not env:
        return []
    return [Path(entry).expanduser() for entry in env.split(os.pathsep) if entry]


def _read_manifest(path: Path) -> ProjectConfig:
    with path.open('rb') as fh:
        data = tomllib.load(fh)

    project = data.get('project', {})
    name = project.get('name')
    if not name:
        raise KeyError(f'Manifest {path} is missing project.name')

    raw_sources = data.get('source')
    if raw_sources is None:
        raw_sources = data.get('sources', [])
    if isinstance(raw_sources, dict):
        raw_sources = [raw_sources]
    if not raw_sources:
        raw_sources = [{'kind': 'workspace', 'root': '.', 'files': ['specs/**/*.yaml'], 'code_roots': ['tests', 'src']}]

    sources = [_validate_source(ProjectSource(**source), path) for source in raw_sources]
    return ProjectConfig(
        name=name,
        display_name=project.get('display_name', name),
        manifest_path=path,
        sources=sources,
    )


def _validate_source(source: ProjectSource, manifest_path: Path) -> ProjectSource:
    if source.kind not in {'workspace', 'path', 'git'}:
        raise KeyError(f'Manifest {manifest_path} has unknown source kind {source.kind!r}')
    if source.kind == 'path' and not source.root:
        raise KeyError(f'Manifest {manifest_path} path source requires root')
    if source.kind == 'git' and not source.git_url:
        raise KeyError(f'Manifest {manifest_path} git source requires git_url')
    for field_name in ('files', 'requirements', 'tests', 'comments', 'comment_csv', 'code_roots'):
        value = getattr(source, field_name)
        if not isinstance(value, list):
            raise KeyError(f'Manifest {manifest_path} field {field_name} must be a list')
    return source


def _materialize_source_root(source: ProjectSource, manifest_dir: Path) -> Path:
    kind = source.kind
    if kind == 'workspace':
        root = source.root or '.'
        return (manifest_dir / root).resolve()
    if kind == 'path':
        if not source.root:
            raise KeyError('Path source requires root')
        return Path(source.root).expanduser().resolve()
    if kind == 'git':
        if not source.git_url:
            raise KeyError('Git source requires git_url')
        root = _ensure_git_checkout(source.git_url, source.ref)
        if source.subdir:
            root = root / source.subdir
        return root.resolve()
    raise KeyError(f'Unknown source kind {kind!r}')


def _ensure_git_checkout(git_url: str, ref: str | None) -> Path:
    cache_home = Path(os.getenv('XDG_CACHE_HOME', Path.home() / '.cache'))
    cache_root = cache_home / 'speky' / 'git-sources'
    cache_root.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(f'{git_url}\0{ref or "HEAD"}'.encode()).hexdigest()[:16]
    checkout = cache_root / key
    if not checkout.exists():
        subprocess.run(['git', 'clone', '--quiet', git_url, str(checkout)], check=True)
    if ref:
        subprocess.run(['git', '-C', str(checkout), 'checkout', '--quiet', ref], check=True)
    return checkout


def _expand_yaml_files(source_root: Path, source: ProjectSource) -> list[Path]:
    patterns = [*source.files, *source.requirements, *source.tests, *source.comments]
    if not patterns:
        patterns = ['specs/**/*.yaml']
    return _expand_patterns(source_root, patterns)


def _expand_patterns(source_root: Path, patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for path in sorted(source_root.glob(pattern)):
            if path.is_file() and path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def _expand_code_roots(source_root: Path, patterns: list[str]) -> list[Path]:
    roots: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns or ['tests']:
        for path in sorted(source_root.glob(pattern)):
            if path.exists() and path not in seen:
                seen.add(path)
                roots.append(path)
    return roots
