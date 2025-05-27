# ===== Configurable via the environment =====
PACKAGE_NAMESPACE ?= local
PACKAGE_NAME      ?= speky
PACKAGE_VERSION   ?= $(shell git tag --sort '-version:refname' --merged | head -1)
# ============================================

ifeq "$(shell uname)" "Darwin"
	DataFolder := $(shell osascript -e 'POSIX path of (path to application support folder from user domain)' | sed 's| |\\ |')
else
	DataFolder  := $XDG_DATA_HOME
	SHELL       := bash
	.SHELLFLAGS := -o errexit -o nounset -o pipefail -c
endif

InstallFolder := $(DataFolder)typst/packages/$(PACKAGE_NAMESPACE)/$(PACKAGE_NAME)/$(PACKAGE_VERSION)

$(eval export PACKAGE_VERSION)

# Phony rules

install: typst.toml speky.typ | $(InstallFolder)
	cp $^ "$|"

clean:
	$(RM) typst.toml

format: | speky.typ
	typstyle -i $|

.PHONY: install clean format

# Concrete rules

typst.toml: typst.toml.in
	envsubst '$$PACKAGE_VERSION' < $< > $@

$(InstallFolder):
	mkdir -p "$@"
