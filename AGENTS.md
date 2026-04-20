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
- `specification.py` — Loads YAML/TOML files and `kind: project` manifests, manages cross-references between items
- `models.py` — `Requirement`, `Test`, `Comment` data models
- `generators/markdown.py` — MyST Markdown output

### `speky_mcp` — MCP server
Exposes specs over JSON-RPC 2.0 to LLM clients (e.g., Claude).
- `server.py` — Startup, initialization, request dispatch
- `tools.py` — Tool implementations (search, get, list operations)
- `protocol.py` — JSON-RPC error types

**MCP tools available:** `get_requirement`, `get_test`, `search_requirements`, `search_tests`, `list_references_to`, `test_plan_coverage`, `list_all_tags`, `list_all_ids`

See `MCP.md` for detailed tool documentation and architecture.

### `typst/` — Typst PDF templates
The `@local/speky` Typst package for rendering specs as PDFs. Install with `make -C typst`.

### `specs/` — Speky's own specifications
The tool is itself specified using Speky files in `specs/`. Entry point is `specs/speky.yaml` (manifest). The MCP sub-project uses `specs/mcp/mcp.toml` (TOML manifest with `root_directory = ".."`). These serve as both documentation and integration test fixtures.

## Testing

- Tests live in `tests/` with YAML/TOML fixtures in `tests/samples/`
- `conftest.py` provides `simple_specs` (3 files) and `complex_specs` (6 files) fixtures; `tests/samples/more_samples.yaml` is a manifest covering all `simple_*` and `more_*` samples
- `--import-mode importlib` is required for all pytest invocations
- MCP server tests (`test_mcp_server.py`) are comprehensive functional tests; nominal tests (`test_nominal.py`, `test_mcp_nominal.py`) cover basic CLI/server startup behavior

## CI/CD

GitHub Actions (`.github/workflows/check.yaml`) runs YAML validation, format check, lint, and tests on every push.
