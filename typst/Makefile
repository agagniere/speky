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

Files          := typst.toml speky.typ
InstallFolder  := $(DataFolder)typst/packages/$(PACKAGE_NAMESPACE)/$(PACKAGE_NAME)/$(PACKAGE_VERSION)
InstalledFiles := $(addprefix $(InstallFolder)/,$(Files))

$(eval export PACKAGE_VERSION)

# Phony rules

install: $(InstalledFiles)

clean:
	$(RM) typst.toml

format: | speky.typ
	typstyle -i $|

purge:
	$(RM) -rv $(InstallFolder)

.PHONY: install clean format purge

# Concrete rules

$(InstalledFiles) &: $(Files) | $(InstallFolder)
	cp $^ "$|"

typst.toml: typst.toml.in
	envsubst '$$PACKAGE_VERSION' < $< > $@

$(InstallFolder):
	mkdir -p "$@"
