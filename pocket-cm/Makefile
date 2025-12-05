.PHONY: help install run test docker-build docker-up docker-down lint format clean

help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  run        - Run the application locally"
	@echo "  test       - Run tests"
	@echo "  lint       - Run code linting"
	@echo "  format     - Format code"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-up  - Start with docker-compose"
	@echo "  docker-down - Stop docker-compose"
	@echo "  clean      - Clean up temporary files"

install:
	pip install -r requirements.txt

run:
	python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

dev:
	DEBUG=true python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest tests/ -v --cov=src --cov-report=html

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

lint:
	ruff check src/ tests/
	flake8 src/ tests/

format:
	ruff format src/ tests/
	black src/ tests/

docker-build:
	docker build -t pocket-cm-ai-agent .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ dist/ build/

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-asyncio black ruff flake8

check: lint test