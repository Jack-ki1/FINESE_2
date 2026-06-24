.PHONY: install test lint format run docker-build docker-up docker-down clean help

# Default target
help:
	@echo "FINESE2 - Available commands:"
	@echo ""
	@echo "  make install     - Install dependencies and setup pre-commit hooks"
	@echo "  make test        - Run tests with coverage"
	@echo "  make lint        - Run linters (flake8, black, isort)"
	@echo "  make format      - Format code with black and isort"
	@echo "  make run         - Run application in debug mode"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up   - Start Docker containers"
	@echo "  make docker-down - Stop Docker containers"
	@echo "  make clean       - Clean up temporary files"
	@echo ""

# Install dependencies
install:
	pip install -r requirements.txt
	pre-commit install || echo "pre-commit not available, skipping"
	@echo "Dependencies installed successfully!"

# Run tests
test:
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# Run linters
lint:
	flake8 app/ tests/ --max-line-length=120 --ignore=E203,W503 || echo "Linting issues found"
	black --check app/ tests/ || echo "Black formatting issues found"
	isort --check-only app/ tests/ || echo "Import sorting issues found"

# Format code
format:
	black app/ tests/
	isort app/ tests/

# Run application
run:
	python main.py --host 0.0.0.0 --port 5000 --debug

# Docker commands
docker-build:
	docker build -t finese2:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Clean up
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	rm -rf temp/ 2>/dev/null || true
	@echo "Cleanup complete!"
