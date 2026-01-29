.PHONY: test lint format typecheck check

test:
	python -m pytest tests/ -v

lint:
	ruff check hey_cleber/ tests/

format:
	ruff format hey_cleber/ tests/

typecheck:
	mypy hey_cleber/ --ignore-missing-imports --disable-error-code=import-untyped

check: lint typecheck test
	@echo "✅ All checks passed"
