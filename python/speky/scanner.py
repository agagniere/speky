"""
speky:speky#SF016

Scan source files for speky reference tags in comments and docstrings.

Tags of the form `speky:<project>#<ID>` are extracted from:
- Comments immediately before a named symbol (function/class/method) → symbol reference
- Docstrings (Python) at the start of a function or class body → symbol reference
- Any other comment → free reference (file:line only, no symbol)

Tags in other project namespaces are silently ignored.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import tree_sitter_bash as tsbash
import tree_sitter_go as tsgo
import tree_sitter_python as tspython
import tree_sitter_rust as tsrust
from tree_sitter import Language, Node, Parser

if TYPE_CHECKING:
    from .models import Manifest

logger = logging.getLogger(__name__)

ANNOTATION_RE = re.compile(r'speky:(?P<project>[A-Za-z0-9_.-]+)#(?P<id>[A-Za-z0-9_-]+)')

_SH_LANG = Language(tsbash.language())
_PY_LANG = Language(tspython.language())
_GO_LANG = Language(tsgo.language())
_RS_LANG = Language(tsrust.language())

_COMMENT_TYPES: dict[str, frozenset[str]] = {
    '.sh': frozenset({'comment'}),
    '.py': frozenset({'comment'}),
    '.go': frozenset({'comment'}),
    '.rs': frozenset({'line_comment'}),
}

_SYMBOL_TYPES: dict[str, frozenset[str]] = {
    '.sh': frozenset({'function_definition'}),
    '.py': frozenset({'function_definition', 'class_definition', 'decorated_definition'}),
    '.go': frozenset({'function_declaration', 'method_declaration'}),
    '.rs': frozenset({'function_item'}),
}


@dataclass(order=True)
class CodeReference:
    """A speky tag found in source code."""

    project: str
    file: Path
    line: int
    target_id: str
    symbol: str | None  # None for free references (tag not adjacent to a named symbol)
    is_test: bool  # True if the associated symbol is a test function
    url: str | None = field(default=None)  # clickable link to the source line, if source_links configured
    manifest: Manifest | None = field(default=None, compare=False)

    @property
    def filename(self) -> str:
        return str(self.file.relative_to(self.manifest.root_dir))


def scan_sources(sources: list[Path], project_names: set[str]) -> list[CodeReference]:
    """Scan a list of source files for speky tags."""
    refs: list[CodeReference] = []
    for source in sources:
        if source.is_file():
            refs.extend(_scan_file(source, project_names))
        elif source.is_dir():
            for path in sorted(source.rglob('*')):
                if path.suffix in _SCANNERS:
                    refs.extend(_scan_file(path, project_names))
        else:
            logger.warning('Code source not found: %s', source)
    return refs


def _scan_file(path: Path, project_names: set[str]) -> list[CodeReference]:
    scanner = _SCANNERS.get(path.suffix)
    if not scanner:
        return []
    try:
        source = path.read_bytes()
    except OSError as err:
        logger.warning('Cannot read %s: %s', path, err)
        return []
    return scanner(source, project_names, path)


def _scan_python(source: bytes, project_names: set[str], file: Path) -> list[CodeReference]:
    tree = Parser(_PY_LANG).parse(source)
    refs: list[CodeReference] = []
    _walk(tree.root_node, source, '.py', project_names, file, refs)
    _collect_python_docstrings(tree.root_node, source, project_names, file, refs)
    return refs


def _scan_go(source: bytes, project_names: set[str], file: Path) -> list[CodeReference]:
    tree = Parser(_GO_LANG).parse(source)
    refs: list[CodeReference] = []
    _walk(tree.root_node, source, '.go', project_names, file, refs)
    return refs


def _scan_rust(source: bytes, project_names: set[str], file: Path) -> list[CodeReference]:
    tree = Parser(_RS_LANG).parse(source)
    refs: list[CodeReference] = []
    _walk(tree.root_node, source, '.rs', project_names, file, refs)
    return refs


def _scan_bash(source: bytes, project_names: set[str], file: Path) -> list[CodeReference]:
    tree = Parser(_SH_LANG).parse(source)
    refs: list[CodeReference] = []
    _walk(tree.root_node, source, '.sh', project_names, file, refs)
    return refs


_SCANNERS = {
    '.sh': _scan_bash,
    '.py': _scan_python,
    '.go': _scan_go,
    '.rs': _scan_rust,
}


def _walk(node: Node, source: bytes, ext: str, project_names: set[str], file: Path, refs: list[CodeReference]):
    if node.type in _COMMENT_TYPES[ext]:
        text = _text(node, source)
        for m in ANNOTATION_RE.finditer(text):
            if m.group('project').lower() not in project_names:
                continue
            symbol, is_test, symbol_node = _following_symbol(node, source, ext)
            if ext == '.sh' and file.name.startswith('test'):
                is_test = True
            elif ext == '.go' and file.name.endswith('_test.go'):
                is_test = True
            line = (symbol_node.start_point[0] + 1) if symbol_node else (node.start_point[0] + 1)
            refs.append(
                CodeReference(
                    project=m.group('project').lower(),
                    target_id=m.group('id'),
                    file=file,
                    line=line,
                    symbol=symbol,
                    is_test=is_test,
                )
            )
        return  # don't recurse into comment text

    for child in node.children:
        _walk(child, source, ext, project_names, file, refs)


def _following_symbol(comment: Node, source: bytes, ext: str) -> tuple[str | None, bool, Node | None]:
    """Return (name, is_test, node) of the named symbol immediately after this comment, or (None, False, None)."""
    parent = comment.parent
    if not parent:
        return None, False, None

    siblings = parent.children
    idx = next((i for i, c in enumerate(siblings) if c.id == comment.id), -1)
    if idx < 0:
        return None, False, None

    for sibling in siblings[idx + 1 :]:
        if sibling.type in _COMMENT_TYPES[ext]:
            continue  # consecutive comments are still "adjacent"
        if sibling.type in _SYMBOL_TYPES[ext]:
            name = _symbol_name(sibling, source)
            return name, _is_test(sibling, siblings, idx + 1, source, ext, name), sibling
        break

    return None, False, None


def _symbol_name(node: Node, source: bytes) -> str | None:
    """Extract the identifier name from a function/class/method definition node."""
    for child in node.children:
        if child.type in ('identifier', 'field_identifier', 'word'):
            return _text(child, source)
        if child.type in ('function_definition', 'class_definition', 'function_item'):
            return _symbol_name(child, source)
    return None


def _is_test(symbol: Node, siblings: list[Node], symbol_idx: int, source: bytes, ext: str, name: str | None) -> bool:
    if ext == '.py':
        return bool(name and name.startswith(('test', 'Test')))
    if ext == '.go':
        return bool(name and name.startswith('Test'))
    if ext == '.rs':
        for sibling in reversed(siblings[:symbol_idx]):
            if sibling.type == 'attribute_item' and 'test' in _text(sibling, source):
                return True
            if sibling.type not in ('line_comment',):
                break
    return False


def _collect_python_docstrings(root: Node, source: bytes, project_names: set[str], file: Path, refs: list[CodeReference]):
    """Collect tags from Python docstrings (first string literal in a function/class/module body)."""
    if root.type in ('function_definition', 'class_definition'):
        body = next((c for c in root.children if c.type == 'block'), None)
        if body:
            first = next((c for c in body.children if c.is_named), None)
            if first and first.type == 'expression_statement':
                string = next((c for c in first.children if c.type == 'string'), None)
                if string:
                    text = _text(string, source)
                    name = _symbol_name(root, source)
                    is_test = bool(name and name.startswith(('test', 'Test')))
                    for m in ANNOTATION_RE.finditer(text):
                        if m.group('project').lower() in project_names:
                            refs.append(
                                CodeReference(
                                    project=m.group('project').lower(),
                                    target_id=m.group('id'),
                                    file=file,
                                    line=root.start_point[0] + 1,
                                    symbol=name,
                                    is_test=is_test,
                                )
                            )
    elif root.type == 'module':
        first = next((c for c in root.children if c.is_named), None)
        if first and first.type == 'expression_statement':
            string = next((c for c in first.children if c.type == 'string'), None)
            if string:
                text = _text(string, source)
                for m in ANNOTATION_RE.finditer(text):
                    if m.group('project') in project_names:
                        refs.append(
                            CodeReference(
                                project=m.group('project').lower(),
                                target_id=m.group('id'),
                                file=file,
                                line=string.start_point[0] + 1,
                                symbol=None,
                                is_test=False,
                            )
                        )

    for child in root.children:
        _collect_python_docstrings(child, source, project_names, file, refs)


def _text(node: Node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode('utf8', errors='replace')
