# Development Guide

## Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install uv if needed
# https://docs.astral.sh/uv/getting-started/installation/
curl -LsSf https://astral.sh/uv/install.sh | sh
# or build from source
cargo install --locked uv
# Trust no registry
cargo install --git https://github.com/astral-sh/uv --tag 0.10.2 uv --locked

# Install dependencies
uv sync
```

## Testing

Run tests with the correct import mode:

```bash
# Run all tests (as used in CI)
uv run pytest --import-mode importlib --quiet

# Run specific test file
uv run pytest --import-mode importlib tests/test_nominal.py
```

## Code Quality

### Format Code

```bash
# Format Python code
uv run --dev ruff format python tests

# Check formatting without making changes
uv run --dev ruff format --check python tests
```

### Lint Code

```bash
# Run linter
uv run --dev ruff check python tests

# Auto-fix issues where possible
uv run --dev ruff check --fix python tests
```

## Running Speky CLI

### Validate Specifications

```bash
# Validate YAML files without generating output
uv run speky specs/*.yaml --project-name "My Project" --check-only

# Validate using the Makefile
make -C specs check
```

### Generate HTML Output

```bash
# Generate Myst Markdown
uv run speky requirements.yaml tests.yaml comments.yaml \
  --output-folder markdown \
  --project-name "My Project"

# Generate HTML with Sphinx (requires sphinx installation)
uv run --with furo,sphinx-design,sphinx-copybutton,myst-parser \
  sphinx-build -M html markdown output --conf-dir .
```

### Generate PDF Output

Requires [Typst](https://github.com/typst/typst) >= 0.13.0

```bash
# Install Speky Typst package locally
make -C typst

# Compile PDF
typst compile specification.typ
```

## MCP Server

The MCP server is under development.

```bash
# Install as a tool
uv tool install git+https://github.com/agagniere/speky#master

# Run MCP server
speky-mcp requirements.yaml tests.yaml comments.yaml
```

## Project Structure

```
python/speky/
├── __init__.py
├── __main__.py
├── main.py           # CLI entry point
├── specification.py  # Core Specification class
├── models.py         # Data models (Requirement, Test, Comment)
├── utils.py          # Helper functions
└── generators/       # Output generators
    └── markdown.py
```

## Workflow

1. Make changes to code
2. Format: `uv run --dev ruff format python tests`
3. Lint: `uv run --dev ruff check python tests`
4. Test: `uv run pytest --import-mode importlib --quiet`
5. Commit changes

## CI/CD

The GitHub Actions workflow automatically runs:
- YAML validation
- Code formatting check
- Linting
- Tests

See `.github/workflows/check.yaml` for details.
