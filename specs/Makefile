Pdf         := speky_specification.pdf
TypstSource := pdf.typ
YamlSources := $(shell find . -type f -name '*.yaml')
CsvSources  := $(shell find . -type f -name '*.csv')
Yamale      := uv run --group dev yamale

pdf: $(Pdf)

check: ../schema.yaml $(YamlSources)
	$(Yamale) -s $^

.PHONY: pdf check

$(Pdf): $(TypstSource) $(YamlSources) $(CsvSources)
	typst compile $< $@
