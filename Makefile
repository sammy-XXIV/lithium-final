# Install editable package first, or run with PYTHONPATH=src.
.PHONY: rebuild fetch preview test

rebuild:
	python -m solverline.rebuild --offline

fetch:
	python -m solverline.rebuild --fetch

preview:
	python -m solverline.rebuild --offline --allow-partial

test:
	python -m unittest discover -s tests -v
