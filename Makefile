BUILDOUT_BIN ?= $(shell command -v buildout || echo 'bin/buildout')
BUILDOUT_ARGS ?=
PYBOT_ARGS ?=

.PHONY: all
all: build check

.PHONY: format
format: bin/isort bin/yapf
	bin/yapf -r -i src
	bin/isort -rc -y src

.PHONY: show
show: $(BUILDOUT_BIN)
	$(BUILDOUT_BIN) $(BUILDOUT_ARGS) annotate

.PHONY: build
build: $(BUILDOUT_BIN)
	$(BUILDOUT_BIN) $(BUILDOUT_ARGS)

.PHONY: docs
docs: bin/pocompile bin/sphinx-build
	bin/pocompile
	LANGUAGE=fi bin/sphinx-build docs html

.PHONY: test
test: bin/pocompile bin/code-analysis bin/test bin/pybot
	bin/pocompile
	bin/code-analysis
	bin/test --all
	LANGUAGE=fi bin/pybot $(PYBOT_ARGS) -d parts/test docs

.PHONY: check
check: test

.PHONY: dist
dist:
	@echo "Not implemented"

.PHONY: deploy
deploy:
	@echo "Not implemented"

.PHONY: watch
watch: bin/instance
	RELOAD_PATH=src bin/instance fg

.PHONY: robot-server
robot-server: bin/robot-server
	LANGUAGE=fi RELOAD_PATH=src bin/robot-server collective.flow.testing.FLOW_ACCEPTANCE_TESTING -v

.PHONY: robot
robot: bin/robot
	bin/robot -d parts/test docs

.PHONY: sphinx
sphinx: bin/robot-sphinx-build
	bin/robot-sphinx-build -d html docs html

.PHONY: clean
clean:
	rm -rf .installed bin develop-eggs parts

###

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

bin/yapf: $(BUILDOUT_BIN) buildout.cfg
	$(BUILDOUT_BIN) $(BUILDOUT_ARGS) install yapf

bin/pocompile: $(BUILDOUT_BIN) buildout.cfg
	$(BUILDOUT_BIN) $(BUILDOUT_ARGS) install i18ndude

requirements.nix: nix-shell setup.nix -A pip2nix --run "pip2nix generate -r requirements.txt -r requirements-manual.txt --output=requirements.nix"
