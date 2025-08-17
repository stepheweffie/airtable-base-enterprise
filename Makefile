.PHONY: help install install-dev test test-unit test-integration test-performance test-coverage lint format type-check security clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt

test: ## Run all tests
	pytest -v

test-unit: ## Run unit tests only
	pytest test_unit.py test_basic.py -v

test-integration: ## Run integration tests only
	pytest test_integration.py -v

test-performance: ## Run performance tests only
	pytest test_performance.py -v -s

test-coverage: ## Run tests with coverage reporting
	pytest --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=80

lint: ## Run flake8 linting
	flake8 *.py --max-line-length=120 --exclude=venv,htmlcov

format: ## Format code with black and isort
	black *.py --line-length=120
	isort *.py

type-check: ## Run type checking with mypy
	mypy *.py --ignore-missing-imports

security: ## Run security checks
	bandit -r *.py
	safety check

clean: ## Clean up generated files
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf *.pyc
	rm -rf .tox/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

setup-pre-commit: ## Setup pre-commit hooks
	pre-commit install

run-pre-commit: ## Run pre-commit on all files
	pre-commit run --all-files

tox: ## Run tests in multiple Python environments
	tox

quick-test: ## Run a quick subset of tests for development
	pytest test_basic.py test_unit.py::TestConfig -v

demo: ## Run the system status to demo functionality
	@echo "Running system status check..."
	python main.py status

validate: ## Validate configuration
	python -c "import config; config.validate_config(); print('✅ Configuration is valid!')"
