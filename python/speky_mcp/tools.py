"""MCP tool handlers for Speky specifications."""

from typing import Callable

from speky.specification import Specification

from .protocol import ToolError


def handle_get_requirement(arguments: dict, specs: Specification) -> dict:
    """speky:speky_mcp#MCP003"""
    requirement_id = arguments['id']

    # speky:speky_mcp#TMCP006
    if requirement_id not in specs.by_id:
        raise ToolError(f'Requirement {requirement_id} not found')

    requirement = specs.by_id[requirement_id]

    # speky:speky_mcp#TMCP006
    if requirement.kind != 'requirement':
        raise ToolError(f'{requirement_id} is a {requirement.kind}, not a requirement')

    content = {
        'category': requirement.category,
        'id': requirement.id,
        'long': requirement.long,
    }

    # speky:speky_mcp#TMCP005
    if requirement.short:
        content['short'] = requirement.short
    if requirement.tags:
        content['tags'] = requirement.tags
    if requirement.client_statement:
        content['client_statement'] = requirement.client_statement
    if requirement.properties:
        content['properties'] = requirement.properties
    if requirement.ref:
        content['ref'] = [
            referred.json_oneliner(False) for referred in sorted(map(specs.by_id.__getitem__, requirement.ref))
        ]
    if requirement_id in specs.references:
        content['referenced_by'] = [ref.json_oneliner(False) for ref in sorted(specs.references[requirement_id])]
    if requirement_id in specs.testers_of:
        content['tested_by'] = [test.json_oneliner(False) for test in sorted(specs.testers_of[requirement_id])]
    if requirement_id in specs.comments:
        content['comments'] = [
            {k: v for k, v in comment.__dict__.items() if k in ('date', 'external', 'from', 'text')}
            for comment in specs.comments[requirement_id]
        ]

    return content


def handle_get_test(arguments: dict, specs: Specification) -> dict:
    """speky:speky_mcp#MCP004"""
    test_id = arguments['id']

    # speky:speky_mcp#TMCP009
    if test_id not in specs.by_id:
        raise ToolError(f'Test {test_id} not found')

    test = specs.by_id[test_id]

    # speky:speky_mcp#TMCP010
    if test.kind != 'test':
        raise ToolError(f'{test_id} is a {test.kind}, not a test')

    content = {
        'category': test.category,
        'id': test.id,
        'long': test.long,
        'ref': [referred.json_oneliner(False) for referred in sorted(map(specs.by_id.__getitem__, test.ref))],
        'steps': test.steps,
    }

    # speky:speky_mcp#TMCP008
    if test.short:
        content['short'] = test.short
    if test.initial:
        content['initial'] = test.initial
    if test.prereq:
        content['prereq'] = [
            prereq_test.json_oneliner(False) for prereq_test in sorted(map(specs.by_id.__getitem__, test.prereq))
        ]

    return content


def handle_search_requirements(arguments: dict, specs: Specification) -> dict:
    """speky:speky_mcp#MCP005"""
    tag = arguments.get('tag')
    category = arguments.get('category')

    if tag and tag not in specs.tags:
        raise ToolError(f'Tag {tag!r} not found')
    if category and category not in specs.requirements:
        raise ToolError(f'Category {category!r} not found')

    # speky:speky_mcp#TMCP012
    # speky:speky_mcp#TMCP014
    if tag and category:
        by_tag = {r.id for r in specs.tags[tag]}
        candidates = [r for r in specs.requirements[category] if r.id in by_tag]
    elif tag:
        candidates = specs.tags[tag]
    elif category:
        candidates = specs.requirements[category]
    else:
        candidates = [r for reqs in specs.requirements.values() for r in reqs]

    # speky:speky_mcp#TMCP015
    requirements = sorted(
        (r.json_oneliner(True) for r in candidates),
        key=lambda r: r['id'],
    )
    return {'requirements': requirements}


def handle_list_testers_of(arguments: dict, specs: Specification) -> dict:
    """speky:speky_mcp#MCP006"""
    requirement_id = arguments['id']

    # speky:speky_mcp#TMCP019
    if requirement_id not in specs.by_id:
        raise ToolError(f'Requirement {requirement_id} not found')

    tests = [test.json_oneliner(True) for test in sorted(specs.testers_of[requirement_id])]
    return {'tests': tests}


def handle_list_references_to(arguments: dict, specs: Specification) -> dict:
    """speky:speky_mcp#MCP007"""
    requirement_id = arguments['id']

    # speky:speky_mcp#TMCP022
    if requirement_id not in specs.by_id:
        raise ToolError(f'Requirement {requirement_id} not found')

    requirements = [req.json_oneliner(True) for req in sorted(specs.references[requirement_id])]
    return {'requirements': requirements}


def handle_list_untested_requirements(arguments: dict, specs: Specification) -> dict:
    """speky:speky_mcp#MCP010"""
    category = arguments.get('category')

    if category and category not in specs.requirements:
        raise ToolError(f'Category {category!r} not found')

    candidates = specs.requirements[category] if category else [r for reqs in specs.requirements.values() for r in reqs]
    requirements = [r.json_oneliner(True) for r in sorted(r for r in candidates if r.id not in specs.testers_of)]
    return {'requirements': requirements}


def handle_search_tests(arguments: dict, specs: Specification) -> dict:
    """speky:speky_mcp#MCP011"""
    tester_of = arguments.get('tester_of')
    category = arguments.get('category')

    if tester_of and tester_of not in specs.by_id:
        raise ToolError(f'Requirement {tester_of!r} not found')
    if category and category not in specs.tests:
        raise ToolError(f'Category {category!r} not found')

    if tester_of and category:
        by_tester = {t.id for t in specs.testers_of[tester_of]}
        candidates = [t for t in specs.tests[category] if t.id in by_tester]
    elif tester_of:
        candidates = specs.testers_of[tester_of]
    elif category:
        candidates = specs.tests[category]
    else:
        candidates = [t for tests in specs.tests.values() for t in tests]

    tests = sorted((t.json_oneliner(False) for t in candidates), key=lambda t: t['id'])
    return {'tests': tests}


def handle_list_all_ids(arguments: dict, specs: Specification) -> dict:
    """speky:speky_mcp#MCP009"""
    return {
        'requirements': sorted(item.id for item in specs.by_id.values() if item.kind == 'requirement'),
        'tests': sorted(item.id for item in specs.by_id.values() if item.kind == 'test'),
    }


def handle_list_all_tags(arguments: dict, specs: Specification) -> dict:
    """speky:speky_mcp#MCP008"""
    return {'tags': sorted(specs.tags.keys())}


TOOLS: dict[str, Callable] = {
    'get_requirement': handle_get_requirement,
    'get_test': handle_get_test,
    'search_requirements': handle_search_requirements,
    'list_testers_of': handle_list_testers_of,
    'search_tests': handle_search_tests,
    'list_references_to': handle_list_references_to,
    'list_untested_requirements': handle_list_untested_requirements,
    'list_all_tags': handle_list_all_tags,
    'list_all_ids': handle_list_all_ids,
}
