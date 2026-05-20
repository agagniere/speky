# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Project Overview

**Speky** is a Python tool for writing project specifications (requirements and tests) in YAML or TOML, version-controlled alongside code. It generates static HTML (via Sphinx/MyST) and PDFs (via Typst), and exposes specs to LLM agents via an MCP server.

## Commands

**Setup:**
```bash
uv sync
```

**Run all tests:**
```bash
uv run pytest --import-mode importlib --quiet
```

**Run a single test:**
```bash
uv run pytest --import-mode importlib tests/test_mcp_server.py::TestInitialization::test_initialize -v
```

**Format and lint:**
```bash
uv run --dev ruff format python tests
uv run --dev ruff check python tests
uv run --dev ruff check --fix python tests
```

**Validate YAML specs:**
```bash
make -C specs check
```

**Generate Markdown and HTML from specs:**
```bash
uv run speky specs/speky.yaml --output-folder markdown
uv run --with furo,sphinx-design,sphinx-copybutton,myst-parser sphinx-build -M html markdown output --conf-dir .
```

Sphinx's `conf.py` must set `project`, include `'substitution'` in `myst_enable_extensions`, and set `myst_substitutions = {'project': project}`.

## Architecture

The project has two Python packages under `python/`:

### `speky` — CLI tool
- `main.py` — Argument parsing and orchestration
- `specification.py` — Loads YAML/TOML files and `kind: project` manifests, resolves cross-references, scans source code for `speky:<project>#<ID>` tags, computes test-plan coverage
- `models.py` — `Requirement`, `Test`, `Comment`, `Manifest`, `SourceLinkConfig` data models
- `scanner.py` — Tree-sitter based scanner extracting code references from Python/Go/Rust/Bash sources
- `generators/markdown.py` — MyST Markdown output
- `utils.py`, `log_formatter.py` — Field-import helpers and CLI log formatting
- `assets/` — Default `logging.yaml` config and `speky.css` copied into the generated Markdown folder

### `speky_mcp` — MCP server
Exposes specs over JSON-RPC 2.0 to LLM clients (e.g., Claude).
- `server.py` — Startup, initialization, request dispatch
- `tools.py` — Tool implementations (search, get, list operations)
- `protocol.py` — JSON-RPC error types

**MCP tools available:** `get_requirement`, `get_test`, `search_requirements`, `search_tests`, `list_references_to`, `test_plan_coverage`, `least_tested_requirements`, `list_all_tags`, `list_all_ids`

See `MCP.md` for detailed tool documentation and architecture.

### `typst/` — Typst PDF templates
The `@local/speky` Typst package for rendering specs as PDFs. Install with `make -C typst`.

### `specs/` — Speky's own specifications
The tool is itself specified using Speky files in `specs/`. Entry point is `specs/speky.yaml` (manifest). The MCP sub-project uses `specs/mcp/mcp.toml` (TOML manifest with `root_directory = ".."`). These serve as both documentation and integration test fixtures.

### `.claude-plugin/` and `claude_plugin/` — Claude Code plugin
A first-party Claude Code plugin shipped from this repo. `.claude-plugin/plugin.json` registers two MCP servers (`speky` for the consumer's project, `speky-selfspec` for Speky's own spec) and points at custom `skills` / `agents` directories under `claude_plugin/`.

`claude_plugin/skills/` provides three workflow skills consumed by Claude:
- `init/` — onboards a new project (manifest, sample requirements, Sphinx `conf.py`, Makefile)
- `speky-workflow/` — day-to-day workflow guidance, including test steps
- `write-test-plans/` — style guide and templates for authoring test plans

`claude_plugin/agents/` provides read-only subagents:
- `test-plan-author` — drafts a test plan TOML block for a requirement ID
- `requirement-reviewer` — reviews a draft or existing requirement against atomicity / testability / fit
- `test-plan-reviewer` — reviews a draft or existing test plan against step-style rules and downstream impact
- `code-test-reviewer` — reviews an automated test (unit/integration/e2e) against its Speky test plan, mapping each plan step to code assertions and flagging gaps

## Testing

- Tests live in `tests/` with YAML/TOML fixtures in `tests/samples/`
- `conftest.py` provides the generic `tests_folder` and `sample` fixtures. The MCP-specific `simple_specs` (3 files) and `complex_specs` (loaded via the `more_samples.yaml` manifest) fixtures are defined inside `tests/test_mcp_server.py`
- `tests/samples/more_samples.yaml` is a manifest covering all `simple_*` and `more_*` samples, including the `more_source.{py,go}` files used to exercise the code-reference scanner
- `--import-mode importlib` is required for all pytest invocations
- MCP server tests (`test_mcp_server.py`) are comprehensive functional tests; nominal tests (`test_nominal.py`, `test_mcp_nominal.py`) cover basic CLI/server startup behavior; `test_fail.py` exercises the `failing_samples/` fixtures

## CI/CD

GitHub Actions (`.github/workflows/check.yaml`) runs YAML validation, format check, lint, and tests on every push.
