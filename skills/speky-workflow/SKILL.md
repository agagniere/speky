---
name: speky-workflow
description: Guidelines for working with Speky requirements and tests via the speky MCP server tools
when_to_use: When working with requirements, tests, specifications, or using any speky MCP tools (get_requirement, get_test, search_requirements, search_tests, list_all_ids, list_all_tags, list_references_to, test_plan_coverage)
user-invocable: false
---

# Speky Workflow Guidelines

Speky organizes a project's detailed specification into **requirements** (what the system must do) and **tests** (how to verify it). Items are identified by short IDs like `RF01`, `RNF02`, `T03`.

## Tool selection

- Start with `list_all_ids` to get a full overview of available IDs before searching or fetching.
- Use `get_requirement` / `get_test` when you already know the ID — it's faster and returns full detail including cross-references.
- Use `search_requirements` only when filtering by tag or category. Use `search_tests` only when filtering by category or by requirement (`tester_of`). Do not call either with no filters as a substitute for `list_all_ids`.
- Use `list_all_tags` to discover available tags before filtering by one.
- Use `list_references_to` to find what depends on a given item (e.g., before modifying or deleting it).
- Use `test_plan_coverage` to find coverage gaps — it gives a project-wide summary without requiring manual inspection.

## Reading results

- `get_requirement` returns `tested_by` (tests covering it) and `referenced_by` (requirements that depend on it). Read these before assessing coverage or impact.
- `get_test` returns `ref` (requirements it validates) and `prereq` (tests that must run first). Read these to understand test scope and ordering.
- Tags use a namespaced format: `namespace:value` (e.g., `output:pdf`, `mcp:tools`). When filtering by tag, use the exact full string.

## Working with coverage

- A requirement is covered if it appears in at least one test's `ref` list (visible as `tested_by` on the requirement).
- Use `test_plan_coverage` for a project-wide summary before concluding anything about overall coverage.
- Do not infer coverage from description alone — always check `tested_by`.

## Writing test plans

- Think about prerequisites first: "how to reach a state where the feature can be tested simply?" Structure tests so that later tests can build on the final state of earlier ones, using the `prereq` field rather than repeating setup steps.
- Be as specific as possible: include relevant excerpts of inputs and outputs as `sample` fields on steps.
- `expected` is only for listing (an excerpt of) the output of a `run` command. Do not use it for steps that have no `run`.

## Building a new feature

Follow this order strictly:
1. Write the requirements in Speky YAML
2. Write the test plan (Speky functional tests)
3. Implement the tests as executable code where possible
4. Write the implementation until the tests pass

## Requirement categories

Category is a free-form field, but four values cover most cases:

| Category | Intent | Test plan |
|---|---|---|
| `functional` | User-facing behavior: "The user shall be able to …" | Primary focus of test plans |
| `non-functional` | System-level constraint: "The system shall … (e.g. handle 100k tps, respond in < 1ms)" | Test if measurable, otherwise document |
| `architecture` | Represents an architectural decision | Not tested |
| `definition` | Defines a project-specific term, referenced from other requirements to avoid duplication | Not tested |

When writing requirements, pick the category that reflects the *intent*, not just the wording.

## Adding or modifying specifications

- Requirements and tests are defined in YAML or TOML files, which can be placed anywhere, usually under `specs/`.
- The manifest (`specs/speky.yaml` or similar) lists which files to load — new files must be referenced there.
- After editing spec files, the MCP server must be restarted to pick up changes (it loads specs at startup).
- IDs must be unique across the entire loaded specification set.
