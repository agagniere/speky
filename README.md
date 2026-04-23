# Speky: Specifications in YAML/TOML

![logo](sphinx/assets/Speky-256.png)

Write your requirements and functional tests in a textual format to easily version it with Git,
then generate a PDF and a static website.

## Roadmap
- [x] PDF with all relevant cross references
- [x] Static website
- [ ] Differential PDF to see what changed since last version
- [x] Coverage report to see in a glimpse how much of your requirements are tested
- [x] MCP server for LLMs to discover and query your spec
- [x] Claude plugin to help onboard new projects, or write test plans

## Generate a static website

Requires [uv](https://github.com/astral-sh/uv) >= 0.8.0

1. Install speky
   ```shell
   uv tool install git+https://github.com/agagniere/speky#master
   ```
1. Create a manifest listing your spec files:
   ```yaml
   # speky.yaml
   kind: project
   name: my-project
   files:
     - requirements.yaml
     - tests.yaml
     - comments/*.yaml
   ```
1. Generate MyST Markdown:
   ```shell
   speky speky.yaml --output-folder markdown
   ```
1. Configure Sphinx:
   ```python
   # conf.py
   project    = 'My Project'
   language   = 'en'
   extensions = [ 'myst_parser', 'sphinx_design' ]
   html_theme = 'furo'
   myst_enable_extensions = [ 'colon_fence', 'substitution' ]
   myst_substitutions     = {'project': project}
   ```
1. Generate HTML with Sphinx:
   ```shell
   uv tool install sphinx --with furo,sphinx-design,sphinx-copybutton,myst-parser
   sphinx-build -M html markdown sphinx --conf-dir .
   ```
1. Open the website in a browser
   ```shell
   open sphinx/html/index.html
   ```

## Generate a PDF

Requires [Typst](https://github.com/typst/typst) >= 0.13.0

### Install locally

```shell
SPEKYTMP=$(mktemp -d)
git clone https://github.com/agagniere/speky $SPEKYTMP --depth=1
make -C $SPEKYTMP/typst PACKAGE_VERSION=0.3.0
rm -rf $SPEKYTMP
```

### Use from typst

```typst
#import "@local/speky:0.3.0": speky

#speky((
  "requirements.yaml",
  "tests.yaml",
  "comments.yaml",
).map(yaml))
```

## Use with Claude Code

Requires [uv](https://github.com/astral-sh/uv).

### 1. Install the plugin

The plugin adds workflow skills and two MCP servers.

```shell
# Share with everyone in the repo (both commands need the same scope)
claude plugin marketplace add agagniere/speky --scope project
claude plugin install speky@speky --scope project

# Or just for yourself
claude plugin marketplace add agagniere/speky --scope user
claude plugin install speky@speky --scope user
```

The plugin registers two MCP servers automatically:
- **`speky`** — queries your project's specification
- **`speky-selfspec`** — queries Speky's own spec, available as a reference at any time

### 2. First time?

If you don't have a specification yet, the `speky` MCP server will fail to start — the manifest doesn't exist yet. That's expected. Run `/speky:init` in Claude Code: it will guide you through writing your first requirements and creating the manifest. Then restart the `speky` MCP server via `/mcp`.

## Use with other MCP clients

Requires [uv](https://github.com/astral-sh/uv). Add to your client's config:

```json
{
  "mcpServers": {
    "speky": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/agagniere/speky", "speky-mcp", "speky.yaml"]
    }
  }
}
```

Replace `speky.yaml` with the path to your manifest, or list individual YAML/TOML specification files.

## Used by

![safran](https://upload.wikimedia.org/wikipedia/fr/thumb/5/5f/Safran_-_logo_2016.png/330px-Safran_-_logo_2016.png)

## AI usage disclosure

Written 100% by hand (without even a language server):
- Speky's specification
- The PDF generation in typst
- Python CLI (spec checker, markdown generation, common code reused by the MCP server, ...)
- Tests and spec samples
- This README.md
- Makefiles, the Yamale schema, pyproject.toml, ...

Written with LLM assistance:
- MCP server specification, implementation and related tests
- [DEVELOPMENT.md](DEVELOPMENT.md), [MCP.md](MCP.md), [AGENTS.md](AGENTS.md)
- All files in [.claude-plugin](.claude-plugin), [skills](skills)
- `python/speky/scanner.py`
