# Speky: Specifications in YAML

![logo](sphinx/assets/Speky-256.png)

Write your requirements and functional tests in a textual format to easily version it with Git,
then generate a PDF and a static website.

Track the specification in the same repository as the code by checking in a `speky.toml`
manifest and the related YAML sources.

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
#import "@local/speky:1.3.0": speky

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
1. Generate Myst Markdown:
   ```shell
   speky requirements.yaml tests.yaml comments.yaml \
	   --output-folder markdown \
	   --project-name Toto
   ```
1. Configure Sphinx:
   ```shell
   cat <<-EOF > conf.py
   project    = 'Toto'
   language   = 'en'
   extensions = [ 'myst_parser', 'sphinx_design' ]
   html_theme = 'furo'
   myst_enable_extensions = [ 'colon_fence' ]
   EOF
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

## Load a repo-tracked project

Instead of listing YAML files manually, you can check a `speky.toml` manifest into the repository
and load the project by name.

Example manifest:

```toml
[project]
name = "demo"
display_name = "Demo"

[[source]]
kind = "workspace"
root = "."
requirements = ["specs/requirements.yaml"]
tests = ["specs/tests.yaml"]
comments = ["specs/comments.yaml"]
code_roots = ["tests"]
```

Validate the project:

```shell
speky --project demo --check-only
```

The CLI also supports `--manifest path/to/speky.toml`.

## Link code references

Tagged source annotations can now point to Speky identifiers directly. For example:

```python
# speky:demo#T10
def test_feature():
    assert True
```

When a project is loaded from a manifest, Speky will discover these annotations and expose
generic code mentions in generated output and through the MCP server. If the target is a Speky
test and the code symbol is an executable test, Speky also exposes that reference as executable
test evidence for the Speky test.

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
- [DEVELOPMENT.md](DEVELOPMENT.md), [MCP.md](MCP.md)
