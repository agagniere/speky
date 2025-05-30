# ===== Configurable via the environment =====
PROJECT_VERSION ?= $(shell git tag --sort '-version:refname' --merged | head -1)
# ============================================

PythonSources  := $(shell find generators -type f -name '*.py')
YamlSources    := $(shell find ../specs -type f -name '*.yaml')

MarkdownFolder := markdown
MarkdownIndex  := $(MarkdownFolder)/index.md

SphinxFolder   := sphinx
SphinxHtml     := $(SphinxFolder)/html/index.html

Run            := uv run
Speky          := $(Run) speky
Sphinx         := $(Run) sphinx-build


$(eval export PROJECT_VERSION)

html: $(SphinxHtml)

clean:
	$(RM) -r $(SphinxFolder) $(MarkdownFolder)

$(MarkdownIndex): $(YamlSources) $(PythonSources)
	$(Speky) $(YamlSources) --output-folder $(@D)

$(SphinxHtml): $(MarkdownIndex) conf.py Makefile
	$(Sphinx) -M html $(MarkdownFolder) $(SphinxFolder) --conf-dir . --nitpicky
