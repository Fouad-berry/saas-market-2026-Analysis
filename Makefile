PYTHON ?= python3

.PHONY: install test lint format typecheck run clean

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m pytest tests/ -v --tb=short

lint:
	$(PYTHON) -m ruff check src/ tests/

format:
	$(PYTHON) -m ruff format src/ tests/

typecheck:
	$(PYTHON) -m mypy src/

run:
	$(PYTHON) -m src.pipeline

clean:
	rm -rf .mypy_cache/ .pytest_cache/ .ruff_cache/
	rm -rf src/*.egg-info/
	rm -f data/processed/*.parquet data/processed/*.tmp.parquet
	rm -f data/marts/*.parquet data/marts/*.tmp.parquet
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
