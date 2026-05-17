.PHONY: lint format test typecheck all

all: lint typecheck test

lint:
	ruff check .

format:
	ruff format .

test:
	python -m pytest tests/

typecheck:
	mypy . --ignore-missing-imports
