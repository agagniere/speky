# ===== Configurable via the environment =====
PROJECT_VERSION ?= $(shell $(Speky) --version | cut -d' ' -f2)
# ============================================

PythonSources  := $(shell find ../python -type f -name '*.py')
SpecSources    := $(shell find ../specs -name '*.yaml' -o -name '*.toml')
CSVComments    := $(shell find ../specs/comments -type f -name '*.csv')
ManifestSource := ../specs/speky.yaml ../specs/mcp/mcp.toml

MarkdownFolder := markdown
MarkdownIndex  := $(MarkdownFolder)/index.md

SphinxFolder   := sphinx
SphinxHtml     := $(SphinxFolder)/html/index.html

Run            := uv run
Speky          := $(Run) speky
Sphinx         := $(Run) --group docs sphinx-build


$(eval export PROJECT_VERSION)

html: $(SphinxHtml)

open: $(SphinxHtml)
	open $<

clean:
	$(RM) -r $(SphinxFolder) $(MarkdownFolder)

$(MarkdownIndex): $(SpecSources) $(PythonSources) $(CSVComments)
	$(Speky) $(ManifestSource) \
		--output-folder $(@D)

$(SphinxHtml): $(MarkdownIndex) conf.py Makefile
	$(Sphinx) -M html $(MarkdownFolder) $(SphinxFolder) \
		--conf-dir . --nitpicky --jobs auto
