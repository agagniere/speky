from pathlib import Path

import pytest

from speky.project import load_specification
from speky.specification import Specification
from speky_mcp.server import handle_request


def write_demo_project(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / 'specs').mkdir()
    (root / 'src').mkdir()
    (root / 'tests').mkdir()

    (root / 'speky.toml').write_text(
        """\
[project]
name = "demo"
display_name = "Demo"

[[source]]
kind = "workspace"
root = "."
requirements = ["specs/requirements.yaml"]
tests = ["specs/tests.yaml"]
code_roots = ["tests", "src"]
""",
        encoding='utf8',
    )
    (root / 'specs' / 'requirements.yaml').write_text(
        """\
kind: requirements
category: functional
requirements:
- id: RF10
  short: Approved requirement
  long: Approved requirement
  properties:
    stage: approved
- id: RF11
  short: Unimplemented requirement
  long: Unimplemented requirement
  properties:
    stage: approved
""",
        encoding='utf8',
    )
    (root / 'specs' / 'tests.yaml').write_text(
        """\
kind: tests
category: functional
tests:
- id: T10
  short: Implemented test
  long: Executable proof
  ref: [RF10]
  properties:
    stage: implemented
  steps:
  - action: Run the implemented test
- id: T11
  short: Spec-only test
  long: Specification only
  ref: [RF11]
  properties:
    stage: approved
  steps:
  - action: Run the specification-only test
""",
        encoding='utf8',
    )
    (root / 'tests' / 'test_feature.py').write_text(
        '''\
# speky:demo#T10
def test_feature():
    """Implements the feature."""
    assert True
''',
        encoding='utf8',
    )
    (root / 'src' / 'feature.py').write_text(
        '''\
# speky:demo#RF10
def feature_entrypoint():
    return True

# speky:demo#T11
def speky_lookup():
    return "lookup"
''',
        encoding='utf8',
    )
    return root


def mcp_call(name: str, arguments: dict, specs: Specification) -> dict:
    request = {
        'jsonrpc': '2.0',
        'method': 'tools/call',
        'id': 1,
        'params': {'name': name, 'arguments': arguments},
    }
    response = handle_request(request, specs, initialized=True)
    assert 'result' in response
    return response['result']['structuredContent']


# speky:speky_mcp#TMCP043
def test_load_specification_from_local_manifest(tmp_path):
    project_root = write_demo_project(tmp_path)

    specs, display_name = load_specification(
        paths=[],
        comment_csvs=None,
        project_name='demo',
        manifest_path=None,
        cwd=project_root,
    )

    assert display_name == 'Demo'
    assert specs.project_name == 'demo'
    assert len(specs.code_tests_by_test['T10']) == 1
    code_test = specs.code_tests_by_test['T10'][0]
    assert code_test.path == 'tests/test_feature.py'
    assert code_test.symbol == 'test_feature'
    assert len(specs.requirements_covered_by_code_tests['RF10']) == 1
    assert specs.requirements_covered_by_code_tests['RF11'] == []
    assert [item.symbol for item in specs.code_references_by_item['RF10']] == ['feature_entrypoint']


def test_explicit_paths_reuse_local_manifest_context(tmp_path):
    project_root = write_demo_project(tmp_path)

    specs, display_name = load_specification(
        paths=[
            str(project_root / 'specs' / 'requirements.yaml'),
            str(project_root / 'specs' / 'tests.yaml'),
        ],
        comment_csvs=None,
        project_name=None,
        manifest_path=None,
        cwd=project_root,
    )

    assert display_name == 'Demo'
    assert specs.project_name == 'demo'
    assert [item.symbol for item in specs.code_tests_by_test['T10']] == ['test_feature']


def test_load_specification_from_manifest_search_path(tmp_path, monkeypatch):
    project_root = write_demo_project(tmp_path / 'demo-project')
    working_dir = tmp_path / 'scratch'
    working_dir.mkdir()
    monkeypatch.setenv('SPEKY_PROJECTS_PATH', str(tmp_path))

    specs, _ = load_specification(
        paths=[],
        comment_csvs=None,
        project_name='demo',
        manifest_path=None,
        cwd=working_dir,
    )

    assert specs.by_id['RF10'].stage == 'approved'
    assert specs.by_id['T10'].stage == 'implemented'


def test_invalid_stage_raises(tmp_path):
    invalid_spec = tmp_path / 'invalid.yaml'
    invalid_spec.write_text(
        """\
kind: requirements
category: functional
requirements:
- id: RF99
  long: Invalid stage
  properties:
    stage: released
""",
        encoding='utf8',
    )

    specs = Specification()
    with pytest.raises(KeyError):
        specs.read_yaml(str(invalid_spec))


def load_demo_specs(tmp_path: Path) -> Specification:
    project_root = write_demo_project(tmp_path)
    specs, _ = load_specification(
        paths=[],
        comment_csvs=None,
        project_name='demo',
        manifest_path=None,
        cwd=project_root,
    )
    specs.check_references()
    return specs


# speky:speky_mcp#TMCP045
# speky:speky_mcp#TMCP051
def test_get_requirement_includes_stage_and_code_mentions(tmp_path):
    specs = load_demo_specs(tmp_path)

    requirement = mcp_call('get_requirement', {'id': 'RF10'}, specs)
    assert requirement['stage'] == 'approved'
    assert requirement['mentioned_in_code_by'][0]['path'] == 'src/feature.py'


# speky:speky_mcp#TMCP046
def test_get_test_includes_stage_and_code_tests(tmp_path):
    specs = load_demo_specs(tmp_path)

    test = mcp_call('get_test', {'id': 'T10'}, specs)
    assert test['stage'] == 'implemented'
    assert test['code_tests'][0]['symbol'] == 'test_feature'


# speky:speky_mcp#TMCP050
def test_get_test_includes_generic_code_mentions_without_duplication(tmp_path):
    specs = load_demo_specs(tmp_path)

    generic_test = mcp_call('get_test', {'id': 'T11'}, specs)
    assert generic_test['mentioned_in_code_by'][0]['symbol'] == 'speky_lookup'

    executable_test = mcp_call('get_test', {'id': 'T10'}, specs)
    assert 'mentioned_in_code_by' not in executable_test


# speky:speky_mcp#TMCP044
def test_search_requirements_filters_by_stage(tmp_path):
    specs = load_demo_specs(tmp_path)

    approved_requirements = mcp_call('search_requirements', {'stage': 'approved'}, specs)
    assert [item['id'] for item in approved_requirements['requirements']] == ['RF10', 'RF11']
    assert all(item['stage'] == 'approved' for item in approved_requirements['requirements'])


# speky:speky_mcp#TMCP049
def test_search_tests_filters_by_stage(tmp_path):
    specs = load_demo_specs(tmp_path)

    implemented_tests = mcp_call('search_tests', {'stage': 'implemented'}, specs)
    assert [item['id'] for item in implemented_tests['tests']] == ['T10']
    assert implemented_tests['tests'][0]['stage'] == 'implemented'


# speky:speky_mcp#TMCP047
def test_list_tests_without_code_tests(tmp_path):
    specs = load_demo_specs(tmp_path)

    uncovered_tests = mcp_call('list_tests_without_code_tests', {}, specs)
    assert [item['id'] for item in uncovered_tests['tests']] == ['T11']


# speky:speky_mcp#TMCP048
def test_list_requirements_without_code_tests(tmp_path):
    specs = load_demo_specs(tmp_path)

    uncovered_requirements = mcp_call('list_requirements_without_code_tests', {}, specs)
    assert [item['id'] for item in uncovered_requirements['requirements']] == ['RF11']
