BUILDOUT_BIN ?= $(shell command -v buildout || echo 'bin/buildout')
BUILDOUT_ARGS ?=
PYBOT_ARGS ?=

all: build check

show: $(BUILDOUT_BIN)
	$(BUILDOUT_BIN) $(BUILDOUT_ARGS) annotate

build: $(BUILDOUT_BIN)
	$(BUILDOUT_BIN) $(BUILDOUT_ARGS)

docs: bin/pocompile bin/sphinx-build
	bin/pocompile
	LANGUAGE=fi bin/sphinx-build docs html

test: bin/pocompile bin/code-analysis bin/test bin/pybot
	bin/pocompile
	bin/code-analysis
	bin/test --all
	LANGUAGE=fi bin/pybot $(PYBOT_ARGS) -d parts/test docs

check: test

dist:
	@echo "Not implemented"

deploy:
	@echo "Not implemented"

watch: bin/instance
	RELOAD_PATH=src bin/instance fg

robot-server: bin/robot-server
	LANGUAGE=fi RELOAD_PATH=src bin/robot-server collective.flow.testing.FLOW_ACCEPTANCE_TESTING -v

robot: bin/robot
	bin/robot -d parts/test docs

sphinx: bin/robot-sphinx-build
	bin/robot-sphinx-build -d html docs html

clean:
	rm -rf .installed bin develop-eggs parts

###

.PHONY: all show build docs test check dist deploy watch clean

bootstrap-buildout.py:
	curl -k -O https://bootstrap.pypa.io/bootstrap-buildout.py

bin/buildout: bootstrap-buildout.py buildout.cfg
	python bootstrap-buildout.py -c buildout.cfg

bin/test: $(BUILDOUT_BIN) buildout.cfg
	$(BUILDOUT_BIN) $(BUILDOUT_ARGS) install test

bin/pybot: $(BUILDOUT_BIN) buildout.cfg
	$(BUILDOUT_BIN) $(BUILDOUT_ARGS) install pybot

bin/sphinx-build: $(BUILDOUT_BIN) buildout.cfg
	$(BUILDOUT_BIN) $(BUILDOUT_ARGS) install sphinx-build

bin/robot: $(BUILDOUT_BIN) buildout.cfg
	$(BUILDOUT_BIN) $(BUILDOUT_ARGS) install robot

bin/robot-server: $(BUILDOUT_BIN) buildout.cfg
	$(BUILDOUT_BIN) $(BUILDOUT_ARGS) install robot

bin/robot-sphinx-build: $(BUILDOUT_BIN) buildout.cfg
	$(BUILDOUT_BIN) $(BUILDOUT_ARGS) install robot

bin/instance: $(BUILDOUT_BIN) buildout.cfg
	$(BUILDOUT_BIN) $(BUILDOUT_ARGS) install instance

bin/code-analysis: $(BUILDOUT_BIN) buildout.cfg
	$(BUILDOUT_BIN) $(BUILDOUT_ARGS) install code-analysis

bin/isort: $(BUILDOUT_BIN) buildout.cfg
	$(BUILDOUT_BIN) $(BUILDOUT_ARGS) install isort

bin/pocompile: $(BUILDOUT_BIN) buildout.cfg
	$(BUILDOUT_BIN) $(BUILDOUT_ARGS) install i18ndude

requirements.nix: nix-shell setup.nix -A pip2nix --run "pip2nix generate -r requirements.txt -r requirements-manual.txt --output=requirements.nix"
