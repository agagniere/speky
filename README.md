# Speky: Specifications in YAML

![logo](sphinx/assets/Speky-256.png)

Write your requirements and functional tests in a textual format to easily version it with Git,
then generate a PDF and a static website.

## Roadmap
- [x] PDF with all relevant cross references
- [x] Static website
- [ ] Differential PDF to see what changed since last version

## Generate a PDF

Requires [Typst](https://github.com/typst/typst) >= 0.13.0

The speky typst package will generate content from language-agnostic data, like YAML.

### Install locally

```shell
make -C typst
```

### Use from typst

```typst
#import "@local/speky:1.2.0": speky

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

## Used by

![safran](https://upload.wikimedia.org/wikipedia/fr/thumb/5/5f/Safran_-_logo_2016.png/330px-Safran_-_logo_2016.png)
