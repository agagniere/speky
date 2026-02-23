"""Tests for the MCP server implementation."""

from pathlib import Path

import pytest
from speky.specification import Specification
from speky_mcp.server import handle_request

SAMPLES_DIR = Path(__file__).parent / 'samples'


@pytest.fixture
def simple_specs():
    """Load simple test specifications."""
    specs = Specification()
    specs.read_yaml(str(SAMPLES_DIR / 'simple_requirements.yaml'))
    specs.read_yaml(str(SAMPLES_DIR / 'simple_tests.yaml'))
    specs.read_yaml(str(SAMPLES_DIR / 'simple_comments.yaml'))
    specs.check_references()
    return specs


@pytest.fixture
def complex_specs():
    """Load all test sample specifications."""
    specs = Specification()
    specs.read_yaml(str(SAMPLES_DIR / 'simple_requirements.yaml'))
    specs.read_yaml(str(SAMPLES_DIR / 'simple_tests.yaml'))
    specs.read_yaml(str(SAMPLES_DIR / 'simple_comments.yaml'))
    specs.read_yaml(str(SAMPLES_DIR / 'more_requirements.yaml'))
    specs.read_yaml(str(SAMPLES_DIR / 'more_tests.yaml'))
    specs.read_yaml(str(SAMPLES_DIR / 'more_comments.yaml'))
    specs.check_references()
    return specs


class TestInitialization:
    """Tests for MCP server initialization protocol."""

    def test_initialize(self, simple_specs):
        """Test server initialization protocol (TMCP003)."""
        # speky:speky_mcp#TMCP003
        request = {
            'jsonrpc': '2.0',
            'method': 'initialize',
            'id': 1,
            'params': {
                'protocolVersion': '2025-11-25',
                'capabilities': {},
            },
        }

        response = handle_request(request, simple_specs, initialized=False)

        assert response['jsonrpc'] == '2.0'
        assert response['id'] == 1
        assert 'result' in response
        assert response['result']['protocolVersion'] == '2025-11-25'
        assert 'capabilities' in response['result']
        assert 'serverInfo' in response['result']
        assert response['result']['serverInfo']['name'] == 'speky-mcp'

    def test_reject_before_initialization(self, simple_specs):
        """Test that server rejects calls before initialization."""
        # speky:speky_mcp#TMCP003
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'id': 1,
            'params': {
                'name': 'get_requirement',
                'arguments': {'id': 'RF01'},
            },
        }

        response = handle_request(request, simple_specs, initialized=False)

        assert 'error' in response
        assert response['error']['code'] == -32002
        assert 'not initialized' in response['error']['message'].lower()

    def test_method_not_found(self, simple_specs):
        """Test error for unknown method."""
        request = {
            'jsonrpc': '2.0',
            'method': 'unknown_method',
            'id': 1,
        }

        response = handle_request(request, simple_specs, initialized=True)

        assert 'error' in response
        assert response['error']['code'] == -32601
        assert 'not found' in response['error']['message'].lower()


class TestGetRequirement:
    """Tests for get_requirement tool."""

    def test_get_simple_requirement(self, simple_specs):
        """Test getting a simple requirement with comments and tested_by (TMCP004)."""
        # speky:speky_mcp#TMCP004
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'id': 2,
            'params': {
                'name': 'get_requirement',
                'arguments': {'id': 'RF01'},
            },
        }

        response = handle_request(request, simple_specs, initialized=True)

        assert response['jsonrpc'] == '2.0'
        assert response['id'] == 2
        assert 'result' in response
        assert 'structuredContent' in response['result']

        content = response['result']['structuredContent']

        # Verify required fields
        assert content['id'] == 'RF01'
        assert content['category'] == 'functional'
        assert content['long'] == 'The first requirement'

        # Verify tested_by
        assert 'tested_by' in content
        assert len(content['tested_by']) == 1
        assert content['tested_by'][0]['id'] == 'T01'

        # Verify comments
        assert 'comments' in content
        assert len(content['comments']) == 1
        comment = content['comments'][0]
        assert comment['from'] == 'Some Person'
        assert comment['date'] == '01/01/2025'
        assert comment['text'] == 'The first comment'
        assert comment['external'] is False

    def test_get_requirement_all_fields(self, complex_specs):
        """Test getting a requirement with all possible fields (TMCP005)."""
        # speky:speky_mcp#TMCP005
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'id': 3,
            'params': {
                'name': 'get_requirement',
                'arguments': {'id': 'RF03'},
            },
        }

        response = handle_request(request, complex_specs, initialized=True)

        content = response['result']['structuredContent']

        # Required fields
        assert content['id'] == 'RF03'
        assert content['category'] == 'non-functional'
        assert content['long'] == 'The third requirement !'

        # Optional fields
        assert content['short'] == 'Number 3'
        assert 'tags' in content
        assert 'foo' in content['tags']
        assert 'bar:baz' in content['tags']
        assert content['client_statement'] == 'I want a requirement will all fields'
        assert 'properties' in content
        assert content['properties']['author'] == 'Mr. Author'

        # References
        assert 'ref' in content
        assert len(content['ref']) == 1
        assert content['ref'][0]['id'] == 'RF04'

        assert 'referenced_by' in content
        assert len(content['referenced_by']) == 1
        assert content['referenced_by'][0]['id'] == 'RF04'

        # Tested by
        assert 'tested_by' in content
        assert len(content['tested_by']) == 2

        # Comments
        assert 'comments' in content
        assert len(content['comments']) == 3

    def test_get_requirement_not_found(self, simple_specs):
        """Test error when requirement ID doesn't exist (TMCP006)."""
        # speky:speky_mcp#TMCP006
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'id': 4,
            'params': {
                'name': 'get_requirement',
                'arguments': {'id': 'NOTFOUND'},
            },
        }

        response = handle_request(request, simple_specs, initialized=True)

        assert 'result' in response
        assert response['result']['isError'] is True
        assert 'error' in response['result']['structuredContent']
        error_msg = response['result']['structuredContent']['error']
        assert 'NOTFOUND' in error_msg
        assert 'not found' in error_msg

    def test_get_requirement_wrong_type(self, simple_specs):
        """Test error when ID is a test, not a requirement (TMCP006)."""
        # speky:speky_mcp#TMCP006
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'id': 5,
            'params': {
                'name': 'get_requirement',
                'arguments': {'id': 'T01'},
            },
        }

        response = handle_request(request, simple_specs, initialized=True)

        assert 'result' in response
        assert response['result']['isError'] is True
        assert 'error' in response['result']['structuredContent']
        error_msg = response['result']['structuredContent']['error']
        assert 'T01' in error_msg
        assert 'test' in error_msg


class TestGetTest:
    """Tests for get_test tool."""

    def test_get_simple_test(self, simple_specs):
        """Test getting a simple test with minimal fields (TMCP007)."""
        # speky:speky_mcp#TMCP007
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'id': 2,
            'params': {
                'name': 'get_test',
                'arguments': {'id': 'T01'},
            },
        }

        response = handle_request(request, simple_specs, initialized=True)

        assert response['jsonrpc'] == '2.0'
        assert response['id'] == 2
        assert 'result' in response
        assert 'structuredContent' in response['result']

        content = response['result']['structuredContent']

        # Verify required fields
        assert content['id'] == 'T01'
        assert content['category'] == 'functional'
        assert content['long'] == 'The first test, that validates the first requirement'

        # Verify ref
        assert 'ref' in content
        assert len(content['ref']) == 1
        assert content['ref'][0]['id'] == 'RF01'

        # Verify steps
        assert 'steps' in content
        assert len(content['steps']) == 1
        assert content['steps'][0]['action'] == 'The only step'

    def test_get_test_all_fields(self, complex_specs):
        """Test getting a test with all optional fields (TMCP008)."""
        # speky:speky_mcp#TMCP008
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'id': 2,
            'params': {
                'name': 'get_test',
                'arguments': {'id': 'T04'},
            },
        }

        response = handle_request(request, complex_specs, initialized=True)

        content = response['result']['structuredContent']

        # Required fields
        assert content['id'] == 'T04'
        assert content['category'] == 'non-functional'
        assert content['long'] == 'The third test, that validates the third requirement'

        # Optional fields
        assert content['short'] == 'Yet another test'
        assert content['initial'] == 'Requires ls and cat'

        # Prerequisites
        assert 'prereq' in content
        assert len(content['prereq']) == 1
        assert content['prereq'][0]['id'] == 'T03'

        # References
        assert 'ref' in content
        assert len(content['ref']) == 1
        assert content['ref'][0]['id'] == 'RF03'

        # Steps with various fields
        assert 'steps' in content
        assert len(content['steps']) > 0

    def test_get_test_not_found(self, simple_specs):
        """Test error when test ID doesn't exist (TMCP009)."""
        # speky:speky_mcp#TMCP009
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'id': 2,
            'params': {
                'name': 'get_test',
                'arguments': {'id': 'NOTFOUND'},
            },
        }

        response = handle_request(request, simple_specs, initialized=True)

        assert 'result' in response
        assert response['result']['isError'] is True
        assert 'error' in response['result']['structuredContent']
        error_msg = response['result']['structuredContent']['error']
        assert 'NOTFOUND' in error_msg
        assert 'not found' in error_msg

    def test_get_test_wrong_type(self, simple_specs):
        """Test error when ID is a requirement, not a test (TMCP010)."""
        # speky:speky_mcp#TMCP010
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'id': 2,
            'params': {
                'name': 'get_test',
                'arguments': {'id': 'RF01'},
            },
        }

        response = handle_request(request, simple_specs, initialized=True)

        assert 'result' in response
        assert response['result']['isError'] is True
        assert 'error' in response['result']['structuredContent']
        error_msg = response['result']['structuredContent']['error']
        assert 'RF01' in error_msg
        assert 'requirement' in error_msg


class TestSearchRequirements:
    """Tests for search_requirements tool."""

    def test_search_all(self, complex_specs):
        """Test searching with no filters returns all requirements (TMCP011)."""
        # speky:speky_mcp#TMCP011
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'id': 2,
            'params': {'name': 'search_requirements', 'arguments': {}},
        }

        response = handle_request(request, complex_specs, initialized=True)
        requirements = response['result']['structuredContent']['requirements']

        ids = [r['id'] for r in requirements]
        assert ids == ['RF01', 'RF02', 'RF03', 'RF04']
        assert all('category' in r for r in requirements)

    def test_search_by_tag(self, complex_specs):
        """Test filtering by tag (TMCP012)."""
        # speky:speky_mcp#TMCP012
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'id': 2,
            'params': {'name': 'search_requirements', 'arguments': {'tag': 'foo'}},
        }

        response = handle_request(request, complex_specs, initialized=True)
        requirements = response['result']['structuredContent']['requirements']

        assert len(requirements) == 1
        assert requirements[0]['id'] == 'RF03'
        assert requirements[0]['category'] == 'non-functional'
        assert requirements[0]['short'] == 'Number 3'
        assert 'foo' in requirements[0]['tags']
        assert 'RF04' not in [r['id'] for r in requirements]

    def test_search_by_namespaced_tag(self, complex_specs):
        """Test filtering by namespaced tag (TMCP013)."""
        # speky:speky_mcp#TMCP013
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'id': 2,
            'params': {'name': 'search_requirements', 'arguments': {'tag': 'bar:baz'}},
        }

        response = handle_request(request, complex_specs, initialized=True)
        requirements = response['result']['structuredContent']['requirements']

        assert len(requirements) == 1
        assert requirements[0]['id'] == 'RF03'

    def test_search_by_category(self, simple_specs):
        """Test filtering by category (TMCP014)."""
        # speky:speky_mcp#TMCP014
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'id': 2,
            'params': {'name': 'search_requirements', 'arguments': {'category': 'functional'}},
        }

        response = handle_request(request, simple_specs, initialized=True)
        requirements = response['result']['structuredContent']['requirements']

        assert len(requirements) == 2
        assert all(r['category'] == 'functional' for r in requirements)
        ids = [r['id'] for r in requirements]
        assert 'RF01' in ids
        assert 'RF02' in ids

    def test_search_no_matches(self, simple_specs):
        """Test searching with a tag that matches nothing (TMCP015)."""
        # speky:speky_mcp#TMCP015
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'id': 2,
            'params': {'name': 'search_requirements', 'arguments': {'tag': 'nonexistent'}},
        }

        response = handle_request(request, simple_specs, initialized=True)
        requirements = response['result']['structuredContent']['requirements']

        assert requirements == []
