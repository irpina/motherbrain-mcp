.PHONY: help up down logs shell agent test lint format clean

# Default target
help:
	@echo "Motherbrain MCP - Available commands:"
	@echo "  make up       - Start all services with docker compose"
	@echo "  make down     - Stop all services"
	@echo "  make logs     - Follow logs from all services"
	@echo "  make shell    - Open a shell in the API container"
	@echo "  make agent    - Run the example agent (requires API to be running)"
	@echo "  make test     - Run tests (if any)"
	@echo "  make clean    - Stop services and remove volumes"

# Start all services
up:
	docker compose up --build -d

# Stop all services
down:
	docker compose down

# Follow logs
logs:
	docker compose logs -f

# Open shell in API container
shell:
	docker compose exec api /bin/sh

# Run the example agent (outside docker)
agent:
	cd agent && python agent.py

# Run tests
test:
	cd agent && API_URL=http://localhost:8000 python -m pytest ../tests/ -v

# Clean everything (volumes included)
clean:
	docker compose down -v

# Format code with black/black-like formatter
format:
	@echo "Run your formatter here (e.g., black app/ agent/)"

# Lint code
lint:
	@echo "Run your linter here (e.g., flake8 app/ agent/)"
