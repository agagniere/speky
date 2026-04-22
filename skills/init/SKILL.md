---
name: write-specs
description: Interactive workflow for writing Speky specifications (requirements + test plan) for an existing project
user-invocable: true
disable-model-invocation: false
argument-hint: "[path to project root, defaults to current directory]"
---

You are helping the user write a formal Speky specification for an existing project. This skill is typically run just after installing the Speky plugin — at that point the `speky` MCP server may be failing because the manifest file doesn't exist yet. That is expected; completing this skill will create the manifest and fix it.

Follow these steps in order, waiting for user input where indicated.

## Step 1 — Identify relevant files

Explore the project at $ARGUMENTS (or the current directory if not provided).

Identify files that reveal intent, behavior, or constraints:
- Source code (focus on public interfaces, entry points, core logic — not boilerplate)
- Existing documentation (README, docs/, wikis)
- Configuration files that define behavior
- Tests (they often describe expected behavior explicitly)
- Changelogs or ADRs if present

## Step 2 — Write a file index

Write a temporary file at `/tmp/speky-index-${CLAUDE_SESSION_ID}.md` with the following structure:

```markdown
# Project File Index

## Source files
| File | Summary |
|------|---------|
| `path/to/file.py` | One-line description of what behavior/feature it contains |
...

## Documentation
| File | Summary |
|------|---------|
...

## Tests
| File | Summary |
|------|---------|
...
```

Include the full relative path for every file — it will be used later to trace requirements back to source. Omit files with no behavioral content (lockfiles, assets, generated code, etc.).

Tell the user the index has been written to `/tmp/speky-index-${CLAUDE_SESSION_ID}.md`.

## Step 3 — Ask for external sources

Ask the user:

> "Are there any external sources of requirements or specifications I should consider? (e.g. a product brief, a standards document, a public API spec, a user story map — please share URLs or file paths)"

If the user provides sources:
- Fetch or read each one
- Write a temporary file at `/tmp/speky-sources-${CLAUDE_SESSION_ID}.md`:

```markdown
# External Sources

## [Document title](URL or path)
### [Section name](URL#anchor or path:line)
One-paragraph summary of what requirements or constraints this section implies.

### [Next section](...)
...
```

Include the URL or file path for every section — it will be used to justify requirements. Tell the user this file has been written.

If the user has no external sources, continue to the next step.

## Step 4 — Propose requirements and iterate

Using the file index and external sources, draft a list of requirements. For each requirement, write:

```
[ID draft] [category] — Short title
  > Long description
  > Source: `path/to/file.py` or [Section](URL)
```

Choose the category that reflects the *intent*:
- `functional` — user-facing behavior ("The user shall be able to …"). These are the main focus of test plans.
- `non-functional` — system-level constraint ("The system shall …", e.g. performance, reliability).
- `architecture` — an architectural decision. Not tested.
- `definition` — defines a project-specific term referenced from other requirements. Not tested.

Also look for implicit definitions and architectural decisions in the code — not just functional behaviors. They deserve their own requirements too.

**Writing good requirements:** A requirement should be precise enough to be unambiguous, but silent on how it is implemented. For functional requirements in particular, describe what the user does to trigger the behavior and what observable effect results — not what happens inside the system.

Group them by theme. Present the full list to the user and ask:

> "Does this list look right? What should be added, removed, rephrased, or split?"

Iterate — revise the list based on feedback — until the user is satisfied.

## Step 5 — Save as a plan

Once the user approves the list, write the final requirements as a plan file at `/tmp/speky-plan-${CLAUDE_SESSION_ID}.md`:

```markdown
# Requirements Plan

## [Theme name]

### [ID draft] — [Short title]
- **Category:** functional | non-functional | architecture | definition
- **Description:** Full requirement text
- **Source:** `path/to/file` or [Section title](URL)

...
```

Tell the user the plan has been saved to `/tmp/speky-plan-${CLAUDE_SESSION_ID}.md`, then continue with the steps below.

## Step 6 — Write and validate the first requirement

See `tests/samples/more_requirements.toml` in speky repo for the format,
and the `sample-req.toml` file bundled in this skill for an example of a good functional requirement.

Requirements from the plan where short summaries, now you can go in more details on what user actions are expected and about observable effects.

For requirements that are rephrased from an existing requirement (not from code),
include the original requirement (or the most significant excerpt) in the `client_statement` field.

For requirements that come from a webpage, include the URL as a `source` field inside the `properties` of that requirement.

Use tags to allow readers to find a requirement from:
- its theme
- the associated system component
etc

Tags support one level of hierarchy to create sub-groups, e.g. `protocol`, `protocol:http`, `protocol:grpc`

Write a single functional requirement from the plan as a Speky TOML file and show it to the user. Ask:

> "Does this format and phrasing meet your expectations?"

Incorporate any feedback before proceeding. This first requirement sets the style for all the rest.

## Step 7 — Write all requirements

Write all remaining requirements as TOML files. Group them into files of roughly 4–10 requirements each, grouping by category, theme, or functional area. Use one file per group.

Refer to the index .md files created in previous steps to correctly source requirements.

## Step 8 — Write the manifest

Create a Speky manifest file at `${user_config.spec_folder}/${user_config.manifest_name}` listing all the requirement files written in the previous step.

## Step 9 — Validate

Run speky to validate the specification:

```bash
uvx --from git+https://github.com/agagniere/speky speky ${user_config.spec_folder}/${user_config.manifest_name} --check-only
```

Fix any validation errors before finishing.

## Step 10 — Commit

Stage and commit all new specification files:

```bash
git add ${user_config.spec_folder}/
git commit
```

Write a commit message that briefly describes what was specified (e.g. "Add initial Speky specification for <project or feature name>").

## Step 11 — Restart the MCP server

Tell the user to restart the `speky` MCP server so it picks up the new manifest. In Claude Code, this can be done with `/mcp` → select the server → restart.
