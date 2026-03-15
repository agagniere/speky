from pathlib import Path

from speky.project import load_specification


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
  short: First requirement
  long: First requirement
""",
        encoding='utf8',
    )
    (root / 'specs' / 'tests.yaml').write_text(
        """\
kind: tests
category: functional
tests:
- id: T10
  short: First test
  long: First test
  ref: [RF10]
  steps:
  - action: Run the first test
""",
        encoding='utf8',
    )
    return root


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
    assert sorted(specs.by_id) == ['RF10', 'T10']


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
    assert sorted(specs.by_id) == ['RF10', 'T10']


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
    assert sorted(specs.by_id) == ['RF10', 'T10']
