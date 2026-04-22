---
name: write-test-plans
description: Interactive workflow for writing new Speky test plans for requirements lacking coverage, guided by the Speky MCP server
user-invocable: true
argument-hint: "[area of interest, e.g. 'search', 'authentication', 'file output']"
---

You are helping the user expand their project's test plan coverage for a specific area. Follow these steps in order.

## Step 1 — Identify the area of interest

If `$ARGUMENTS` is provided, use it as the area of interest (e.g. `"search"`, `"authentication"`, `"file output"`).

Otherwise ask the user:
> "What area or feature would you like to focus on? (e.g. a functional area, a component name, or a keyword)"

## Step 2 — Discover relevant tags

Call `list_all_tags` to retrieve all tags used in the specification.

From the returned list, select all tags that relate to the area of interest. Use the full tag string including namespace (e.g. `mcp:tools`, not just `tools`).

Tell the user which tags you selected and why, and ask them to confirm or adjust before continuing:
> "I identified these tags as relevant: `tag-a`, `tag-b`. Does that look right, or would you like to add or remove any?"

## Step 3 — Find requirements needing test plans

For each selected tag, call `least_tested_requirements` with that tag and `count: 3`. Merge and deduplicate the results across all tags, then sort by `test_plans` ascending (then `automated_test_plans` ascending). Keep the top 3.

Tell the user which requirements you will write test plans for, and wait for their approval before proceeding.

## Step 4 — Study each target requirement

For each target requirement, gather full context before designing anything:

1. Call `get_requirement` — read its `long` description, `tags`, `ref`, `referenced_by`, and `tested_by`. Note the `source_file` field: it tells you which spec file the requirement lives in, which determines where the test file will go.
2. For each ID in `ref` and `referenced_by`, call `get_requirement` to understand related requirements and shared context.
3. For each ID in `tested_by` (if any), call `get_test` to understand what is already tested — avoid designing scenarios that duplicate existing tests.

## Step 5 — Design new test scenarios

Using what you learned, design **2 to 5 new test scenarios** per requirement. Think across these angles:

- **Minimal happy path** — the simplest possible demonstration that the feature works as intended (doubles as documentation)
- **Complex happy path** — exercises the feature more completely, combining multiple inputs or options
- **Invalid inputs** — what happens when the user passes something wrong; verify the system handles it properly
- **Failure conditions** — external failures such as file not found, query error, missing dependency, or permission denied
- **Untested combinations** — input pairings or states that existing tests do not yet cover

For each scenario, determine the **initial state**:
- If it naturally starts from the final state of an existing test, list that test in `prereq`.
- If several new scenarios share the same non-trivial setup, consider writing one dedicated setup test and listing it as a `prereq` for all of them.
- If the initial state just requires specific tools or files to be present, describe that plainly in the `initial` field.

## Step 6 — Write the test files

For each target requirement `<ID>`:

1. Derive the test file path from `source_file`: take its parent directory, append `tests/`, and name the file `test_<ID>.toml`. For example, if `source_file` is `${user_config.spec_folder}/mcp/query.yaml`, write to `${user_config.spec_folder}/mcp/tests/test_MCP005.toml`; if it is `${user_config.spec_folder}/functional.yaml`, write to `${user_config.spec_folder}/tests/test_F012.toml`.
2. Write all new scenarios for that requirement into that single file.

Use TOML format:

```toml
kind = "tests"
category = "functional"  # match the category of the requirement

[[tests]]
id = "T<NNN>"
short = "Brief scenario title"
long = "What this scenario validates and why it is interesting"
ref = ["<ID>"]            # the requirement this test covers
prereq = ["T<previous>"]  # omit if not applicable
initial = """
- Tool X must be available
- File foo.yaml must exist in the current directory
"""

[[tests.steps]]
action = "Description of what the user does"
run = "shell command if applicable"
expected = "excerpt of expected output (only when a run command is present)"

[[tests.steps]]
action = "Next step"
sample_lang = "json"
sample = """
{"key": "value"}
"""
```

Assign IDs that continue from the highest existing test ID in the project. If unsure of the highest, call `list_all_ids` to check.

## Step 7 — Update the manifest

Open the project manifest at `${user_config.spec_folder}/${user_config.manifest_name}`.

Check whether it already includes a glob pattern that would match the new test files (e.g. `tests/*.toml` relative to the manifest). If not, add the appropriate pattern to the `files` list.

## Step 8 — Validate

Run speky on the manifest to validate the newly written tests:

```bash
uvx --from git+https://github.com/agagniere/speky speky <manifest-path> --check-only
```

Fix any validation errors before continuing.

## Step 9 — Commit

Stage and commit:

```bash
git add ${user_config.spec_folder}/
git commit
```

Write a commit message naming the requirements being covered, e.g. `"Add test plans for MCP005, MCP007"`.

## Step 10 — Restart MCP

Tell the user:

> "The new test plans have been committed. **Restart the `speky` MCP server** so it picks up the changes. In Claude Code, use `/mcp` → select the server → restart."
