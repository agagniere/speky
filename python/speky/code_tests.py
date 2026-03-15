"""Discovery of tagged code references linked to Speky identifiers."""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

ANNOTATION_RE = re.compile(r'speky:(?P<project>[A-Za-z0-9_.-]+)#(?P<id>[A-Z0-9_-]+)')
RUST_FN_RE = re.compile(r'fn\s+(?P<name>[A-Za-z0-9_]+)')


@dataclass(frozen=True, order=True)
class CodeReference:
    """Tagged code reference linked to a Speky identifier."""

    project: str
    target_id: str
    language: str
    path: str
    symbol: str
    line: int
    framework: str | None = None
    is_executable_test: bool = False

    def json_summary(self) -> dict:
        """Return a stable JSON representation for MCP responses."""
        data = {
            'framework': self.framework,
            'language': self.language,
            'line': self.line,
            'path': self.path,
            'project': self.project,
            'symbol': self.symbol,
        }
        return {key: value for key, value in data.items() if value is not None}


def discover_code_references(project_name: str, code_roots: list[Path], repo_root: Path) -> list[CodeReference]:
    """
    Discover tagged code references for a project.

    The current implementation supports Python and Rust sources. It keeps a narrow public interface
    so a tree-sitter-backed parser can replace the internals later without changing callers.
    """
    discovered: list[CodeReference] = []
    for root in code_roots:
        if not root.exists():
            logger.warning('Code root does not exist: %s', root)
            continue
        for path in sorted(root.rglob('*.py')):
            discovered.extend(_scan_python_file(path, project_name, repo_root))
        for path in sorted(root.rglob('*.rs')):
            discovered.extend(_scan_rust_file(path, project_name, repo_root))
    return discovered


def _scan_python_file(path: Path, project_name: str, repo_root: Path) -> list[CodeReference]:
    try:
        text = path.read_text(encoding='utf8')
    except OSError as err:
        logger.warning('Unable to read Python file %s: %s', path, err)
        return []

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as err:
        logger.warning('Unable to parse Python file %s: %s', path, err)
        return []

    lines = text.splitlines()
    found: list[CodeReference] = []

    def visit(body: list[ast.stmt], parents: tuple[str, ...] = (), in_test_class: bool = False):
        for node in body:
            if isinstance(node, ast.ClassDef):
                symbol = '.'.join((*parents, node.name))
                annotations = _collect_python_annotations(node, lines)
                class_is_test = node.name.startswith('Test')
                found.extend(
                    _build_refs(
                        annotations,
                        'python',
                        path,
                        repo_root,
                        symbol,
                        node.lineno,
                        'pytest' if class_is_test else None,
                        class_is_test,
                    )
                )
                visit(node.body, (*parents, node.name), in_test_class=class_is_test)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbol = '.'.join((*parents, node.name))
                annotations = _collect_python_annotations(node, lines)
                is_test = node.name.startswith('test') or in_test_class
                found.extend(
                    _build_refs(
                        annotations,
                        'python',
                        path,
                        repo_root,
                        symbol,
                        node.lineno,
                        'pytest' if is_test else None,
                        is_test,
                    )
                )

    visit(tree.body)
    return [ref for ref in found if ref.project == project_name]


def _collect_python_annotations(node: ast.AST, lines: list[str]) -> list[str]:
    start_line = getattr(node, 'lineno', 1)
    decorator_lines = [getattr(decorator, 'lineno', start_line) for decorator in getattr(node, 'decorator_list', [])]
    block_start = min([start_line, *decorator_lines]) - 1

    comments: list[str] = []
    cursor = block_start - 1
    while cursor >= 0:
        line = lines[cursor].strip()
        if not line:
            break
        if not line.startswith('#'):
            break
        comments.append(line.removeprefix('#').strip())
        cursor -= 1
    comments.reverse()

    annotations = list(comments)
    docstring = ast.get_docstring(node, clean=False)
    if docstring:
        annotations.extend(docstring.splitlines())
    return annotations


def _scan_rust_file(path: Path, project_name: str, repo_root: Path) -> list[CodeReference]:
    try:
        lines = path.read_text(encoding='utf8').splitlines()
    except OSError as err:
        logger.warning('Unable to read Rust file %s: %s', path, err)
        return []

    found: list[CodeReference] = []
    pending_annotations: list[str] = []
    pending_test = False

    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            pending_annotations = []
            pending_test = False
            continue
        if line.startswith('///'):
            pending_annotations.append(line.removeprefix('///').strip())
            continue
        if line.startswith('//'):
            pending_annotations.append(line.removeprefix('//').strip())
            continue
        if line == '#[test]':
            pending_test = True
            continue
        match = RUST_FN_RE.search(line)
        if match:
            symbol = match.group('name')
            found.extend(
                _build_refs(
                    pending_annotations,
                    'rust',
                    path,
                    repo_root,
                    symbol,
                    idx + 1,
                    'rust-test' if pending_test else None,
                    pending_test,
                )
            )
        pending_annotations = []
        pending_test = False

    return [ref for ref in found if ref.project == project_name]


def _build_refs(
    annotations: list[str],
    language: str,
    path: Path,
    repo_root: Path,
    symbol: str,
    line: int,
    framework: str | None,
    is_executable_test: bool,
) -> list[CodeReference]:
    refs: list[CodeReference] = []
    relative_path = str(path.relative_to(repo_root)) if path.is_relative_to(repo_root) else str(path)
    for annotation in annotations:
        for match in ANNOTATION_RE.finditer(annotation):
            refs.append(
                CodeReference(
                    project=match.group('project'),
                    target_id=match.group('id'),
                    language=language,
                    path=relative_path,
                    symbol=symbol,
                    line=line,
                    framework=framework,
                    is_executable_test=is_executable_test,
                )
            )
    return refs
