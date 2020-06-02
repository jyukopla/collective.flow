# Requires .netrc file with
#
# machine repo.kopla.jyu.fi
# login username
# password secret

INDEX_URL ?= https://repo.kopla.jyu.fi/api/pypi/pypi/simple
INDEX_HOSTNAME ?= repo.kopla.jyu.fi
PYPI_USERNAME ?= guest
PYPI_PASSWORD ?= guest

PLONE ?= plone50
PYTHON ?= python27

BUILDOUT_CFG ?= test_$(PLONE).cfg
BUILDOUT_ARGS ?= -N

NIX_OPTIONS ?= --argstr plone $(PLONE) --argstr python $(PYTHON)
REF_NIXPKGS = branches nixos-20.03

.PHONY: check
check: .installed.cfg
ifeq ($(PYTHON), python37)
	bin/black -t py27 --check src
	# pylama src
endif

env:
	nix-build $(NIX_OPTIONS) setup.nix -A env -o env

.PHONY: format
format: .installed.cfg
ifeq ($(PYTHON), python37)
	bin/black -t py27 src
endif
	bin/isort -rc -y src

.PHONY: show
show:
	buildout -c $(BUILDOUT_CFG) $(BUILDOUT_ARGS) annotate

.PHONY: start
start: .installed.cfg
	PYTHON= bin/instance fg

.PHONY: test
test: check
	bin/pocompile src
	bin/test  --all

###

nix-%: netrc
	NIX_CONF_DIR=$(PWD) \
	nix-shell $(NIX_OPTIONS) setup.nix -A shell --run "$(MAKE) $*"

nix-shell: netrc
	NIX_CONF_DIR=$(PWD) \
	nix-shell $(NIX_OPTIONS) setup.nix -A shell

.installed.cfg: $(BUILDOUT_CFG)
	buildout -c $(BUILDOUT_CFG) $(BUILDOUT_ARGS)

.cache:
	@if [ -d ~/.cache ]; then ln -s ~/.cache .; else \
	  mkdir -p .cache; \
	fi

.netrc:
	@if [ -f ~/.netrc ]; then ln -s ~/.netrc .; else \
	  echo machine ${INDEX_HOSTNAME} > .netrc && \
	  echo login ${PYPI_USERNAME} >> .netrc && \
	  echo password ${PYPI_PASSWORD} >> .netrc; \
	fi

netrc: .netrc .cache
	@ln -sf .netrc netrc

.PHONY: requirements
requirements: requirements-$(PLONE)-$(PYTHON).nix

requirements-$(PLONE)-$(PYTHON).nix: requirements-$(PLONE)-$(PYTHON).txt
	HOME=$(PWD) NIX_CONF_DIR=$(PWD) \
	nix-shell setup.nix $(NIX_OPTIONS) -A pip2nix --run "HOME=$(PWD) NIX_CONF_DIR=$(PWD) pip2nix generate -r requirements-$(PLONE)-$(PYTHON).txt --index-url $(INDEX_URL) --output=requirements-$(PLONE)-$(PYTHON).nix"

requirements-$(PLONE)-$(PYTHON).txt: $(BUILDOUT_CFG) setup.cfg
	$(RM) .installed.cfg
	nix-shell $(NIX_OPTIONS) --run "buildout -c $(BUILDOUT_CFG) $(BUILDOUT_ARGS)"
	HOME=$(PWD) NIX_CONF_DIR=$(PWD) \
	nix-shell setup.nix $(NIX_OPTIONS) -A pip2nix --run "HOME=$(PWD) NIX_CONF_DIR=$(PWD) pip2nix generate -r requirements.txt --index-url $(INDEX_URL) --output=requirements-$(PLONE)-$(PYTHON).nix"
	@grep "pname =\|version =" requirements-$(PLONE)-$(PYTHON).nix|awk "ORS=NR%2?FS:RS"|sed 's|.*"\(.*\)";.*version = "\(.*\)".*|\1==\2|' > requirements-$(PLONE)-$(PYTHON).txt

.PHONY: upgrade
upgrade:
	nix-shell --pure -p cacert curl gnumake jq nix --run "make setup.nix"

.PHONY: setup.nix
setup.nix:
	@set -e pipefail; \
	echo "Updating nixpkgs @ setup.nix using $(REF_NIXPKGS)"; \
	rev=$$(curl https://api.github.com/repos/NixOS/nixpkgs-channels/$(firstword $(REF_NIXPKGS)) \
		| jq -er '.[]|select(.name == "$(lastword $(REF_NIXPKGS))").commit.sha'); \
	echo "Latest commit sha: $$rev"; \
	sha=$$(nix-prefetch-url --unpack https://github.com/NixOS/nixpkgs-channels/archive/$$rev.tar.gz); \
	sed -i \
		-e "2s|.*|    # $(REF_NIXPKGS)|" \
		-e "3s|.*|    url = \"https://github.com/NixOS/nixpkgs-channels/archive/$$rev.tar.gz\";|" \
		-e "4s|.*|    sha256 = \"$$sha\";|" \
		setup.nix
