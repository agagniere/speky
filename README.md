# Speky: Specifications in YAML

Write your requirements and functional tests in a textual format to easily version it with Git,
then generate a PDF and a static website.

## Roadmap
- [x] PDF with all relevant cross references
- [x] Static website
- [ ] Differential PDF to see what changed since last version

## Generate a PDF

The speky typst package will generate content from language-agnostic data, like YAML.

### Install locally

```shell
make -C typst
```

### Use from typst

```typst
#import "@local/speky:0.0.6": speky

#speky((
  "requirements.yaml",
  "tests.yaml",
  "comments.yaml",
).map(yaml))
```

## Generate a static website

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
1. Generate HTML with sphinx:
   ```shell
   uv tool install sphinx --with furo,sphinx-design,sphinx-copybutton,myst-parser
   sphinx-build -M html markdown sphinx --conf-dir .
   ```
1. Open the website in a browser
   ```shell
   open sphinx/html/index.html
   ```
