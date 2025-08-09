.PHONY: help install test lint format clean docker-up docker-down run-pipeline

help:
	@echo "Available commands:"
	@echo "  install        Install dependencies"
	@echo "  install-dev    Install development dependencies"
	@echo "  test          Run tests"
	@echo "  lint          Run linters"
	@echo "  format        Format code"
	@echo "  clean         Clean build artifacts"
	@echo "  docker-up     Start Qdrant container"
	@echo "  docker-down   Stop Qdrant container"
	@echo "  run-pipeline  Run the main pipeline"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

lint:
	flake8 src/ tests/
	mypy src/ --ignore-missing-imports
	black --check src/ tests/
	isort --check-only src/ tests/

format:
	black src/ tests/
	isort src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ 2>/dev/null || true

docker-up:
	docker run -d --name qdrant -p 6333:6333 -v ./qdrant_storage:/qdrant/storage qdrant/qdrant

docker-down:
	docker stop qdrant && docker rm qdrant

run-pipeline:
	cd src && python pipeline.py

run-pipeline-test:
	cd src && python pipeline.py --states CA --tasks FundingSources

check-security:
	bandit -r src/ -ll
	safety check

pre-commit:
	pre-commit run --all-files