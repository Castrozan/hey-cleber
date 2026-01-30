.PHONY: test lint format typecheck check

test:
	python -m pytest tests/ -v

lint:
	ruff check hey_clever/ tests/

format:
	ruff format hey_clever/ tests/

typecheck:
	mypy hey_clever/ --ignore-missing-imports --disable-error-code=import-untyped

check: lint typecheck test
	@echo "All checks passed"
