Pdf         := speky_specifications.pdf
TypstSource := pdf.typ
YamlSources := $(shell find . -type f -name '*.yaml')
CsvSources  := $(shell find . -type f -name '*.csv')

pdf: $(Pdf)

$(Pdf): $(TypstSource) $(YamlSources) $(CsvSources)
	typst compile $< $@
