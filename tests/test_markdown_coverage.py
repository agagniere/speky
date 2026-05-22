"""Tests for coverage_item and write_coverage_list in the markdown generator."""

from io import StringIO
from types import SimpleNamespace

from speky.generators.markdown import MarkdownWriter, coverage_item, write_coverage_list


class StubRequirement:
    folder = 'requirements'

    def __init__(self, req_id: str):
        self.id = req_id
        self.title = f'`{req_id}`'

    def __lt__(self, other):
        return self.id < other.id


def make_requirement(req_id: str) -> StubRequirement:
    return StubRequirement(req_id)


def make_test(test_id: str) -> SimpleNamespace:
    return SimpleNamespace(id=test_id)


def make_specs(tests_by_req: dict[str, list], automated_ids: set[str]):
    """Build a minimal specs stub for coverage_item tests."""
    testers_of = {req_id: [make_test(t) for t in test_ids] for req_id, test_ids in tests_by_req.items()}
    return SimpleNamespace(
        testers_of=testers_of,
        is_test_automated=lambda test_id: test_id in automated_ids,
    )


class TestCoverageItem:
    def test_no_tests_returns_link_only(self):
        req = make_requirement('RF01')
        specs = make_specs({}, set())
        result = coverage_item(req, specs)
        assert result == '[`RF01`](/requirements/RF01)'

    def test_single_automated_test(self):
        req = make_requirement('RF01')
        specs = make_specs({'RF01': ['T01']}, {'T01'})
        result = coverage_item(req, specs)
        assert '1 automated test plan' in result
        assert '`RF01`' in result

    def test_multiple_automated_tests(self):
        req = make_requirement('RF01')
        specs = make_specs({'RF01': ['T01', 'T02', 'T03']}, {'T01', 'T02', 'T03'})
        result = coverage_item(req, specs)
        assert '3 automated test plans' in result

    def test_single_manual_test(self):
        req = make_requirement('RF01')
        specs = make_specs({'RF01': ['T01']}, set())
        result = coverage_item(req, specs)
        assert '1 test plan' in result
        assert 'automated' not in result

    def test_multiple_manual_tests(self):
        req = make_requirement('RF01')
        specs = make_specs({'RF01': ['T01', 'T02']}, set())
        result = coverage_item(req, specs)
        assert '2 test plans' in result
        assert 'automated' not in result

    def test_partial_automation(self):
        req = make_requirement('RF01')
        specs = make_specs({'RF01': ['T01', 'T02', 'T03']}, {'T01', 'T02'})
        result = coverage_item(req, specs)
        assert '2/3 test plans automated' in result

    def test_singular_plan_word(self):
        req = make_requirement('RF01')
        specs = make_specs({'RF01': ['T01']}, {'T01'})
        assert 'test plan' in coverage_item(req, specs)
        assert 'test plans' not in coverage_item(req, specs)

    def test_plural_plan_word(self):
        req = make_requirement('RF01')
        specs = make_specs({'RF01': ['T01', 'T02']}, {'T01', 'T02'})
        assert 'test plans' in coverage_item(req, specs)


class TestWriteCoverageList:
    def _capture(self, items, specs):
        buf = StringIO()
        write_coverage_list(MarkdownWriter(buf), items, specs)
        return buf.getvalue()

    def test_empty_list_writes_nothing(self):
        specs = make_specs({}, set())
        assert self._capture([], specs) == ''

    def test_single_item_no_bullet(self):
        req = make_requirement('RF01')
        specs = make_specs({'RF01': ['T01']}, {'T01'})
        output = self._capture([req], specs)
        assert not output.startswith('-')
        assert '`RF01`' in output

    def test_multiple_items_with_bullets(self):
        reqs = [make_requirement('RF01'), make_requirement('RF02')]
        specs = make_specs({'RF01': ['T01'], 'RF02': ['T02']}, {'T01', 'T02'})
        output = self._capture(reqs, specs)
        lines = [line for line in output.splitlines() if line]
        assert all(line.startswith('- ') for line in lines)
        assert len(lines) == 2

    def test_multiple_items_sorted(self):
        reqs = [make_requirement('RF02'), make_requirement('RF01')]
        specs = make_specs({}, set())
        output = self._capture(reqs, specs)
        lines = [line for line in output.splitlines() if line]
        assert 'RF01' in lines[0]
        assert 'RF02' in lines[1]
