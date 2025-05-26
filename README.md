# Specifications with YAML and PDF

Write your requirements and functional tests in a textual format to easily version it with Git,
then generate a PDF and a static website.

## Roadmap
- [x] PDF with all relevant cross references
- [ ] Static website
- [ ] Differential PDF to see what changed since last version

## Usage

The speky typst package will generate content from language-agnostic data, like YAML.

### Install locally

```shell
make -C typst
```

### Use from typst

```typst
#import "@local/speky:0.0.3": speky

#speky((
  "requirements.yaml",
  "tests.yaml",
  "comments.yaml",
).map(yaml))
```
