.PHONY: help install test lint format clean run schedule deploy

help:
	@echo "Naukari Profile Auto-Updater"
	@echo ""
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make run          - Run automation once"
	@echo "  make schedule     - Run local scheduler"
	@echo "  make clean        - Clean generated files"
	@echo "  make deploy-gcp   - Deploy to GCP (with instructions)"

install:
	python -m venv venv
	$(VENV)/pip install --upgrade pip
	$(VENV)/pip install -r requirements.txt
	$(VENV)/playwright install chromium

test:
	pytest tests/ -v --cov=src --cov-report=html

lint:
	pylint src/ config/ tests/ || true
	black --check src/ config/ tests/ || true

format:
	black src/ config/ tests/
	isort src/ config/ tests/

run:
	DEBUG=true python src/naukari_automator.py

schedule:
	python src/scheduler.py

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

deploy-gcp:
	@echo "See deployment/gcp-compute-engine.md for detailed instructions"
	@cat deployment/gcp-compute-engine.md | head -50
