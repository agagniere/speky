Pdf         := speky_specification.pdf
TypstSource := pdf.typ
ManifestSource := speky.yaml
YamlSources := $(shell find . -type f -name '*.yaml')
CsvSources  := $(shell find . -type f -name '*.csv')
Run         := uv run
Yamale      := $(Run) --dev yamale
Speky       := $(Run) speky

pdf: $(Pdf)

check: ../schema.yaml $(YamlSources)
	$(Speky) --check-only $(ManifestSource)
	$(Yamale) -s $^

.PHONY: pdf check

$(Pdf): $(TypstSource) $(YamlSources) $(CsvSources)
	typst compile $< $@
