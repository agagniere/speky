from pathlib import Path

import pytest

from speky.project import load_specification
from speky.specification import Specification
from speky_mcp.server import handle_request


def write_demo_project(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / 'specs').mkdir()
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
  short: Draft requirement
  long: Draft requirement
  properties:
    stage: draft
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
  long: Implemented test
  ref: [RF10]
  properties:
    stage: implemented
  steps:
  - action: Run the implemented test
- id: T11
  short: Review test
  long: Review test
  ref: [RF11]
  properties:
    stage: review
  steps:
  - action: Run the review test
""",
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
    assert sorted(specs.by_id) == ['RF10', 'RF11', 'T10', 'T11']


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
    assert sorted(specs.by_id) == ['RF10', 'RF11', 'T10', 'T11']


def test_load_specification_from_manifest_search_path(tmp_path, monkeypatch):
    project_root = write_demo_project(tmp_path / 'demo-project')
    working_dir = tmp_path / 'scratch'
    working_dir.mkdir()
    monkeypatch.setenv('SPEKY_PROJECTS_PATH', str(tmp_path))

    specs, display_name = load_specification(
        paths=[],
        comment_csvs=None,
        project_name='demo',
        manifest_path=None,
        cwd=working_dir,
    )

    assert display_name == 'Demo'
    assert sorted(specs.by_id) == ['RF10', 'RF11', 'T10', 'T11']
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


# speky:speky_mcp#TMCP044
def test_search_requirements_filters_by_stage(tmp_path):
    specs = load_demo_specs(tmp_path)

    approved = mcp_call('search_requirements', {'stage': 'approved'}, specs)
    assert [item['id'] for item in approved['requirements']] == ['RF10']
    assert approved['requirements'][0]['stage'] == 'approved'


# speky:speky_mcp#TMCP049
def test_search_tests_filters_by_stage(tmp_path):
    specs = load_demo_specs(tmp_path)

    implemented = mcp_call('search_tests', {'stage': 'implemented'}, specs)
    assert [item['id'] for item in implemented['tests']] == ['T10']
    assert implemented['tests'][0]['stage'] == 'implemented'


def test_get_requirement_includes_stage(tmp_path):
    specs = load_demo_specs(tmp_path)

    requirement = mcp_call('get_requirement', {'id': 'RF10'}, specs)
    assert requirement['stage'] == 'approved'


def test_get_test_includes_stage(tmp_path):
    specs = load_demo_specs(tmp_path)

    test = mcp_call('get_test', {'id': 'T10'}, specs)
    assert test['stage'] == 'implemented'
