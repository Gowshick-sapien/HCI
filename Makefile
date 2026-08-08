.PHONY: help install test lint format clean benchmark run

help:
	@echo "Available commands:"
	@echo "  install    : Install dependencies in editable mode"
	@echo "  test       : Run unit and integration tests with pytest"
	@echo "  lint       : Check code style with flake8 and types with mypy"
	@echo "  format     : Auto-format code with black and isort"
	@echo "  benchmark  : Run performance and frame latency benchmarks"
	@echo "  clean      : Remove build artifacts, cache, and temp files"
	@echo "  run        : Launch the main adaptive HCI system"

install:
	pip install -e ".[dev,evaluation]"

test:
	pytest tests/

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/ configs/
	isort src/ tests/

benchmark:
	pytest tests/benchmarks/ --benchmark-only

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov .mypy_cache

run:
	python src/main.py
