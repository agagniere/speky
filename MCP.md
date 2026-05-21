# Speky MCP Server

The Speky MCP (Model Context Protocol) server exposes your project specifications to LLM agents like Claude Code, enabling them to query requirements, tests, and their relationships directly.

## Purpose

When working with Claude Code on a project that uses Speky specifications, the MCP server allows Claude to:
- Search and filter requirements by tag or category
- Query requirements and tests by ID
- Understand test coverage and requirement relationships
- Verify implementations against formal specifications
- Navigate between requirements, tests, and code

This creates a feedback loop where specifications inform code generation, and Claude can verify that implementations match the specs.

## Configuration

Requires [uv](https://github.com/astral-sh/uv).

### Configuring Claude Code

Install the Speky plugin — it registers the MCP server automatically:

```bash
# Share with everyone in the repo (both commands need the same scope)
claude plugin marketplace add agagniere/speky --scope project
claude plugin install speky@speky --scope project
```

The plugin expects specifications in `specs/` with a manifest at `specs/spec.yaml`. Run `/speky:init` to set this up.

**Additional options:**
- Add `-C path/to/comments.csv` to include CSV comment files not covered by the manifest
- Add `-l path/to/logging.yaml` for custom logging configuration

## Available Tools

### `get_requirement`

Query a requirement by ID.

**Arguments:**
- `id` (string): The requirement ID (e.g., "RF01")

**Returns:**
- `id`, `category`, `long`: Core requirement fields
- `short`: Short description (if present)
- `tags`: List of tags (if present)
- `client_statement`: User story (if present)
- `properties`: Custom properties dict (if present)
- `ref`: List of referenced requirements with `{id, short?}`
- `referenced_by`: List of requirements that reference this one with `{id, short?}`
- `tested_by`: List of tests covering this requirement with `{id, short?}`
- `comments`: List of comments with `{date, from, text, external}`
- `code_references`: List of pointers to source code locations associated with this requirement. Each entry has `{file, line, symbol?, url?}`. Populated from `speky:<name>#<ID>` tags found by scanning `code_sources`, and from declarative `code` entries on the requirement itself (see [Declaring code references from the spec](#declaring-code-references-from-the-spec)).

**Example:**
```json
{
  "name": "get_requirement",
  "arguments": {"id": "RF03"}
}
```

**Response:**
```json
{
  "structuredContent": {
    "id": "RF03",
    "category": "non-functional",
    "short": "Number 3",
    "long": "The third requirement !",
    "tags": ["foo", "bar:baz"],
    "tested_by": [
      {"id": "T03", "short": "Create files"},
      {"id": "T04", "short": "Yet another test"}
    ],
    "comments": [...],
    "code_references": [
      {"file": "src/foo.py", "line": 6, "symbol": "do_the_thing"},
      {"file": "src/bar.py", "line": 42}
    ]
  }
}
```

### `get_test`

Query a test by ID.

**Arguments:**
- `id` (string): The test ID (e.g., "T01")

**Returns:**
- `id`, `category`, `long`: Core test fields
- `short`: Short description (if present)
- `initial`: Initial state/prerequisites description (if present)
- `prereq`: List of prerequisite tests with `{id, short?}`
- `ref`: List of requirements tested by this test with `{id, short?}`
- `steps`: Array of test steps, each containing:
  - `action`: Description of the step
  - `run`: Shell command (if present)
  - `expected`: Expected outcome (if present)
  - `sample`: Sample code/output (if present)
  - `sample_lang`: Language of the sample (if present)
- `code_references`: List of pointers to source code locations associated with this test. Each entry has `{file, line, symbol?, is_test, url?}`. `is_test: true` flags the reference as an automated test implementation (used by `least_tested_requirements` and `test_plan_coverage` to count automated coverage). Populated from `speky:<name>#<ID>` tags found by scanning `code_sources`, and from declarative `code` entries on the test itself (see [Declaring code references from the spec](#declaring-code-references-from-the-spec)).

**Example:**
```json
{
  "name": "get_test",
  "arguments": {"id": "T04"}
}
```

**Response:**
```json
{
  "structuredContent": {
    "id": "T04",
    "category": "non-functional",
    "short": "Yet another test",
    "initial": "Requires ls and cat",
    "prereq": [{"id": "T03", "short": "Create files"}],
    "ref": [{"id": "RF03"}],
    "steps": [
      {
        "action": "Do that shell command",
        "run": "ls *secret*",
        "expected": "topsecret.txt"
      }
    ],
    "code_references": [
      {"file": "tests/test_feature.py", "line": 12, "symbol": "test_my_function", "is_test": true}
    ]
  }
}
```

### `search_requirements`

Search and filter requirements.

**Arguments** (all optional):
- `tag` (string): Filter by tag, exact match (e.g., `"security"` or `"output:pdf"`)
- `category` (string): Filter by category (e.g., `"functional"`)

If no arguments are provided, all requirements are returned. An error is returned if the tag or category does not exist.

**Returns:** `requirements` — a sorted list of matching requirement summaries, each with:
- `id`, `category`: Always present
- `short`: Short description (if present)
- `tags`: List of tags (if present)

**Examples:**
```json
{"name": "search_requirements", "arguments": {}}
{"name": "search_requirements", "arguments": {"tag": "security"}}
{"name": "search_requirements", "arguments": {"category": "functional"}}
{"name": "search_requirements", "arguments": {"tag": "output:pdf", "category": "functional"}}
```

**Response:**
```json
{
  "structuredContent": {
    "requirements": [
      {"category": "functional", "id": "RF01"},
      {"category": "functional", "id": "RF02", "short": "Second"},
      {"category": "non-functional", "id": "RF03", "short": "Number 3", "tags": ["foo", "bar:baz"]}
    ]
  }
}
```

### `search_tests`

Search and filter tests.

**Arguments** (all optional):
- `category` (string): Filter by category (e.g., `"functional"`). An error is returned if the category does not exist.
- `tester_of` (string): Filter by requirement ID — returns only tests that reference that requirement in their `ref` field. An error is returned if the requirement ID does not exist.

If no arguments are provided, all tests are returned. Filters can be combined.

**Returns:** `tests` — a sorted list of matching test summaries, each with:
- `id`, `category`: Always present
- `short`: Short description (if present)

**Examples:**
```json
{"name": "search_tests", "arguments": {}}
{"name": "search_tests", "arguments": {"category": "functional"}}
{"name": "search_tests", "arguments": {"tester_of": "RF03"}}
{"name": "search_tests", "arguments": {"category": "functional", "tester_of": "RF01"}}
```

**Response:**
```json
{
  "structuredContent": {
    "tests": [
      {"category": "non-functional", "id": "T03", "short": "Create files"},
      {"category": "non-functional", "id": "T04", "short": "Yet another test"}
    ]
  }
}
```

### `least_tested_requirements`

List all requirements ranked by ascending test coverage, with the least tested first.

**Arguments** (all optional):
- `tag` (string): Filter to requirements carrying this tag. An error is returned if the tag does not exist.
- `category` (string): Filter to a single category. An error is returned if the category does not exist.
- `count` (integer): Limit the number of results (e.g., `5` returns only the top 5). Negative or out-of-range values are ignored.

Both `tag` and `category` may be combined. If no arguments are provided, all requirements are returned.

**Sort order:**
1. Ascending total number of test plans (untested requirements come first)
2. Ascending number of automated test plans (fully manual before partially automated)
3. Alphabetically by ID as a tiebreaker

**Returns:** `requirements` — sorted list of requirement summaries, each with:
- `id`, `category`: Always present
- `short`: Short description (if present)
- `test_plans`: Total number of tests referencing this requirement
- `automated_test_plans`: Number of those tests with at least one automated code reference

**Example:**
```json
{"name": "least_tested_requirements", "arguments": {"count": 3}}
```

**Response:**
```json
{
  "structuredContent": {
    "requirements": [
      {"id": "RF04", "category": "non-functional", "test_plans": 0, "automated_test_plans": 0},
      {"id": "RF01", "category": "functional", "test_plans": 1, "automated_test_plans": 0},
      {"id": "RF02", "category": "functional", "short": "Second", "test_plans": 1, "automated_test_plans": 0}
    ]
  }
}
```

### `list_references_to`

List all requirements and tests that reference a given item.

**Arguments:**
- `id` (string): The requirement or test ID to look up

**Returns:** `requirements` — sorted list of items that have this ID in their `ref` field, each with:
- `id`, `category`: Always present
- `short`: Short description (if present)
- `tags`: List of tags (if present)

**Example:**
```json
{"name": "list_references_to", "arguments": {"id": "RF04"}}
```

**Response:**
```json
{
  "structuredContent": {
    "requirements": [
      {"category": "non-functional", "id": "RF03", "short": "Number 3", "tags": ["foo", "bar:baz"]}
    ]
  }
}
```

### `test_plan_coverage`

Partition requirements by test plan coverage status.

**Arguments** (all optional):
- `category` (string): Filter by category (e.g., `"functional"`). An error is returned if the category does not exist.

If no argument is provided, all requirements are included.

**Returns:** Four sorted lists of requirement summaries (each with `id`, `category`, and optionally `short` and `tags`):
- `no_test_plan`: Requirements with no associated tests
- `manual_test_plan`: Requirements covered only by manual tests
- `partially_manual_test_plan`: Requirements covered by a mix of manual and automated tests
- `automated_test_plan`: Requirements covered exclusively by automated tests

**Examples:**
```json
{"name": "test_plan_coverage", "arguments": {}}
{"name": "test_plan_coverage", "arguments": {"category": "functional"}}
```

**Response:**
```json
{
  "structuredContent": {
    "no_test_plan": [
      {"category": "functional", "id": "RF01"}
    ],
    "manual_test_plan": [],
    "partially_manual_test_plan": [
      {"category": "functional", "id": "RF02", "short": "Second"}
    ],
    "automated_test_plan": [
      {"category": "non-functional", "id": "RF03", "short": "Number 3", "tags": ["foo", "bar:baz"]}
    ]
  }
}
```

### `list_all_tags`

List all tags used across all loaded requirements.

**Arguments:** none

**Returns:** `tags` — sorted list of tag strings.

**Example response:**
```json
{
  "structuredContent": {
    "tags": ["bar:baz", "foo", "mcp:discovery", "mcp:tools"]
  }
}
```

### `list_all_ids`

List all requirement and test IDs in the loaded specifications.

**Arguments:** none

**Returns:**
- `requirements`: Sorted list of all requirement IDs
- `tests`: Sorted list of all test IDs

**Example response:**
```json
{
  "structuredContent": {
    "requirements": ["RF01", "RF02", "RF03", "RF04"],
    "tests": ["T01", "T02", "T03", "T04"]
  }
}
```

## Declaring code references from the spec

Code references can be sourced two ways:

1. **From source comments** — Speky scans files listed in the manifest's `code_sources` and harvests `speky:<name>#<ID>` tags from comments and docstrings (Python, Go, Rust, Bash).
2. **Declaratively from the spec** — A requirement or test can carry an optional `code` field listing pointers to source locations. No tag is needed in the source file.

Both sources feed the same `code_references` list returned by `get_requirement` and `get_test`.

**Declarative `code` field schema:**

Each entry accepts:
- `file` (required): path to the source file, relative to the manifest's `root_directory`.
- `symbol` (optional): function, class, or method name in that file. When set, Speky resolves it to a line number via tree-sitter and auto-detects whether it is a test (Python `test`/`Test` prefix, Go `Test` prefix, Rust `#[test]` attribute).
- `line` (optional): explicit 1-based line number. Takes precedence over symbol-based resolution. Defaults to 1 when neither `symbol` nor `line` is set.
- `is_test` (optional): override the auto-detected `is_test` flag.

**Resolution precedence:**
- `line`: explicit value > symbol-resolved line > `1`.
- `is_test`: explicit value > symbol-resolved test detection > file-name conventions (`test*.sh`, `*_test.go`) > `false`.

Speky logs a warning and skips the entry when `file` is missing or does not resolve to a real file. When `symbol` is provided but cannot be located in the file, Speky logs a warning and falls back to line 1 instead of erroring.

**Example (YAML):**
```yaml
- id: RF01
  long: The first requirement
  code:
    - file: src/foo.py
      symbol: do_the_thing
    - file: src/bar.py
      line: 42
```

**Example (TOML):**
```toml
[[requirements]]
id = "RF04"
long = "A requirement implemented in Python"
[[requirements.code]]
file = "more_source.py"
symbol = "another_function"
[[requirements.code]]
file = "more_source.py"
line = 1
```

The same `code` field is accepted on entries in `kind: tests` files.

## Usage Examples

### Querying Requirements

**User:** "What does requirement RF03 specify?"

Claude will use `get_requirement` to retrieve the full requirement details including description, tags, and test coverage.

### Understanding Test Coverage

**User:** "Which tests cover the authentication requirements?"

Claude can:
1. Use `search_requirements` with `tag: "authentication"` to find relevant requirements
2. Read the `tested_by` field from each `get_requirement` response, or use `search_tests` with `tester_of` to query by requirement ID
3. Use `get_test` to understand what each test validates

### Finding Coverage Gaps

**User:** "Which requirements have no tests yet?"

Claude can use `test_plan_coverage` to get a project-wide coverage summary partitioned into four buckets, or `least_tested_requirements` to get a ranked list sorted from least to most covered — useful for prioritizing where to write test plans next.

### Verifying Implementation

**User:** "Does this code implement requirement RF05 correctly?"

Claude can:
1. Use `get_requirement` to understand what RF05 specifies
2. Review the code against the requirement
3. Check if tests exist via `tested_by` field
4. Suggest improvements or identify gaps

## Architecture

### Server Lifecycle

1. **Startup**: Load and validate all YAML/TOML specification files (or a manifest that references them)
2. **Initialization**: Handle MCP protocol initialization handshake
3. **Request Loop**: Process tool calls over stdin/stdout using JSON-RPC 2.0
4. **Shutdown**: Clean exit on stdin close

### Data Model

The server loads specifications into memory once at startup:

- **Requirements** indexed by ID with bidirectional references
- **Tests** indexed by ID with prerequisite chains
- **Comments** associated with requirements/tests
- **Tags** for categorization and search
- **Cross-references** validated at load time

### Error Handling

**Tool Execution Errors** (for invalid queries):
```json
{
  "isError": true,
  "structuredContent": {
    "error": "Requirement RF99 not found"
  }
}
```

**Protocol Errors** (for malformed requests):
```json
{
  "error": {
    "code": -32601,
    "message": "Method not found: unknown_method"
  }
}
```

## Development

### Adding a New Tool

1. **Define the specification** in `specs/mcp/` following the pattern of existing spec files
2. **Implement the handler** in `python/speky_mcp/tools.py`:
   ```python
   def handle_my_tool(arguments: dict, specs: Specification) -> dict:
       """speky:speky_mcp#MCP00X"""
       # Implementation — raise ToolError for domain-level errors
       return {'key': value}
   ```
3. **Register the tool** in the `TOOLS` dict at the bottom of `tools.py`:
   ```python
   TOOLS: dict[str, Callable] = {
       ...
       'my_tool': handle_my_tool,
   }
   ```
4. **Write tests** in `tests/test_mcp_server.py` using `handle_request()` directly
5. **Update this documentation** with the new tool's arguments and return format

### Testing

**Run all tests:**
```bash
uv run pytest tests/test_mcp_server.py --import-mode importlib -v
```

**Manual testing:**
```bash
printf '%s\n%s\n%s\n' \
  '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{}},"id":1}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_requirement","arguments":{"id":"RF01"}},"id":2}' \
| uv run speky-mcp tests/samples/more_samples.yaml | jq
```

### Code Quality

**Format:**
```bash
uv run --dev ruff format python/speky_mcp
```

**Lint:**
```bash
uv run --dev ruff check python/speky_mcp
```
