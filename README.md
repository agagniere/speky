# Speky: Specifications in YAML/TOML

![logo](sphinx/assets/Speky-256.png)

Write your requirements and functional tests in a textual format to easily version it with Git,
then generate a PDF and a static website.

## Roadmap
- [x] PDF with all relevant cross references
- [x] Static website
- [ ] Differential PDF to see what changed since last version

## Generate a PDF

Requires [Typst](https://github.com/typst/typst) >= 0.13.0

The speky typst package will generate content from language-agnostic data, like YAML or TOML.

### Install locally

```shell
make -C typst
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

## Use with Claude Code

### 1. Install the plugin

The plugin adds workflow skills that guide Claude when writing and navigating specifications.

```shell
/plugin marketplace add agagniere/speky
/plugin install speky@speky
```

### 2. Connect the MCP server

The MCP server exposes your project's specifications as queryable tools. Requires [uv](https://github.com/astral-sh/uv).

```shell
claude mcp add --scope project speky -- uvx --from git+https://github.com/agagniere/speky speky-mcp speky.yaml
```

Replace `speky.yaml` with the path to your manifest, or list individual YAML/TOML specification files.

> **Note:** If you don't have a specification yet, the `/write-specs` skill will guide you through creating one and configuring the MCP server automatically.

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
