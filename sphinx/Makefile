# ===== Configurable via the environment =====
PROJECT_VERSION ?= $(shell git tag --sort '-version:refname' --merged | head -1)
# ============================================

Sphinx     := uv run sphinx-build
SphinxHtml := html/index.html

$(eval export PROJECT_VERSION)

$(SphinxHtml):
	$(Sphinx) -M html pages . --conf-dir . --nitpicky
