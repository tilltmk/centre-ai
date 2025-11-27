.PHONY: help build up down logs restart clean test

help:
	@echo "Centre AI - MCP Server Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make build       - Build Docker images"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make logs        - Show logs"
	@echo "  make restart     - Restart all services"
	@echo "  make clean       - Clean up everything"
	@echo "  make test        - Run tests"
	@echo "  make dev         - Run in development mode"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services are starting..."
	@echo "Dashboard: http://localhost:5000"
	@echo "API: http://localhost:5000/api/status"

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose restart

clean:
	docker-compose down -v
	rm -rf mcp_data/*.db logs/*.log

test:
	@echo "Running tests..."
	python -m pytest tests/ -v

dev:
	python app.py
