# ===== Configurable via the environment =====
PROJECT_VERSION ?= $(shell git tag --sort '-version:refname' --merged | head -1)
# ============================================

PythonSources  := $(shell find ../python -type f -name '*.py')
YamlSources    := $(shell find ../specs -type f -name '*.yaml')
CSVComments    := $(shell find ../specs/comments -type f -name '*.csv')

MarkdownFolder := markdown
MarkdownIndex  := $(MarkdownFolder)/index.md

SphinxFolder   := sphinx
SphinxHtml     := $(SphinxFolder)/html/index.html

Run            := uv run
Speky          := $(Run) speky
Sphinx         := $(Run) --group docs sphinx-build


$(eval export PROJECT_VERSION)

html: $(SphinxHtml)

clean:
	$(RM) -r $(SphinxFolder) $(MarkdownFolder)

$(MarkdownIndex): $(YamlSources) $(PythonSources) $(CSVComments)
	$(Speky) $(YamlSources) \
		$(addprefix -C ,$(CSVComments)) \
		--output-folder $(@D) \
		--project-name Speky

$(SphinxHtml): $(MarkdownIndex) conf.py Makefile
	$(Sphinx) -M html $(MarkdownFolder) $(SphinxFolder) \
		--conf-dir . --nitpicky --jobs auto
