# Install editable package first, or run with PYTHONPATH=src.
PYTHON ?= python3
.PHONY: reproduce rebuild fetch preview test

reproduce:
	$(PYTHON) tools/reproduce_tables.py

rebuild:
	$(PYTHON) -m solverline.rebuild --offline

fetch:
	$(PYTHON) -m solverline.rebuild --fetch

preview:
	$(PYTHON) -m solverline.rebuild --offline --allow-partial

test:
	$(PYTHON) -m unittest discover -s tests -v
