# Install editable package first, or run with PYTHONPATH=src.
.PHONY: reproduce rebuild fetch preview test

reproduce:
	python tools/reproduce_tables.py

rebuild:
	python -m solverline.rebuild --offline

fetch:
	python -m solverline.rebuild --fetch

preview:
	python -m solverline.rebuild --offline --allow-partial

test:
	python -m unittest discover -s tests -v
