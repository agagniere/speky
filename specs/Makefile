Pdf         := speky_specifications.pdf
TypstSource := pdf.typ
YamlSources := $(shell find . -type f -name '*.yaml')

pdf: $(Pdf)

$(Pdf): $(TypstSource) $(YamlSources)
	typst compile $< $@
