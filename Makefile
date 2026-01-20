.PHONY: docker-build docker-run docker-stop docker-logs docker-shell docker-compose-up docker-compose-down docker-compose-logs help

help:
	@echo "Risk Analyzer Docker Commands"
	@echo "============================="
	@echo ""
	@echo "Docker:"
	@echo "  docker-build           Build Docker image"
	@echo "  docker-run             Run container standalone"
	@echo "  docker-stop            Stop running container"
	@echo "  docker-logs            Show container logs"
	@echo "  docker-shell           Open shell in running container"
	@echo "  docker-clean           Remove image and stopped containers"
	@echo ""
	@echo "Docker Compose:"
	@echo "  docker-compose-up      Start services with docker-compose"
	@echo "  docker-compose-down    Stop and remove docker-compose services"
	@echo "  docker-compose-logs    Show docker-compose logs"
	@echo "  docker-compose-rebuild Rebuild and restart services"
	@echo ""
	@echo "With Joget:"
	@echo "  docker-joget-up        Start with Joget service"
	@echo "  docker-joget-down      Stop Joget and analyzer"
	@echo "  docker-joget-logs      Show logs for Joget setup"
	@echo ""

# Docker standalone commands
docker-build:
	@echo "Building Docker image..."
	docker build -t risk-analyzer:latest .

docker-run: docker-build
	@echo "Starting Risk Analyzer container..."
	@if [ ! -f .env ]; then \
		echo "ERROR: .env file not found. Run 'cp .env.example .env' and configure it."; \
		exit 1; \
	fi
	docker run -d \
		--name risk-analyzer \
		-p 8000:8000 \
		--env-file .env \
		risk-analyzer:latest
	@echo "Container started. Access at http://localhost:8000"
	@echo "View logs: docker logs -f risk-analyzer"

docker-stop:
	@echo "Stopping Risk Analyzer container..."
	docker stop risk-analyzer 2>/dev/null || true
	docker rm risk-analyzer 2>/dev/null || true
	@echo "Container stopped"

docker-logs:
	docker logs -f risk-analyzer

docker-shell:
	docker exec -it risk-analyzer /bin/bash

docker-clean: docker-stop
	@echo "Removing image..."
	docker rmi risk-analyzer:latest 2>/dev/null || true
	@echo "Cleanup complete"

# Docker Compose commands
docker-compose-up:
	@if [ ! -f .env ]; then \
		echo "ERROR: .env file not found. Run 'cp .env.example .env' and configure it."; \
		exit 1; \
	fi
	docker-compose up -d
	@echo "Services started. Access analyzer at http://localhost:8000"

docker-compose-down:
	docker-compose down

docker-compose-logs:
	docker-compose logs -f

docker-compose-rebuild:
	docker-compose build --no-cache
	docker-compose up -d
	@echo "Services rebuilt and started"

# Docker Compose with Joget
docker-joget-up:
	@if [ ! -f .env ]; then \
		echo "ERROR: .env file not found. Run 'cp .env.example .env' and configure it."; \
		exit 1; \
	fi
	docker-compose --profile with-joget up -d
	@echo "Risk Analyzer and Joget started"
	@echo "  Risk Analyzer: http://localhost:8000"
	@echo "  Joget: http://localhost:8080"

docker-joget-down:
	docker-compose --profile with-joget down

docker-joget-logs:
	docker-compose --profile with-joget logs -f

# Dev workflows
docker-dev-build: docker-build
	@echo "Built development image"

docker-dev-logs: docker-logs
	@echo "Showing dev logs..."
