# Starter-repo Makefile
#
# Self-contained: creates a local venv, installs the two deps (pyyaml +
# jsonschema), runs a one-file validator against the example manifest.

PYTHON ?= python3
VENV    = .venv
PIP     = $(VENV)/bin/pip
PY      = $(VENV)/bin/python3

.PHONY: help install validate clean

help:
	@echo "Targets:"
	@echo "  install   Create .venv and install pyyaml + jsonschema"
	@echo "  validate  Validate change-manifest.yaml against the upstream schema"
	@echo "  clean     Remove .venv"

$(VENV)/bin/python3:
	$(PYTHON) -m venv $(VENV)

install: $(VENV)/bin/python3
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --quiet pyyaml jsonschema

validate: install
	$(PY) scripts/validate-manifest.py

clean:
	rm -rf $(VENV)
